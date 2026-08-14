# -*- coding: utf-8 -*-
"""
@Time    : 2025/7/16 22:13
@Author  : QIN2DIM
@GitHub  : https://github.com/QIN2DIM
@Desc    :
"""
import asyncio
import json
import os
import time
from contextlib import suppress

os.environ.setdefault("MPLBACKEND", "Agg")

from hcaptcha_challenger.agent import AgentV
from hcaptcha_challenger.models import ChallengeSignal
from loguru import logger
from playwright.async_api import Error as PlaywrightError
from playwright.async_api import expect, Page, Response
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from extensions.hcaptcha_runtime import wait_for_challenge_signal
from services.epic_totp_service import redact_totp_inputs, submit_totp_challenge, totp_login_enabled
from settings import SCREENSHOTS_DIR, settings

URL_CLAIM = "https://store.epicgames.com/en-US/free-games"
URL_ORDER_HISTORY = "https://www.epicgames.com/account/v2/payment/ajaxGetOrderHistory"


class EpicAuthenticationFatalError(RuntimeError):
    pass


class EpicManualActionRequiredError(RuntimeError):
    pass


class EpicAuthorization:

    def __init__(self, page: Page):
        self.page = page

        self._is_login_success_signal = asyncio.Queue()
        self._login_error_signal = asyncio.Queue()
        self._is_refresh_csrf_signal = asyncio.Queue()
        self._totp_attempts = 0
        self._invalid_totp_rejections = 0
        self._last_captcha_totp_refresh_at = 0.0

    async def _on_response_anything(self, r: Response):
        if r.request.method != "POST" or "talon" in r.url:
            return

        with suppress(Exception):
            result = await r.json()
            result_json = json.dumps(result, indent=2, ensure_ascii=False)

            if "/id/api/login" in r.url and result.get("errorCode"):
                self._login_error_signal.put_nowait(result)
                logger.error(f"{r.request.method} {r.url} - {result_json}")
            elif "/id/api/analytics" in r.url and result.get("accountId"):
                self._is_login_success_signal.put_nowait(result)
            elif "/account/v2/refresh-csrf" in r.url and result.get("success", False) is True:
                self._is_refresh_csrf_signal.put_nowait(result)
            # else:
            #     logger.debug(f"{r.request.method} {r.url} - {result_json}")

    @staticmethod
    def _drain_queue(queue: asyncio.Queue):
        while not queue.empty():
            with suppress(Exception):
                queue.get_nowait()

    def _drain_retryable_mfa_errors(self) -> None:
        retained = []
        while not self._login_error_signal.empty():
            with suppress(Exception):
                result = self._login_error_signal.get_nowait()
                error_code = result.get("errorCode", "unknown_error")
                if self._is_two_factor_required_error(
                    error_code
                ) or self._is_mfa_code_invalid_error(error_code):
                    continue
                retained.append(result)

        for result in retained:
            self._login_error_signal.put_nowait(result)

    @staticmethod
    def _is_two_factor_required_error(error_code: str) -> bool:
        return error_code == "errors.com.epicgames.common.two_factor_authentication.required"

    @staticmethod
    def _is_mfa_code_invalid_error(error_code: str) -> bool:
        return error_code == "errors.com.epicgames.accountportal.mfa_code_invalid"

    def _is_mfa_page(self) -> bool:
        return "/id/login/mfa" in self.page.url.lower()

    async def _handle_right_account_validation(self):
        """
        以下验证仅会在登录成功后出现
        Returns:

        """
        await self.page.goto("https://www.epicgames.com/account/personal", wait_until="networkidle")

        btn_ids = ["#link-success", "#login-reminder-prompt-setup-tfa-skip", "#yes"]

        # == 账号长期不登录需要做的额外验证 == #

        while self._is_refresh_csrf_signal.empty() and btn_ids:
            if self._needs_mfa_setup_prompt():
                if not await self._dismiss_mfa_setup_prompt(timeout_ms=30000):
                    raise EpicManualActionRequiredError(
                        self._mfa_setup_prompt_message(self.page.url)
                    )

            await self.page.wait_for_timeout(500)
            action_chains = btn_ids.copy()
            for action in action_chains:
                with suppress(Exception):
                    reminder_btn = self.page.locator(action)
                    await expect(reminder_btn).to_be_visible(timeout=1000)
                    await reminder_btn.click(timeout=1000)
                    btn_ids.remove(action)

    def _needs_privacy_policy_correction(self) -> bool:
        return "/id/login/correction/privacy-policy" in self.page.url

    def _needs_mfa_setup_prompt(self) -> bool:
        return "/id/login/mfa/add" in self.page.url

    @staticmethod
    def _privacy_policy_confirmation_message(current_url: str) -> str:
        return (
            "Epic account requires a manual privacy-policy confirmation. "
            "Please sign in once in a normal browser, complete the confirmation page, "
            f"and rerun the workflow. current_url={current_url}"
        )

    @staticmethod
    def _mfa_setup_prompt_message(current_url: str) -> str:
        return (
            "Epic account is showing the MFA setup prompt after login. "
            "Please sign in once in a normal browser, skip or finish that prompt, "
            f"and rerun the workflow. current_url={current_url}"
        )

    async def _page_body_text(self) -> str:
        with suppress(Exception):
            return await self.page.locator("body").inner_text(timeout=1000)
        return ""

    async def _dismiss_mfa_setup_prompt(self, timeout_ms: int = 10000) -> bool:
        if not self._needs_mfa_setup_prompt():
            return True

        logger.warning(
            "Epic MFA setup prompt detected after login; attempting to skip | current_url='{}'",
            self.page.url,
        )

        selectors = (
            "#login-reminder-prompt-setup-tfa-skip",
            "#link-success",
            "//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'skip')]",
            "//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'not now')]",
            "//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'maybe later')]",
            "//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'remind me later')]",
            "//a[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'skip')]",
            "//a[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'not now')]",
        )
        deadline = time.monotonic() + timeout_ms / 1000

        while time.monotonic() < deadline:
            if not self._needs_mfa_setup_prompt():
                return True

            for selector in selectors:
                with suppress(Exception):
                    locator = self.page.locator(selector).first
                    if not await locator.is_visible(timeout=300):
                        continue
                    await locator.click(timeout=2000, force=True)
                    await self.page.wait_for_timeout(1500)
                    if not self._needs_mfa_setup_prompt():
                        logger.success("Skipped Epic MFA setup prompt")
                        return True

            with suppress(Exception):
                clicked = await self.page.evaluate(
                    """
                    () => {
                      const normalize = (value) =>
                        (value || '').replace(/\\s+/g, ' ').trim().toLowerCase();
                      const isVisible = (element) => {
                        const rect = element.getBoundingClientRect();
                        const style = window.getComputedStyle(element);
                        return rect.width > 0 && rect.height > 0 &&
                          style.visibility !== 'hidden' &&
                          style.display !== 'none' &&
                          style.opacity !== '0';
                      };
                      const allowed = ['skip', 'not now', 'maybe later', 'remind me later'];
                      const candidates = Array.from(document.querySelectorAll('button,a'))
                        .filter(isVisible)
                        .filter((element) => {
                          const text = normalize(element.innerText || element.textContent);
                          return allowed.some((marker) => text.includes(marker));
                        });
                      const target = candidates.at(-1);
                      if (!target) {
                        const accountPrompt = Array.from(document.querySelectorAll('div,section,main'))
                          .filter(isVisible)
                          .find((element) =>
                            normalize(element.innerText || element.textContent)
                              .includes('protect your account')
                          );
                        if (!accountPrompt) {
                          return false;
                        }
                        const buttons = Array.from(accountPrompt.querySelectorAll('button'))
                          .filter(isVisible);
                        if (buttons.length < 2) {
                          return false;
                        }
                        const fallback = buttons.at(-1);
                        const fallbackText = normalize(fallback.innerText || fallback.textContent);
                        if (fallbackText.includes('set up') || fallbackText.includes('2fa')) {
                          return false;
                        }
                        fallback.click();
                        return true;
                      }
                      target.click();
                      return true;
                    }
                    """
                )
                if clicked:
                    await self.page.wait_for_timeout(1500)
                    if not self._needs_mfa_setup_prompt():
                        logger.success("Skipped Epic MFA setup prompt")
                        return True

            await self.page.wait_for_timeout(500)

        logger.error(
            "Epic MFA setup prompt could not be skipped automatically | current_url='{}'",
            self.page.url,
        )
        return False

    async def _has_pre_login_security_check(self) -> bool:
        with suppress(Exception):
            title = (await self.page.title()).lower()
            if "just a moment" in title:
                return True

        body = (await self._page_body_text()).lower()
        return any(
            marker in body
            for marker in (
                "one more step",
                "please complete a security check to continue",
                "verify you are human",
            )
        )

    async def _has_visible_hcaptcha(self) -> bool:
        for frame in self.page.frames:
            if "hcaptcha" in (frame.url or "").lower():
                with suppress(Exception):
                    frame_element = await frame.frame_element()
                    visible = await frame_element.evaluate(
                        """
                        (element) => {
                          const rect = element.getBoundingClientRect();
                          const style = window.getComputedStyle(element);
                          return rect.width > 0 && rect.height > 0 &&
                            style.visibility !== 'hidden' &&
                            style.display !== 'none' &&
                            style.opacity !== '0';
                        }
                        """
                    )
                    if visible:
                        return True

        body = (await self._page_body_text()).lower()
        return any(
            marker in body
            for marker in (
                "one more step",
                "please complete a security check",
                "verify you are human",
                "i am human",
            )
        )

    async def _wait_for_login_form(self, point_url: str) -> None:
        deadline = time.monotonic() + 45
        recovery_attempts = 0
        email_input = self.page.locator("#email")

        while time.monotonic() < deadline:
            with suppress(Exception):
                await expect(email_input).to_be_visible(timeout=1000)
                return

            if await self._has_pre_login_security_check():
                if recovery_attempts < 2:
                    recovery_attempts += 1
                    logger.warning(
                        "Pre-login security page detected, clearing cookies and retrying login entry ({}/2) | url='{}'",
                        recovery_attempts,
                        self.page.url,
                    )
                    await self.page.context.clear_cookies()
                    await self.page.goto(point_url, wait_until="domcontentloaded")
                    continue

                logger.warning(
                    "Pre-login security page still active after recovery attempts | url='{}'",
                    self.page.url,
                )
                await self.page.wait_for_timeout(2000)
                continue

            await self.page.wait_for_timeout(500)

        raise PlaywrightTimeoutError("Timed out waiting for Epic login form")

    async def _goto_claim_page(self, attempts: int = 3) -> None:
        for attempt in range(1, attempts + 1):
            try:
                await self.page.goto(URL_CLAIM, wait_until="domcontentloaded", timeout=45000)
                return
            except (PlaywrightTimeoutError, PlaywrightError) as err:
                logger.warning(
                    "Claim page navigation timed out during authentication ({}/{}) | current_url='{}' err={}",
                    attempt,
                    attempts,
                    self.page.url,
                    err,
                )
                with suppress(Exception):
                    await self.page.evaluate("window.stop()")

                if "store.epicgames.com" in self.page.url and "free-games" in self.page.url:
                    logger.warning(
                        "Continuing with partially loaded claim page during authentication | current_url='{}'",
                        self.page.url,
                    )
                    return

                if attempt < attempts:
                    await self.page.wait_for_timeout(2000 * attempt)

        raise PlaywrightTimeoutError("Timed out navigating to Epic claim page")

    async def _await_login_outcome(
        self, point_url: str, agent: AgentV, timeout_seconds: int = 300
    ) -> None:
        started_at = time.monotonic()
        deadline = started_at + timeout_seconds
        hard_timeout_seconds = max(timeout_seconds, 180)
        max_deadline = started_at + hard_timeout_seconds
        max_totp_attempts = 6
        max_invalid_totp_rejections = 3
        captcha_totp_refresh_cooldown = 8.0

        def extend_deadline(reason: str, seconds: int = 120) -> None:
            nonlocal deadline

            new_deadline = min(time.monotonic() + seconds, max_deadline)
            if new_deadline > deadline:
                deadline = new_deadline
                logger.debug(
                    "Extended Epic login outcome wait after {} | seconds_remaining={:.1f}",
                    reason,
                    max(deadline - time.monotonic(), 0),
                )

        async def submit_fresh_totp(reason: str) -> None:
            if not totp_login_enabled():
                raise EpicAuthenticationFatalError(reason)

            if self._is_mfa_code_invalid_error(reason):
                self._invalid_totp_rejections += 1
                if self._invalid_totp_rejections >= max_invalid_totp_rejections:
                    logger.error(
                        "Epic rejected {} authenticator TOTP submission(s) as invalid "
                        "or expired. Verify EPIC_TOTP_SECRET and the host clock.",
                        self._invalid_totp_rejections,
                    )
                    raise EpicAuthenticationFatalError(reason)

            if self._totp_attempts >= max_totp_attempts:
                logger.error(
                    "Epic still requires authenticator 2FA after {} TOTP submission(s); "
                    "aborting. Verify EPIC_TOTP_SECRET, the host clock, and captcha reliability.",
                    self._totp_attempts,
                )
                raise EpicAuthenticationFatalError(reason)

            force_next_code = self._is_mfa_code_invalid_error(reason) or (
                reason == "captcha_after_mfa" and self._totp_attempts > 0
            )
            self._totp_attempts += 1
            self._drain_retryable_mfa_errors()
            if not await submit_totp_challenge(
                self.page,
                force_next_code=force_next_code,
                before_submit=self._drain_retryable_mfa_errors,
            ):
                if not self._is_mfa_page():
                    logger.warning(
                        "MFA page disappeared before fresh TOTP could be submitted; "
                        "continuing to observe login outcome | current_url='{}'",
                        self.page.url,
                    )
                    extend_deadline("mfa-page-disappeared", 60)
                    return
                raise EpicAuthenticationFatalError(reason)
            extend_deadline("totp-submit", 120)

        async def wait_for_mfa_captcha_settle(seconds: int = 8) -> bool:
            settle_deadline = time.monotonic() + seconds
            while time.monotonic() < settle_deadline:
                if (
                    not self._is_login_success_signal.empty()
                    or not self._login_error_signal.empty()
                ):
                    return True

                if not self._is_mfa_page():
                    logger.warning(
                        "MFA page disappeared after captcha; continuing to observe login outcome | current_url='{}'",
                        self.page.url,
                    )
                    extend_deadline("mfa-page-disappeared", 60)
                    return True

                if await self._has_visible_hcaptcha():
                    logger.debug(
                        "Another login captcha is visible after MFA captcha; continuing captcha handling"
                    )
                    return True

                await self.page.wait_for_timeout(500)

            return False

        while time.monotonic() < deadline:
            if not self._login_error_signal.empty():
                result = await self._login_error_signal.get()
                error_code = result.get("errorCode", "unknown_error")

                if error_code == "errors.com.epicgames.accountportal.csrf_token_invalid":
                    logger.warning(
                        "Epic login returned csrf_token_invalid, refreshing login entry and retrying | url='{}'",
                        self.page.url,
                    )
                    await self.page.context.clear_cookies()
                    await self.page.goto(point_url, wait_until="domcontentloaded")
                    await self._wait_for_login_form(point_url)
                    raise RuntimeError(error_code)

                if self._is_two_factor_required_error(error_code):
                    await submit_fresh_totp("two_factor_required")
                    continue

                if self._is_mfa_code_invalid_error(error_code):
                    logger.warning(
                        "Epic rejected authenticator TOTP code as invalid or expired; "
                        "retrying with a fresh code on the MFA page ({}/{})",
                        self._totp_attempts + 1,
                        max_totp_attempts,
                    )
                    await submit_fresh_totp(error_code)
                    continue

                raise RuntimeError(error_code)

            if not self._is_login_success_signal.empty():
                await self._is_login_success_signal.get()
                return

            if self._needs_privacy_policy_correction():
                raise RuntimeError("privacy_policy_confirmation_required")

            if self._needs_mfa_setup_prompt():
                if not await self._dismiss_mfa_setup_prompt(timeout_ms=30000):
                    raise EpicManualActionRequiredError(
                        self._mfa_setup_prompt_message(self.page.url)
                    )
                continue

            if await self._has_visible_hcaptcha():
                logger.warning(
                    "Login captcha is visible during authentication outcome; solving before "
                    "continuing | current_url='{}'",
                    self.page.url,
                )
                extend_deadline("captcha-visible", 180)
                challenge_solved = False
                try:
                    challenge_signal = await wait_for_challenge_signal(
                        agent,
                        context="login_mfa",
                        timeout_seconds=min(
                            settings.EXECUTION_TIMEOUT + settings.RESPONSE_TIMEOUT + 5,
                            max(1.0, deadline - time.monotonic()),
                        ),
                    )
                    challenge_solved = challenge_signal is ChallengeSignal.SUCCESS
                    if challenge_solved:
                        extend_deadline("captcha-solved", 120)
                    else:
                        logger.warning(
                            "Login captcha did not succeed during authentication outcome | "
                            "signal={} | current_url='{}'",
                            challenge_signal.value,
                            self.page.url,
                        )
                except Exception as err:
                    logger.warning(
                        "Login captcha solve attempt failed during authentication outcome | err={!r}",
                        err,
                    )
                    extend_deadline("captcha-attempt", 90)

                if challenge_solved and self._is_mfa_page():
                    if await wait_for_mfa_captcha_settle():
                        await self.page.wait_for_timeout(500)
                        continue

                    now = time.monotonic()
                    if now - self._last_captcha_totp_refresh_at >= captcha_totp_refresh_cooldown:
                        logger.warning(
                            "Login captcha finished while Epic is still on MFA page; submitting a "
                            "fresh authenticator TOTP code"
                        )
                        await submit_fresh_totp("captcha_after_mfa")
                        self._last_captcha_totp_refresh_at = time.monotonic()
                    else:
                        logger.debug(
                            "Skipping immediate duplicate TOTP refresh after captcha; waiting for "
                            "Epic MFA response"
                        )

                await self.page.wait_for_timeout(500)
                continue

            if self._is_mfa_page() and self._totp_attempts == 0:
                await submit_fresh_totp("mfa_page")
                continue

            if not self._is_mfa_page() and "/id/login" not in self.page.url:
                if "true" == await self._get_login_status(timeout_ms=500, warn_timeout=False):
                    return

            await self.page.wait_for_timeout(500)

        raise PlaywrightTimeoutError("Timed out waiting for Epic login outcome")

    async def _replace_page(self) -> None:
        old_page = self.page
        self.page = await old_page.context.new_page()
        self.page.on("response", self._on_response_anything)
        with suppress(Exception):
            await old_page.close()

    async def _resubmit_password_form(self) -> bool:
        password_input = self.page.locator("#password")
        sign_in_button = self.page.locator("#sign-in")

        try:
            await password_input.wait_for(state="visible", timeout=1000)
            await sign_in_button.wait_for(state="visible", timeout=1000)

            if not await password_input.input_value(timeout=1000):
                await password_input.fill(settings.EPIC_PASSWORD.get_secret_value())

            await sign_in_button.click(timeout=5000, no_wait_after=True)
            await self.page.wait_for_timeout(1000)
            return True
        except PlaywrightTimeoutError:
            return False
        except Exception as err:
            logger.warning("Could not resubmit Epic password form after captcha reset: {!r}", err)
            return False

    async def _submit_login_or_accept_challenge(self) -> None:
        if await self._has_visible_hcaptcha():
            logger.warning(
                "Login hCaptcha appeared before the sign-in button click; entering solve loop"
            )
            return

        try:
            await self.page.locator("#sign-in").click(timeout=10000, no_wait_after=True)
        except PlaywrightTimeoutError:
            if await self._has_visible_hcaptcha():
                logger.warning(
                    "Login hCaptcha replaced the sign-in button during submission; "
                    "entering solve loop"
                )
                return
            raise

    async def _get_login_status(
        self, timeout_ms: int = 30000, *, warn_timeout: bool = True
    ) -> str | None:
        if self._needs_privacy_policy_correction():
            return None

        try:
            return await self.page.locator("//egs-navigation").get_attribute(
                "isloggedin", timeout=timeout_ms
            )
        except PlaywrightTimeoutError:
            if warn_timeout:
                logger.warning(
                    "Timed out while waiting for //egs-navigation during auth check | current_url='{}'",
                    self.page.url,
                )
            return None

    async def _has_account_session(self) -> bool:
        try:
            await self.page.goto(URL_ORDER_HISTORY, wait_until="domcontentloaded", timeout=15000)
            text_content = ""
            with suppress(Exception):
                text_content = await self.page.text_content("//pre", timeout=5000) or ""
            if not text_content:
                text_content = await self.page.locator("body").inner_text(timeout=5000)
            data = json.loads(text_content or "{}")
            if not isinstance(data.get("orders"), list):
                raise RuntimeError("Epic order history payload did not contain an orders list")
            logger.success("Epic account session verified via order history endpoint")
            return True
        except Exception as err:
            logger.warning("Failed to verify Epic account session via order history: {!r}", err)
            return False

    async def _ensure_store_session_ready(self, timeout_seconds: int = 45) -> None:
        deadline = time.monotonic() + timeout_seconds
        account_probe_at = time.monotonic() + 8
        account_probe_attempted = False

        while time.monotonic() < deadline:
            if self._needs_privacy_policy_correction():
                raise EpicManualActionRequiredError(
                    self._privacy_policy_confirmation_message(self.page.url)
                )

            if self._needs_mfa_setup_prompt():
                if not await self._dismiss_mfa_setup_prompt(timeout_ms=30000):
                    raise EpicManualActionRequiredError(
                        self._mfa_setup_prompt_message(self.page.url)
                    )
                await self._goto_claim_page()
                continue

            status = await self._get_login_status(timeout_ms=1500)
            if status == "true":
                return
            if status == "false":
                raise RuntimeError(
                    "Epic store still reports isloggedin=false after authentication. "
                    f"current_url={self.page.url}"
                )

            if not account_probe_attempted and time.monotonic() >= account_probe_at:
                account_probe_attempted = True
                logger.warning(
                    "Epic navigation login marker did not appear after authentication; "
                    "probing account session via order history."
                )
                if await self._has_account_session():
                    return
                await self._goto_claim_page()

            await self.page.wait_for_timeout(500)

        if self._needs_mfa_setup_prompt():
            raise EpicManualActionRequiredError(self._mfa_setup_prompt_message(self.page.url))

        if await self._has_account_session():
            return

        raise RuntimeError(
            "Could not verify Epic store access after authentication. "
            f"current_url={self.page.url}"
        )

    async def _login(self) -> bool | None:
        # 尽可能早地初始化机器人
        agent = AgentV(page=self.page, agent_config=settings)

        # {{< SIGN IN PAGE >}}
        logger.debug("Login with Email")

        try:
            self._drain_queue(self._is_login_success_signal)
            self._drain_queue(self._login_error_signal)
            self._drain_queue(self._is_refresh_csrf_signal)

            point_url = "https://www.epicgames.com/account/personal?lang=en-US&productName=egs&sessionInvalidated=true"
            await self.page.goto(point_url, wait_until="domcontentloaded")
            await self._wait_for_login_form(point_url)

            # 1. 使用电子邮件地址登录
            email_input = self.page.locator("#email")
            await email_input.fill(settings.EPIC_EMAIL)

            # 2. 点击继续按钮
            await self.page.click("#continue")

            # 3. 输入密码
            password_input = self.page.locator("#password")
            await expect(password_input).to_be_visible(timeout=10000)
            await password_input.fill(settings.EPIC_PASSWORD.get_secret_value())

            # 4. 点击登录按钮，触发人机挑战值守监听器
            # Active hCaptcha checkbox
            await self._submit_login_or_accept_challenge()

            login_confirmed = False
            for challenge_attempt in range(1, 4):
                logger.debug("Solving login challenge attempt {}/3", challenge_attempt)
                challenge_signal = ChallengeSignal.FAILURE
                try:
                    challenge_signal = await wait_for_challenge_signal(
                        agent,
                        context=f"login:{challenge_attempt}",
                        timeout_seconds=(
                            settings.EXECUTION_TIMEOUT + settings.RESPONSE_TIMEOUT + 5
                        ),
                    )
                except Exception:
                    pass

                try:
                    await self._await_login_outcome(point_url, agent, timeout_seconds=25)
                    login_confirmed = True
                    break
                except PlaywrightTimeoutError:
                    if await self._has_visible_hcaptcha():
                        logger.warning(
                            "Login outcome timed out while captcha is still visible; "
                            "retrying solve attempt {}/3 | signal={}",
                            challenge_attempt,
                            challenge_signal.value,
                        )
                        continue

                    if challenge_attempt < 3 and await self._resubmit_password_form():
                        logger.warning(
                            "Login captcha disappeared without authentication; resubmitted the "
                            "password form before solve attempt {}/3",
                            challenge_attempt + 1,
                        )
                        try:
                            await self._await_login_outcome(point_url, agent, timeout_seconds=8)
                            login_confirmed = True
                            break
                        except PlaywrightTimeoutError:
                            if not await self._has_visible_hcaptcha():
                                raise
                        continue

                    raise

            if not login_confirmed:
                await self._await_login_outcome(point_url, agent, timeout_seconds=10)
            logger.success("Login success")

            if self._needs_mfa_setup_prompt() and not await self._dismiss_mfa_setup_prompt(
                timeout_ms=30000
            ):
                raise EpicManualActionRequiredError(self._mfa_setup_prompt_message(self.page.url))

            await asyncio.wait_for(self._handle_right_account_validation(), timeout=60)
            logger.success("Right account validation success")
            await self._goto_claim_page()
            await self._ensure_store_session_ready()
            logger.success("Epic store session verification success")
            return True
        except Exception as err:
            logger.warning(f"Login attempt failed: {err!r}")
            sr = SCREENSHOTS_DIR.joinpath("authorization")
            sr.mkdir(parents=True, exist_ok=True)
            with suppress(Exception):
                await redact_totp_inputs(self.page)
            await self.page.screenshot(path=sr.joinpath(f"login-{int(time.time())}.png"))
            if isinstance(err, EpicAuthenticationFatalError):
                logger.error(
                    "Epic account requires two-factor authentication. Configure EPIC_TOTP_SECRET "
                    "for authenticator app 2FA, or disable Epic 2FA and rerun the workflow."
                )
                raise
            if isinstance(err, EpicManualActionRequiredError):
                logger.error(str(err))
                raise
            return None

    async def invoke(self) -> bool:
        self.page.on("response", self._on_response_anything)
        self._totp_attempts = 0
        self._invalid_totp_rejections = 0
        self._last_captcha_totp_refresh_at = 0.0

        max_attempts = settings.AUTH_MAX_ATTEMPTS
        for attempt in range(1, max_attempts + 1):
            await self._goto_claim_page()

            if self._needs_privacy_policy_correction():
                logger.error(
                    "Epic account requires a manual privacy-policy confirmation | current_url='{}'",
                    self.page.url,
                )
                return False

            if "true" == await self._get_login_status():
                logger.success("Epic Games is already logged in")
                return True

            try:
                if await self._login():
                    return True
            except EpicManualActionRequiredError:
                raise
            except EpicAuthenticationFatalError:
                logger.error("Authentication aborted because Epic 2FA is still enabled")
                return False

            if attempt < max_attempts:
                logger.warning(
                    "Authentication attempt {}/{} failed; resetting page state before retry",
                    attempt,
                    max_attempts,
                )
                with suppress(Exception):
                    await self.page.context.clear_cookies()
                await self._replace_page()

        logger.error("Epic Games authentication failed after {} attempts", max_attempts)
        return False
