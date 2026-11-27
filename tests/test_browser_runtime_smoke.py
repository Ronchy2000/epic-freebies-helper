"""Opt-in real-browser smoke checks with local content and disposable profiles."""

import asyncio
import os

import pytest

import services.browser_context as browser_context
import settings as settings_module
from services.epic_games_service import EpicGames

pytestmark = pytest.mark.skipif(
    os.getenv("EPIC_BROWSER_SMOKE") != "1",
    reason="Set EPIC_BROWSER_SMOKE=1 after installing the browser binaries",
)


@pytest.mark.parametrize("backend", ["playwright", "camoufox"])
def test_real_browser_survives_checkout_frame_replacement(monkeypatch, tmp_path, backend):
    monkeypatch.setattr(settings_module, "USER_DATA_DIR", tmp_path / "profiles")
    monkeypatch.setattr(settings_module.settings, "EPIC_EMAIL", "smoke@example.test")
    monkeypatch.setattr(settings_module.settings, "BROWSER_BACKEND", backend)
    monkeypatch.setattr(settings_module.settings, "BROWSER_PROXY", None)
    monkeypatch.setattr(browser_context, "RECORD_DIR", tmp_path / "recordings")

    async def scenario():
        async with browser_context.open_browser_context(headless=True) as context:
            page = await context.new_page()
            await page.set_content("<h1>Checkout host</h1>")
            await page.evaluate(
                """async () => {
                    for (let i = 0; i < 50; i++) {
                        const frame = document.createElement('iframe');
                        frame.srcdoc = '<button>Add to library</button>';
                        document.body.appendChild(frame);
                        await new Promise(resolve => setTimeout(resolve, 10));
                        frame.srcdoc = '<p>Checkout replaced</p>';
                        frame.remove();
                    }
                    const checkout = document.createElement('iframe');
                    checkout.id = 'webPurchaseContainer';
                    checkout.srcdoc = '<button>Add to library</button>';
                    document.body.appendChild(checkout);
                }"""
            )
            checkout = page.frame_locator("#webPurchaseContainer")
            await checkout.get_by_role("button", name="Add to library").wait_for(timeout=10000)
            assert await page.locator("h1").inner_text() == "Checkout host"
            assert await EpicGames._has_purchase_progress(page, "https://example.test/game")
            await checkout.get_by_role("button", name="Add to library").click(timeout=5000)
            await page.goto("data:text/html,<h1>Driver still connected</h1>")
            assert await page.locator("h1").inner_text() == "Driver still connected"

    asyncio.run(scenario())
