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
from typing import Any

os.environ.setdefault("MPLBACKEND", "Agg")

from hcaptcha_challenger.agent import AgentV
from hcaptcha_challenger.models import ChallengeSignal
from loguru import logger
from playwright.async_api import Error as PlaywrightError
from playwright.async_api import expect, Page, Response
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from extensions.hcaptcha_adapter import (
    begin_captcha_attempt,
    install_captcha_request_tracking,
    prepare_captcha_retry,
)
from extensions.hcaptcha_runtime import wait_for_challenge_signal
from services.epic_totp_service import redact_totp_inputs, submit_totp_challenge, totp_login_enabled
from settings import SCREENSHOTS_DIR, settings

URL_CLAIM = "https://store.epicgames.com/en-US/free-games"
URL_ORDER_HISTORY = "https://www.epicgames.com/account/v2/payment/ajaxGetOrderHistory"
MAX_LOGIN_CAPTCHA_ATTEMPTS = 3
MAX_LOGIN_CAPTCHA_ROUNDS = 6
LOGIN_SUBMISSION_RESPONSE_TIMEOUT_SECONDS = 15.0


class EpicAuthenticationFatalError(RuntimeError):
    pass


class EpicManualActionRequiredError(RuntimeError):
    pass


class EpicLoginRestartRequiredError(RuntimeError):
    """The login page returned to an earlier step and needs one clean retry."""


