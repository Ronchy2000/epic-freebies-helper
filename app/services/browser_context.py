# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import sys
from contextlib import asynccontextmanager, suppress
from typing import AsyncIterator
from urllib.parse import unquote, urlsplit

from loguru import logger
from playwright.async_api import BrowserContext, Route, ViewportSize, async_playwright
from requests import HTTPError, RequestException

from settings import RECORD_DIR, settings

_VIEWPORT = ViewportSize(width=1920, height=1080)
_TRUE_VALUES = {"1", "true", "yes", "on"}
_FALSE_VALUES = {"0", "false", "no", "off"}
_PROXY_SCHEMES = {"http", "https", "socks4", "socks5"}


def resolve_headless_mode(value: bool | str | None = None) -> bool | str:
    raw_value = os.getenv("HEADLESS") if value is None else value
    default: bool | str = "virtual" if sys.platform.startswith("linux") else False
    if raw_value is None:
        return default
    if isinstance(raw_value, bool):
        return raw_value

    normalized = str(raw_value).strip().lower()
    if not normalized:
        return default
    if normalized == "virtual":
        if sys.platform.startswith("linux"):
            return "virtual"
        logger.warning("HEADLESS=virtual is only supported on Linux; using headed mode")
        return False
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False

    logger.warning("Unsupported HEADLESS={!r}, using default mode={!r}", raw_value, default)
    return default


def _browser_proxy_options() -> dict[str, str] | None:
    if settings.BROWSER_PROXY is None:
        return None

    proxy_url = settings.BROWSER_PROXY.get_secret_value().strip()
    if not proxy_url:
        return None

    parsed = urlsplit(proxy_url)
    try:
        port = parsed.port
    except ValueError as err:
        raise ValueError("BROWSER_PROXY contains an invalid port") from err

    if (
        parsed.scheme.lower() not in _PROXY_SCHEMES
        or not parsed.hostname
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError(
            "BROWSER_PROXY must be an http://, https://, socks4://, or socks5:// proxy URL"
        )

    hostname = parsed.hostname
    if ":" in hostname:
        hostname = f"[{hostname}]"
    server = f"{parsed.scheme.lower()}://{hostname}"
    if port is not None:
        server = f"{server}:{port}"

    proxy = {"server": server}
    if parsed.username is not None:
        proxy["username"] = unquote(parsed.username)
    if parsed.password is not None:
        proxy["password"] = unquote(parsed.password)
    return proxy


def _camoufox_launch_options(headless: bool | str, proxy: dict[str, str] | None) -> dict:
    from browserforge.fingerprints import Screen

    screen = Screen(max_width=1920, max_height=1080, min_height=1080, min_width=1920)
    firefox_user_prefs = {"network.dns.disableIPv6": True, "network.trr.mode": 5}
    if proxy is None:
        firefox_user_prefs["network.proxy.type"] = 0

    options = {
        "persistent_context": True,
        "user_data_dir": settings.user_data_dir_for("camoufox"),
        "screen": screen,
        "record_video_dir": RECORD_DIR,
        "record_video_size": _VIEWPORT,
        "firefox_user_prefs": firefox_user_prefs,
        "humanize": 0.2,
        "headless": headless,
    }
    if proxy is not None:
        options["proxy"] = proxy
        options["geoip"] = True
    return options


def _playwright_launch_options(
    headless: bool | str, proxy: dict[str, str] | None, *, display: str | None = None
) -> dict:
    options = {
        "user_data_dir": str(settings.user_data_dir_for("playwright")),
        "headless": False if headless == "virtual" else bool(headless),
        "viewport": _VIEWPORT,
        "record_video_dir": str(RECORD_DIR),
        "record_video_size": _VIEWPORT,
    }
    if proxy is not None:
        options["proxy"] = proxy
    if display is not None:
        options["env"] = {**os.environ, "DISPLAY": display}
    return options


def _is_camoufox_bootstrap_error(err: Exception) -> bool:
    message = str(err).lower()
    if isinstance(err, HTTPError):
        return "api.github.com/repos/daijro/camoufox/releases" in message
    if isinstance(err, RequestException):
        return "camoufox" in message or "api.github.com" in message
    return any(
        marker in message
        for marker in (
            "camoufox is not installed",
            "api.github.com/repos/daijro/camoufox/releases",
            "rate limit exceeded",
            "profile was last used with a newer version",
            "browsertype.launch_persistent_context: target page, context or browser has been closed",
        )
    )


async def _install_hsw_identity_route(context: BrowserContext) -> None:
    async def force_identity_encoding(route: Route) -> None:
        headers = await route.request.all_headers()
        headers["accept-encoding"] = "identity"
        await route.continue_(headers=headers)

    # Camoufox/Firefox can fail while decoding hCaptcha's compressed hsw.js response.
    # Keep the workaround scoped to that script instead of changing all browser traffic.
    await context.route("**/hsw.js*", force_identity_encoding)


@asynccontextmanager
async def open_browser_context(headless: bool | str) -> AsyncIterator[BrowserContext]:
    backend = (settings.BROWSER_BACKEND or "auto").strip().lower()
    headless = resolve_headless_mode(headless)
    proxy = _browser_proxy_options()
    if backend not in {"auto", "camoufox", "playwright"}:
        logger.warning("Unsupported BROWSER_BACKEND={!r}, falling back to auto", backend)
        backend = "auto"

    if backend in {"auto", "camoufox"}:
        try:
            from camoufox import AsyncCamoufox

            camoufox_headless = (
                False if headless == "virtual" and os.getenv("DISPLAY") else headless
            )
            camoufox = AsyncCamoufox(**_camoufox_launch_options(camoufox_headless, proxy))
            browser = await camoufox.__aenter__()
        except Exception as err:
            if backend == "camoufox" or not _is_camoufox_bootstrap_error(err):
                raise
            logger.error(
                "Browser backend degraded | from=camoufox | to=playwright-firefox | "
                "headless_mode={} | proxy_enabled={} | reason={}",
                headless,
                proxy is not None,
                type(err).__name__,
            )
        else:
            await _install_hsw_identity_route(browser)
            logger.info(
                "Browser backend active | backend=camoufox | headless_mode={} | proxy_enabled={}",
                headless,
                proxy is not None,
            )
            try:
                yield browser
                return
            finally:
                with suppress(Exception):
                    await camoufox.__aexit__(None, None, None)

    virtual_display = None
    display = os.getenv("DISPLAY")
    if headless == "virtual" and not display:
        from camoufox.virtdisplay import VirtualDisplay

        virtual_display = VirtualDisplay()
        display = virtual_display.get()

    try:
        async with async_playwright() as playwright:
            browser = await playwright.firefox.launch_persistent_context(
                **_playwright_launch_options(headless, proxy, display=display)
            )
            await _install_hsw_identity_route(browser)
            logger.warning(
                "Browser backend active | backend=playwright-firefox | "
                "headless_mode={} | proxy_enabled={}",
                headless,
                proxy is not None,
            )
            try:
                yield browser
            finally:
                with suppress(Exception):
                    await browser.close()
    finally:
        if virtual_display is not None:
            virtual_display.kill()
