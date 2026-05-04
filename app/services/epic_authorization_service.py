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
from loguru import logger
from playwright.async_api import expect, Page, Response
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from settings import SCREENSHOTS_DIR, settings

URL_CLAIM = "https://store.epicgames.com/en-US/free-games"


class EpicAuthenticationFatalError(RuntimeError):
    pass


class EpicAuthorization:

    def __init__(self, page: Page):
        self.page = page

        self._is_login_success_signal = asyncio.Queue()
        self._login_error_signal = asyncio.Queue()
        self._is_refresh_csrf_signal = asyncio.Queue()

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

    @staticmethod
    def _is_two_factor_required_error(error_code: str) -> bool:
        return error_code == "errors.com.epicgames.common.two_factor_authentication.required"

    async def _handle_right_account_validation(self):
        """
        以下验证仅会在登录成功后出现
        Returns:

        """
        await self.page.goto("https://www.epicgames.com/account/personal", wait_until="networkidle")

        btn_ids = ["#link-success", "#login-reminder-prompt-setup-tfa-skip", "#yes"]

        # == 账号长期不登录需要做的额外验证 == #

        while self._is_refresh_csrf_signal.empty() and btn_ids:
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

    async def _page_body_text(self) -> str:
        with suppress(Exception):
            return await self.page.locator("body").inner_text(timeout=1000)
        return ""

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

    async def _await_login_outcome(self, point_url: str, timeout_seconds: int = 60) -> None:
        deadline = time.monotonic() + timeout_seconds

        while time.monotonic() < deadline:
            if "true" == await self._get_login_status():
                return

            if self._needs_privacy_policy_correction():
                raise RuntimeError("privacy_policy_confirmation_required")

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
                    raise EpicAuthenticationFatalError(error_code)

                raise RuntimeError(error_code)

            if not self._is_login_success_signal.empty():
                await self._is_login_success_signal.get()
                return

            await self.page.wait_for_timeout(500)

        raise PlaywrightTimeoutError("Timed out waiting for Epic login outcome")

    async def _replace_page(self) -> None:
        old_page = self.page
        self.page = await old_page.context.new_page()
        self.page.on("response", self._on_response_anything)
        with suppress(Exception):
            await old_page.close()

    async def _get_login_status(self) -> str | None:
        if self._needs_privacy_policy_correction():
            return None

        try:
            return await self.page.locator("//egs-navigation").get_attribute("isloggedin")
        except PlaywrightTimeoutError:
            logger.warning(
                "Timed out while waiting for //egs-navigation during auth check | current_url='{}'",
                self.page.url,
            )
            return None

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
            await self.page.click("#sign-in")

            login_confirmed = False
            for challenge_attempt in range(1, 4):
                logger.debug("Solving login challenge attempt {}/3", challenge_attempt)
                with suppress(Exception):
                    await agent.wait_for_challenge()

                try:
                    await self._await_login_outcome(point_url, timeout_seconds=25)
                    login_confirmed = True
                    break
                except PlaywrightTimeoutError:
                    if not await self._has_visible_hcaptcha():
                        raise
                    logger.warning(
                        "Login outcome timed out while captcha is still visible; retrying solve "
                        "attempt {}/3",
                        challenge_attempt,
                    )

            if not login_confirmed:
                await self._await_login_outcome(point_url, timeout_seconds=10)
            logger.success("Login success")

            await asyncio.wait_for(self._handle_right_account_validation(), timeout=60)
            logger.success("Right account validation success")
            return True
        except Exception as err:
            logger.warning(f"Login attempt failed: {err!r}")
            sr = SCREENSHOTS_DIR.joinpath("authorization")
            sr.mkdir(parents=True, exist_ok=True)
            await self.page.screenshot(path=sr.joinpath(f"login-{int(time.time())}.png"))
            if isinstance(err, EpicAuthenticationFatalError):
                logger.error(
                    "Epic account requires two-factor authentication, which is not supported by this project. "
                    "Disable Epic 2FA (email / SMS / authenticator) and rerun the workflow."
                )
                raise
            return None

    async def invoke(self) -> bool:
        self.page.on("response", self._on_response_anything)

        for attempt in range(1, 4):
            await self.page.goto(URL_CLAIM, wait_until="domcontentloaded")

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
            except EpicAuthenticationFatalError:
                logger.error("Authentication aborted because Epic 2FA is still enabled")
                return False

            if attempt < 3:
                logger.warning(
                    "Authentication attempt {}/3 failed; resetting page state before retry", attempt
                )
                with suppress(Exception):
                    await self.page.context.clear_cookies()
                await self._replace_page()

        logger.error("Epic Games authentication failed after 3 attempts")
        return False