class EpicAuthorization:

    def __init__(self, page: Page):
        self.page = page

        self._is_login_success_signal = asyncio.Queue()
        self._login_error_signal = asyncio.Queue()
        self._is_refresh_csrf_signal = asyncio.Queue()
        self._login_submission_response_signal = asyncio.Queue()
        self._login_submission_generation = 0
        self._login_request_generations: dict[int, tuple[Any, int]] = {}
        self._login_submission_armed_generation: int | None = None
        self._totp_attempts = 0
        self._invalid_totp_rejections = 0

    @staticmethod
    def _request_identity(request: Any) -> Any:
        return getattr(request, "_impl_obj", request)

    def _on_request(self, request: Any) -> None:
        if request.method != "POST" or "/id/api/login" not in request.url:
            return

        identity = self._request_identity(request)
        generation = self._login_submission_armed_generation or 0
        self._login_request_generations[id(identity)] = (identity, generation)
        if generation:
            self._login_submission_armed_generation = None

    def _begin_login_submission(self) -> int:
        self._drain_queue(self._login_submission_response_signal)
        self._login_submission_generation += 1
        self._login_submission_armed_generation = self._login_submission_generation
        return self._login_submission_generation

    def _take_login_request_generation(self, request: Any) -> int | None:
        identity = self._request_identity(request)
        entry = self._login_request_generations.pop(id(identity), None)
        if entry is None or entry[0] is not identity:
            return None
        return entry[1] or None

    async def _wait_for_login_submission_response(
        self, generation: int, timeout_seconds: float = LOGIN_SUBMISSION_RESPONSE_TIMEOUT_SECONDS
    ) -> tuple[dict, int] | None:
        if not generation:
            return None

        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            remaining = max(0.1, deadline - time.monotonic())
            try:
                record = await asyncio.wait_for(
                    self._login_submission_response_signal.get(), timeout=remaining
                )
            except asyncio.TimeoutError:
                return None

            if record.get("generation") != generation:
                continue
            result = record.get("result")
            result = result if isinstance(result, dict) else {}
            return result, int(record.get("status") or 0)

        return None

    def _remove_login_error(self, target: dict) -> None:
        retained = []
        while not self._login_error_signal.empty():
            with suppress(Exception):
                result = self._login_error_signal.get_nowait()
                if result is not target:
                    retained.append(result)
        for result in retained:
            self._login_error_signal.put_nowait(result)

    async def _await_submission_before_retry(self, generation: int) -> dict:
        record = await self._wait_for_login_submission_response(generation)
        if record is None:
            raise EpicLoginRestartRequiredError(
                "Epic login submission did not return before a captcha retry"
            )

        result, status = record
        self._remove_login_error(result)
        error_code = result.get("errorCode", "")
        if error_code == "errors.com.epicgames.accountportal.csrf_token_invalid":
            raise EpicLoginRestartRequiredError("Epic rejected the login page CSRF token")
        if status >= 400 and not error_code:
            raise EpicLoginRestartRequiredError(
                f"Epic login submission returned HTTP {status} without an error payload"
            )
        if error_code and not (
            self._is_captcha_rejected_error(error_code)
            or self._is_two_factor_required_error(error_code)
            or self._is_mfa_code_invalid_error(error_code)
        ):
            raise RuntimeError(error_code)
        return result

    async def _on_response_anything(self, r: Response):
        if r.request.method != "POST" or "talon" in r.url:
            return

        result: dict = {}
        with suppress(Exception):
            parsed = await r.json()
            if isinstance(parsed, dict):
                result = parsed

        result_json = json.dumps(result, indent=2, ensure_ascii=False)
        if "/id/api/login" in r.url:
            generation = self._take_login_request_generation(r.request)
            if generation is None or generation != self._login_submission_generation:
                logger.debug(
                    "Ignoring stale or untracked Epic login response | generation={} current={}",
                    generation,
                    self._login_submission_generation,
                )
                return

            self._login_submission_response_signal.put_nowait(
                {"generation": generation, "result": result, "status": r.status}
            )
            if result.get("errorCode"):
                self._login_error_signal.put_nowait(result)
                logger.error(f"{r.request.method} {r.url} - {result_json}")
            return

        if "/id/api/analytics" in r.url and result.get("accountId"):
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

    @staticmethod
    def _is_captcha_rejected_error(error_code: str) -> bool:
        normalized = (error_code or "").casefold()
        return "captcha" in normalized and any(
            marker in normalized for marker in ("invalid", "incorrect", "expired", "failed")
        )

    @staticmethod
    def _is_incorrect_login_response(value: str) -> bool:
        normalized = " ".join((value or "").casefold().split())
        return "incorrect response" in normalized and "refresh" in normalized

    async def _is_email_login_step(self) -> bool:
        with suppress(Exception):
            email_visible = await self.page.locator("#email").is_visible()
            password_visible = await self.page.locator("#password").is_visible()
            return email_visible and not password_visible
        return False

    async def _has_incorrect_login_response(self) -> bool:
        return self._is_incorrect_login_response(await self._page_body_text())

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

    async def _has_visible_hcaptcha_challenge(self) -> bool:
        """Return true only while the interactive challenge iframe is visible.

        hCaptcha keeps its checkbox iframe mounted after a challenge succeeds. Treating every
        hCaptcha iframe as an active challenge makes the login loop consume the same result again.
        """
        for frame in self.page.frames:
            frame_url = (frame.url or "").lower()
            if "hcaptcha" not in frame_url or "frame=challenge" not in frame_url:
                continue

            with suppress(Exception):
                challenge_view = frame.locator("//div[@class='challenge-view']")
                if await challenge_view.is_visible(timeout=500):
                    return True

        return False

    async def _has_visible_hcaptcha_checkbox(self) -> bool:
        for frame in self.page.frames:
            frame_url = (frame.url or "").lower()
            if "hcaptcha" not in frame_url or "frame=checkbox" not in frame_url:
                continue

            with suppress(Exception):
                checkbox = frame.locator("//div[@id='checkbox']")
                if await checkbox.is_visible(timeout=500):
                    return True

        return False

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
                        "Pre-login security page detected; reloading without clearing the "
                        "persistent browser session ({}/2) | url='{}'",
                        recovery_attempts,
                        self.page.url,
                    )
                    await self.page.goto(point_url, wait_until="domcontentloaded")
                    continue

                logger.warning(
                    "Pre-login security page still active after recovery attempts | url='{}'",
                    self.page.url,
                )
                raise EpicLoginRestartRequiredError(
                    "Epic pre-login security check did not clear after bounded reloads"
                )

            await self.page.wait_for_timeout(500)

        raise PlaywrightTimeoutError("Timed out waiting for Epic login form")

    async def _solve_login_captcha(
        self, agent: AgentV, *, context: str, attempt: int, timeout_seconds: float
    ) -> ChallengeSignal:
        try:
            signal = await wait_for_challenge_signal(
                agent, context=context, timeout_seconds=max(1.0, timeout_seconds)
            )
        except Exception as err:
            logger.warning(
                "Epic login hCaptcha attempt failed | context={} | attempt={} | err={!r}",
                context,
                attempt,
                err,
            )
            return ChallengeSignal.FAILURE

        logger.info(
            "Epic login hCaptcha result | context={} | attempt={} | signal={}",
            context,
            attempt,
            signal.value,
        )
        return signal

    async def _activate_hcaptcha_checkbox(self, agent: AgentV) -> bool:
        if not await self._has_visible_hcaptcha_checkbox():
            return False

        try:
            for frame in self.page.frames:
                if "frame=checkbox" not in (frame.url or "").lower():
                    continue
                checkbox = frame.locator("//div[@id='checkbox']")
                if await checkbox.is_visible(timeout=500):
                    if await checkbox.get_attribute("aria-checked") == "true":
                        return True
                    # The checkbox can emit the first response before the challenge iframe is
                    # visible, so arm the attempt before sending the click.
                    await begin_captcha_attempt(agent, fresh=True)
                    await agent.robotic_arm.click_by_mouse(checkbox)
                    await self.page.wait_for_timeout(500)
                    return True
        except Exception as err:
            logger.warning("Could not activate the Epic hCaptcha checkbox: {!r}", err)
            return False

        return False

    async def _wait_for_hcaptcha_settle(self, timeout_ms: int = 8000) -> bool:
        deadline = time.monotonic() + timeout_ms / 1000
        while time.monotonic() < deadline:
            if not await self._has_visible_hcaptcha_challenge():
                return True
            await self.page.wait_for_timeout(250)
        return not await self._has_visible_hcaptcha_challenge()

    async def _advance_email_login(self, agent: AgentV) -> None:
        """Advance the email step while allowing Epic to challenge before Continue."""
        email_input = self.page.locator("#email")
        continue_button = self.page.locator("#continue")
        await expect(email_input).to_be_visible(timeout=10000)
        await email_input.fill(settings.EPIC_EMAIL)
        with suppress(Exception):
            await email_input.press("Tab")

        deadline = time.monotonic() + settings.AUTH_TIMEOUT_SECONDS
        disabled_since: float | None = None
        continue_submitted_at: float | None = None
        submission_generation: int | None = None
        captcha_attempts = 0
        captcha_rejections = 0

        while time.monotonic() < deadline:
            if not self._login_error_signal.empty():
                result = await self._login_error_signal.get()
                error_code = result.get("errorCode", "unknown_error")
                if error_code == "errors.com.epicgames.accountportal.csrf_token_invalid":
                    raise EpicLoginRestartRequiredError(
                        "Epic rejected the email login page CSRF token"
                    )
                if self._is_captcha_rejected_error(error_code):
                    captcha_rejections += 1
                    await prepare_captcha_retry(agent)
                    if captcha_rejections > MAX_LOGIN_CAPTCHA_ATTEMPTS:
                        raise EpicLoginRestartRequiredError(
                            "Epic rejected too many email-step hCaptcha responses"
                        )
                    logger.warning(
                        "Epic rejected the email-step hCaptcha response; waiting for a fresh "
                        "challenge | rejection={}/{}",
                        captcha_rejections,
                        MAX_LOGIN_CAPTCHA_ATTEMPTS,
                    )
                    await self.page.wait_for_timeout(500)
                    continue
                if self._is_two_factor_required_error(error_code):
                    await self.page.wait_for_timeout(250)
                    continue
                raise RuntimeError(error_code)

            if await self._has_incorrect_login_response():
                raise EpicLoginRestartRequiredError(
                    "Epic rejected the login challenge and returned to the email step"
                )

            if await self._has_visible_hcaptcha_challenge():
                captcha_attempts += 1
                if captcha_attempts > MAX_LOGIN_CAPTCHA_ATTEMPTS:
                    raise EpicLoginRestartRequiredError(
                        "Epic email-step hCaptcha exceeded the bounded retry limit"
                    )
                signal = await self._solve_login_captcha(
                    agent,
                    context="login_email",
                    attempt=captcha_attempts,
                    timeout_seconds=min(
                        settings.EXECUTION_TIMEOUT + settings.RESPONSE_TIMEOUT + 5,
                        max(1.0, deadline - time.monotonic()),
                    ),
                )
                if signal is not ChallengeSignal.SUCCESS:
                    logger.warning(
                        "Epic email-step hCaptcha did not succeed; keeping the login page for "
                        "another bounded attempt | attempt={}/{}",
                        captcha_attempts,
                        MAX_LOGIN_CAPTCHA_ATTEMPTS,
                    )
                    await self.page.wait_for_timeout(750)
                    continue
                captcha_rejections = 0
                if not await self._wait_for_hcaptcha_settle():
                    logger.warning(
                        "Epic email-step hCaptcha did not settle; retrying on the same page | "
                        "attempt={}/{}",
                        captcha_attempts,
                        MAX_LOGIN_CAPTCHA_ATTEMPTS,
                    )
                    await self.page.wait_for_timeout(750)
                    continue
                disabled_since = None
                continue_submitted_at = None
                continue

            password_visible = False
            with suppress(Exception):
                password_visible = await self.page.locator("#password").is_visible()
            if password_visible:
                if submission_generation is not None:
                    await self._await_submission_before_retry(submission_generation)
                    submission_generation = None
                logger.debug("Epic email login step advanced to password")
                return

            if not await self._is_email_login_step():
                await self.page.wait_for_timeout(250)
                continue

            continue_visible = False
            continue_enabled = False
            with suppress(Exception):
                continue_visible = await continue_button.is_visible()
                if continue_visible:
                    continue_enabled = await continue_button.is_enabled()

            # A visible enabled button wins over the checkbox iframe, which may remain mounted
            # for a short time after hCaptcha has already supplied its token.
            if continue_visible and continue_enabled:
                if continue_submitted_at is None:
                    if submission_generation is not None:
                        await self._await_submission_before_retry(submission_generation)
                        submission_generation = None

                    # The email Continue action can inject hCaptcha before the challenge iframe
                    # becomes visible to the polling loop.
                    await begin_captcha_attempt(agent, fresh=True)
                    generation = self._begin_login_submission()
                    try:
                        await continue_button.click(timeout=10000, no_wait_after=True)
                    except PlaywrightTimeoutError:
                        password_visible = False
                        with suppress(Exception):
                            password_visible = await self.page.locator("#password").is_visible()
                        if password_visible:
                            await self._await_submission_before_retry(generation)
                            logger.debug("Epic email login advanced while Continue was replaced")
                            return
                        if await self._has_visible_hcaptcha_challenge():
                            continue_submitted_at = time.monotonic()
                            submission_generation = generation
                            continue
                        raise
                    submission_generation = generation
                    continue_submitted_at = time.monotonic()
                    captcha_attempts = 0
                    captcha_rejections = 0
                    disabled_since = None
                elif time.monotonic() - continue_submitted_at >= 15:
                    raise EpicLoginRestartRequiredError(
                        "Epic email Continue did not advance to the password step"
                    )
                await self.page.wait_for_timeout(250)
                continue

            if continue_visible and not continue_enabled:
                disabled_since = disabled_since or time.monotonic()
                if await self._has_visible_hcaptcha_checkbox():
                    await self._activate_hcaptcha_checkbox(agent)
                    await self.page.wait_for_timeout(500)
                    continue
                if time.monotonic() - disabled_since >= 20:
                    raise EpicLoginRestartRequiredError(
                        "Epic email Continue remained disabled without an active challenge"
                    )

            await self.page.wait_for_timeout(500)

        raise EpicLoginRestartRequiredError("Timed out advancing the Epic email login step")

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
        self, agent: AgentV, timeout_seconds: int = 300, *, initial_submission_generation: int = 0
    ) -> None:
        started_at = time.monotonic()
        deadline = started_at + timeout_seconds
        hard_timeout_seconds = max(timeout_seconds, 180)
        max_deadline = started_at + hard_timeout_seconds
        max_totp_attempts = 6
        max_invalid_totp_rejections = 3
        last_submission = "password"
        submission_generation = initial_submission_generation
        captcha_attempts = 0
        total_captcha_attempts = 0
        captcha_rejections = 0

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
            nonlocal last_submission, submission_generation, captcha_attempts, captcha_rejections

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
            new_submission_generation: int | None = None

            def before_totp_submit() -> None:
                nonlocal new_submission_generation
                new_submission_generation = self._begin_login_submission()
                self._drain_retryable_mfa_errors()

            # Epic may create the hCaptcha payload immediately after the MFA submit click.
            # Arm the response window before the button action so payload and checkcaptcha
            # responses receive this submission's generation.
            await begin_captcha_attempt(agent, fresh=True)
            if not await submit_totp_challenge(
                self.page, force_next_code=force_next_code, before_submit=before_totp_submit
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
            last_submission = "totp"
            submission_generation = new_submission_generation or self._login_submission_generation
            captcha_attempts = 0
            captcha_rejections = 0
            extend_deadline("totp-submit", 120)

        while time.monotonic() < deadline:
            if not self._is_login_success_signal.empty():
                await self._is_login_success_signal.get()
                return

            if not self._login_error_signal.empty():
                result = await self._login_error_signal.get()
                error_code = result.get("errorCode", "unknown_error")

                if error_code == "errors.com.epicgames.accountportal.csrf_token_invalid":
                    raise EpicLoginRestartRequiredError("Epic rejected the login page CSRF token")

                if self._is_captcha_rejected_error(error_code):
                    captcha_rejections += 1
                    await prepare_captcha_retry(agent)
                    if captcha_rejections > MAX_LOGIN_CAPTCHA_ATTEMPTS:
                        raise EpicLoginRestartRequiredError(
                            "Epic rejected too many login hCaptcha responses"
                        )
                    logger.warning(
                        "Epic rejected the login hCaptcha response; keeping the current page "
                        "for a fresh challenge | rejection={}/{}",
                        captcha_rejections,
                        MAX_LOGIN_CAPTCHA_ATTEMPTS,
                    )
                    await self.page.wait_for_timeout(500)
                    continue

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

            if self._needs_privacy_policy_correction():
                raise RuntimeError("privacy_policy_confirmation_required")

            if self._needs_mfa_setup_prompt():
                if not await self._dismiss_mfa_setup_prompt(timeout_ms=30000):
                    raise EpicManualActionRequiredError(
                        self._mfa_setup_prompt_message(self.page.url)
                    )
                continue

            if await self._has_visible_hcaptcha_challenge():
                captcha_attempts += 1
                total_captcha_attempts += 1
                if (
                    captcha_attempts > MAX_LOGIN_CAPTCHA_ATTEMPTS
                    or total_captcha_attempts > MAX_LOGIN_CAPTCHA_ROUNDS
                ):
                    raise EpicLoginRestartRequiredError(
                        "Epic login hCaptcha exceeded the bounded retry limit"
                    )

                logger.warning(
                    "Login captcha is visible during authentication outcome; solving before "
                    "continuing | submission={} generation={} attempt={}/{} total={}/{} "
                    "current_url='{}'",
                    last_submission,
                    submission_generation,
                    captcha_attempts,
                    MAX_LOGIN_CAPTCHA_ATTEMPTS,
                    total_captcha_attempts,
                    MAX_LOGIN_CAPTCHA_ROUNDS,
                    self.page.url,
                )
                extend_deadline("captcha-visible", 180)
                challenge_signal = await self._solve_login_captcha(
                    agent,
                    context=f"login_{last_submission}",
                    attempt=captcha_attempts,
                    timeout_seconds=min(
                        settings.EXECUTION_TIMEOUT + settings.RESPONSE_TIMEOUT + 5,
                        max(1.0, deadline - time.monotonic()),
                    ),
                )
                if challenge_signal is not ChallengeSignal.SUCCESS:
                    logger.warning(
                        "Epic login hCaptcha did not succeed; retrying on the current page | "
                        "submission={} attempt={}/{}",
                        last_submission,
                        captcha_attempts,
                        MAX_LOGIN_CAPTCHA_ATTEMPTS,
                    )
                    await self.page.wait_for_timeout(500)
                    continue

                captcha_rejections = 0
                extend_deadline("captcha-solved", 120)
                if not await self._wait_for_hcaptcha_settle():
                    raise EpicLoginRestartRequiredError(
                        "Epic login hCaptcha did not settle after a successful response"
                    )

                await self.page.wait_for_timeout(500)
                if last_submission == "totp" and self._is_mfa_page():
                    response = await self._await_submission_before_retry(submission_generation)
                    error_code = response.get("errorCode", "")
                    if self._is_captcha_rejected_error(error_code):
                        logger.warning(
                            "Login captcha finished after the previous MFA request was rejected; "
                            "submitting a fresh authenticator TOTP code"
                        )
                        await submit_fresh_totp("captcha_after_mfa")
                    elif self._is_mfa_code_invalid_error(error_code):
                        await submit_fresh_totp(error_code)
                    elif self._is_two_factor_required_error(error_code):
                        await submit_fresh_totp("two_factor_required")
                elif last_submission == "password":
                    if submission_generation:
                        response = await self._await_submission_before_retry(submission_generation)
                        error_code = response.get("errorCode", "")
                        if self._is_two_factor_required_error(error_code):
                            continue

                    if (
                        not self._is_login_success_signal.empty()
                        or self._is_mfa_page()
                        or "/id/login" not in self.page.url.lower()
                    ):
                        continue

                    submitted = await self._resubmit_password_form(agent)
                    if submitted:
                        submission_generation = submitted
                        captcha_attempts = 0
                        captcha_rejections = 0
                    elif (
                        not self._is_login_success_signal.empty()
                        or self._is_mfa_page()
                        or "/id/login" not in self.page.url
                    ):
                        logger.debug(
                            "Epic password form disappeared after captcha; continuing to "
                            "observe the authentication result"
                        )
                    else:
                        raise EpicLoginRestartRequiredError(
                            "Epic login captcha succeeded but the password form could not be resubmitted"
                        )
                    if submitted:
                        logger.info("Resubmitted Epic password form after login hCaptcha")

                continue

            if await self._is_email_login_step():
                if await self._has_incorrect_login_response():
                    raise EpicLoginRestartRequiredError(
                        "Epic rejected the login challenge and returned to the email step"
                    )
                raise EpicLoginRestartRequiredError(
                    "Epic returned to the email step before authentication completed"
                )

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
        self.page.on("request", self._on_request)
        self.page.on("response", self._on_response_anything)
        self._login_request_generations.clear()
        self._login_submission_armed_generation = None
        with suppress(Exception):
            await old_page.close()

    async def _resubmit_password_form(self, agent: AgentV) -> int | None:
        if (
            not self._is_login_success_signal.empty()
            or self._is_mfa_page()
            or "/id/login" not in self.page.url.lower()
        ):
            return None

        password_input = self.page.locator("#password")
        sign_in_button = self.page.locator("#sign-in")

        try:
            await password_input.wait_for(state="visible", timeout=5000)
            if self._is_mfa_page() or "/id/login" not in self.page.url.lower():
                return None
            await sign_in_button.wait_for(state="visible", timeout=5000)
            await expect(sign_in_button).to_be_enabled(timeout=5000)

            if not await password_input.input_value(timeout=1000):
                await password_input.fill(settings.EPIC_PASSWORD.get_secret_value())

            # A password submit can synchronously replace the form with hCaptcha. Start tracking
            # before the click, rather than when the later challenge poll notices the iframe.
            await begin_captcha_attempt(agent, fresh=True)
            generation = self._begin_login_submission()
            try:
                await sign_in_button.click(timeout=5000, no_wait_after=True)
            except PlaywrightTimeoutError:
                if await self._has_visible_hcaptcha_challenge() or self._is_mfa_page():
                    return generation
                raise
            await self.page.wait_for_timeout(500)
            return generation
        except PlaywrightTimeoutError:
            return None
        except Exception as err:
            logger.warning("Could not resubmit Epic password form after captcha reset: {!r}", err)
            return None

    async def _submit_login_or_accept_challenge(self, agent: AgentV) -> int | None:
        if await self._has_visible_hcaptcha_challenge():
            logger.warning(
                "Login hCaptcha appeared before the sign-in button click; entering solve loop"
            )
            return None

        sign_in_button = self.page.locator("#sign-in")
        await sign_in_button.wait_for(state="visible", timeout=10000)

        checkbox_activated = False
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            if await self._has_visible_hcaptcha_challenge():
                logger.warning("Login hCaptcha appeared before the sign-in submission completed")
                return None

            if await sign_in_button.is_enabled():
                # Epic can return the initial getcaptcha payload while the click is still being
                # handled. Open the captcha generation before submitting the form.
                await begin_captcha_attempt(agent, fresh=True)
                generation = self._begin_login_submission()
                try:
                    await sign_in_button.click(timeout=5000, no_wait_after=True)
                except PlaywrightTimeoutError:
                    if await self._has_visible_hcaptcha_challenge() or self._is_mfa_page():
                        return generation
                    raise
                return generation

            if not checkbox_activated and await self._has_visible_hcaptcha_checkbox():
                checkbox_activated = await self._activate_hcaptcha_checkbox(agent)

            await self.page.wait_for_timeout(250)

        raise EpicLoginRestartRequiredError(
            "Epic sign-in button remained disabled without an active hCaptcha challenge"
        )

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
        install_captcha_request_tracking(agent)

        # {{< SIGN IN PAGE >}}
        logger.debug("Login with Email")

        try:
            self._drain_queue(self._is_login_success_signal)
            self._drain_queue(self._login_error_signal)
            self._drain_queue(self._is_refresh_csrf_signal)
            self._drain_queue(self._login_submission_response_signal)
            self._login_request_generations.clear()
            self._login_submission_armed_generation = None

            # Keep the persistent profile valid. Forcing sessionInvalidated on every run makes
            # Epic re-authenticate even when the browser already has a usable session.
            point_url = "https://www.epicgames.com/account/personal?lang=en-US&productName=egs"
            await self.page.goto(point_url, wait_until="domcontentloaded")
            await self._wait_for_login_form(point_url)

            # Epic can open hCaptcha on the email step, before the password form exists.
            await self._advance_email_login(agent)

            password_input = self.page.locator("#password")
            await expect(password_input).to_be_visible(timeout=10000)
            await password_input.fill(settings.EPIC_PASSWORD.get_secret_value())

            submission_generation = await self._submit_login_or_accept_challenge(agent)
            await self._await_login_outcome(
                agent,
                timeout_seconds=settings.AUTH_TIMEOUT_SECONDS,
                initial_submission_generation=submission_generation or 0,
            )

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
        self.page.on("request", self._on_request)
        self.page.on("response", self._on_response_anything)

        max_attempts = settings.AUTH_MAX_ATTEMPTS
        for attempt in range(1, max_attempts + 1):
            self._totp_attempts = 0
            self._invalid_totp_rejections = 0
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
                    "Authentication attempt {}/{} failed; replacing the page while preserving "
                    "the browser session",
                    attempt,
                    max_attempts,
                )
                await self._replace_page()

        logger.error("Epic Games authentication failed after {} attempts", max_attempts)
        return False
