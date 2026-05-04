# -*- coding: utf-8 -*-
"""
@Time    : 2025/7/16 21:57
@Author  : QIN2DIM
@GitHub  : https://github.com/QIN2DIM
@Desc    :
"""
import asyncio
import sys
from contextlib import suppress
from typing import List

from playwright.async_api import Page

from services.epic_authorization_service import EpicAuthorization
from services.browser_context import open_browser_context
from services.epic_games_service import EpicAgent
from settings import LOG_DIR
from utils import init_log
from extensions.ext_celery import ext_celery_app

init_log(
    runtime=LOG_DIR.joinpath("runtime.log"),
    error=LOG_DIR.joinpath("error.log"),
    serialize=LOG_DIR.joinpath("serialize.log"),
)


async def add_games_to_cart(page: Page, urls: List[str] | None = None):
    """
    检测点功能，在登录后，控制前往指定站点点击 Add To Cart 操作
    Args:
        page:
        urls:

    Returns:

    """
    agent = EpicAgent(page)

    urls = urls or [
        "https://store.epicgames.com/en-US/p/bloompunk-2fd3fd",
        "https://store.epicgames.com/en-US/p/fall-guys",
        "https://store.epicgames.com/en-US/p/lords-of-the-fallen-2-lords-of-the-fallen-free-coop-mode-81b41f",
        "https://store.epicgames.com/en-US/p/once-upon-a-puppet-08ad66",
    ]
    await agent.epic_games.add_promotion_to_cart(page, urls=urls)
    await page.goto("https://store.epicgames.com/en-US/cart", wait_until="networkidle")
    await page.wait_for_timeout(5000)


async def collect_games(page: Page):
    """
    采集周免游戏
    Args:
        page:

    Returns:

    """
    agent = EpicAgent(page)
    await agent.collect_epic_games()


async def authorize(page: Page):
    agent = EpicAuthorization(page)
    await agent.invoke()


@ext_celery_app.task(queue="epic-freebies-helper")
async def collect_epic_games_task():
    headless = "virtual" if "linux" in sys.platform else False

    async with open_browser_context(headless=headless) as browser:
        page = browser.pages[0] if browser.pages else await browser.new_page()

        agent = EpicAuthorization(page)
        await agent.invoke()

        game_page = await browser.new_page()
        agent = EpicAgent(game_page)
        await agent.collect_epic_games()

        with suppress(Exception):
            for p in browser.pages:
                await p.close()

        with suppress(Exception):
            await browser.close()


if __name__ == '__main__':
    asyncio.run(collect_epic_games_task())
