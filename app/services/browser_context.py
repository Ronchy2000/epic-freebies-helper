# -*- coding: utf-8 -*-
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from browserforge.fingerprints import Screen
from camoufox import AsyncCamoufox
from loguru import logger
from playwright.async_api import BrowserContext, ViewportSize, async_playwright
from requests import HTTPError, RequestException

from settings import RECORD_DIR, settings

_SCREEN = Screen(max_width=1920, max_height=1080, min_height=1080, min_width=1920)
_VIEWPORT = ViewportSize(width=1920, height=1080)


def _camoufox_launch_options(headless: bool | str) -> dict:
    return {
        "persistent_context": True,
        "user_data_dir": settings.user_data_dir_for("camoufox"),
        "screen": _SCREEN,
        "record_video_dir": RECORD_DIR,
        "record_video_size": _VIEWPORT,
        "humanize": 0.2,
        "headless": headless,
    }


def _playwright_launch_options(headless: bool | str) -> dict:
    return {
        "user_data_dir": str(settings.user_data_dir_for("playwright")),
        "headless": True if headless == "virtual" else bool(headless),
        "viewport": _VIEWPORT,
        "record_video_dir": str(RECORD_DIR),
        "record_video_size": _VIEWPORT,
    }


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


@asynccontextmanager
async def open_browser_context(headless: bool | str) -> AsyncIterator[BrowserContext]:
    backend = (settings.BROWSER_BACKEND or "auto").strip().lower()
    if backend not in {"auto", "camoufox", "playwright"}:
        logger.warning("Unsupported BROWSER_BACKEND=%r, falling back to auto", backend)
        backend = "auto"

    if backend in {"auto", "camoufox"}:
        try:
            async with AsyncCamoufox(**_camoufox_launch_options(headless)) as browser:
                yield browser
                return
        except Exception as err:
            if backend == "camoufox" or not _is_camoufox_bootstrap_error(err):
                raise
            logger.warning(
                "Camoufox bootstrap failed, falling back to Playwright Firefox. err={}",
                err,
            )

    async with async_playwright() as playwright:
        browser = await playwright.firefox.launch_persistent_context(
            **_playwright_launch_options(headless)
        )
        try:
            yield browser
        finally:
            try:
                await browser.close()
            except Exception:
                pass
