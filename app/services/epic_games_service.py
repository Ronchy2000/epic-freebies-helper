# -*- coding: utf-8 -*-
# Time       : 2022/1/16 0:25
# Author     : QIN2DIM
# GitHub     : https://github.com/QIN2DIM
# Description: 游戏商城控制句柄

import json
import time
from contextlib import suppress
from json import JSONDecodeError
from typing import List

import httpx
from hcaptcha_challenger.agent import AgentV
from loguru import logger
from playwright.async_api import Page
from playwright.async_api import expect, TimeoutError, FrameLocator
from tenacity import retry, retry_if_exception_type, stop_after_attempt

from models import OrderItem, Order
from models import PromotionGame
from settings import settings, RUNTIME_DIR

URL_CLAIM = "https://store.epicgames.com/en-US/free-games"
URL_LOGIN = (
    f"https://www.epicgames.com/id/login?lang=en-US&noHostRedirect=true&redirectUrl={URL_CLAIM}"
)
URL_CART = "https://store.epicgames.com/en-US/cart"
URL_CART_SUCCESS = "https://store.epicgames.com/en-US/cart/success"


URL_PROMOTIONS = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions"
URL_PRODUCT_PAGE = "https://store.epicgames.com/en-US/p/"
URL_PRODUCT_BUNDLES = "https://store.epicgames.com/en-US/bundles/"


def get_promotions() -> List[PromotionGame]:
    """获取周免游戏数据"""
    def is_discount_game(prot: dict) -> bool | None:
        with suppress(KeyError, IndexError, TypeError):
            offers = prot["promotions"]["promotionalOffers"][0]["promotionalOffers"]
            for i, offer in enumerate(offers):
                if offer["discountSetting"]["discountPercentage"] == 0:
                    return True

    promotions: List[PromotionGame] = []

    resp = httpx.get(URL_PROMOTIONS, params={"local": "zh-CN"})

    try:
        data = resp.json()
    except JSONDecodeError as err:
        logger.error("Failed to get promotions", err=err)
        return []

    with suppress(Exception):
        cache_key = RUNTIME_DIR.joinpath("promotions.json")
        cache_key.parent.mkdir(parents=True, exist_ok=True)
        cache_key.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    # Get store promotion data and <this week free> games
    for e in data["data"]["Catalog"]["searchStore"]["elements"]:
        if not is_discount_game(e):
            continue

        # -----------------------------------------------------------
        # 🟢 智能 URL 识别逻辑
        # -----------------------------------------------------------
        is_bundle = False
        if e.get("offerType") == "BUNDLE":
            is_bundle = True
        
        # 补充检测：分类和标题
        if not is_bundle:
            for cat in e.get("categories", []):
                if "bundle" in cat.get("path", "").lower():
                    is_bundle = True
                    break
        if not is_bundle and "Collection" in e.get("title", ""):
             is_bundle = True

        base_url = URL_PRODUCT_BUNDLES if is_bundle else URL_PRODUCT_PAGE

        try:
            if e.get('offerMappings'):
                slug = e['offerMappings'][0]['pageSlug']
                e["url"] = f"{base_url.rstrip('/')}/{slug}"
            elif e.get("productSlug"):
                e["url"] = f"{base_url.rstrip('/')}/{e['productSlug']}"
            else:
                 e["url"] = f"{base_url.rstrip('/')}/{e.get('urlSlug', 'unknown')}"
        except (KeyError, IndexError):
            logger.info(f"Failed to get URL: {e}")
            continue

        logger.info(e["url"])
        promotions.append(PromotionGame(**e))

    return promotions


class EpicAgent:
    def __init__(self, page: Page):
        self.page = page
        self.epic_games = EpicGames(self.page)
        self._promotions: List[PromotionGame] = []
        self._ctx_cookies_is_available: bool = False
        self._orders: List[OrderItem] = []
        self._namespaces: List[str] = []
        self._cookies = None

    async def _sync_order_history(self):
        if self._orders:
            return
        completed_orders: List[OrderItem] = []
        try:
            await self.page.goto("https://www.epicgames.com/account/v2/payment/ajaxGetOrderHistory")
            text_content = await self.page.text_content("//pre")
            data = json.loads(text_content)
            for _order in data["orders"]:
                order = Order(**_order)
                if order.orderType != "PURCHASE":
                    continue
                for item in order.items:
                    if not item.namespace or len(item.namespace) != 32:
                        continue
                    completed_orders.append(item)
        except Exception as err:
            logger.warning(err)
        self._orders = completed_orders

    async def _check_orders(self):
        await self._sync_order_history()
        self._namespaces = self._namespaces or [order.namespace for order in self._orders]
        self._promotions = [p for p in get_promotions() if p.namespace not in self._namespaces]

    async def _should_ignore_task(self) -> bool:
        self._ctx_cookies_is_available = False
        await self.page.goto(URL_CLAIM, wait_until="domcontentloaded")
        status = await self.page.locator("//egs-navigation").get_attribute("isloggedin")
        if status == "false":
            logger.error("❌ context cookies is not available")
            return False
        self._ctx_cookies_is_available = True
        await self._check_orders()
        if not self._promotions:
            return True
        return False

    async def collect_epic_games(self):
        if await self._should_ignore_task():
            logger.success("All week-free games are already in the library")
            return

        if not self._ctx_cookies_is_available:
            return

        if not self._promotions:
            await self._check_orders()

        if not self._promotions:
            logger.success("All week-free games are already in the library")
            return

        for p in self._promotions:
            pj = json.dumps({"title": p.title, "url": p.url}, indent=2, ensure_ascii=False)
            logger.debug(f"Discover promotion \n{pj}")

        if self._promotions:
            try:
                await self.epic_games.collect_weekly_games(self._promotions)
            except Exception as e:
                logger.exception(e)
        
        logger.debug("All tasks in the workflow have been completed")


class EpicGames:
    def __init__(self, page: Page):
        self.page = page
        self._promotions: List[PromotionGame] = []

    @staticmethod
    async def _page_text(page: Page) -> str:
        body_text = await page.locator("body").text_content() or ""
        return " ".join(body_text.upper().split())

    @staticmethod
    async def _purchase_button_text(page: Page) -> str:
        purchase_btn = page.locator("//button[@data-testid='purchase-cta-button']").first
        with suppress(Exception):
            if await purchase_btn.is_visible(timeout=500):
                return ((await purchase_btn.text_content()) or "").strip().upper()
        return ""

    @staticmethod
    async def _click_visible_continue_button(page: Page) -> bool:
        candidates = [
            page.get_by_role("button", name="Continue"),
            page.locator(
                "//button[normalize-space(.)='Continue' or .//span[normalize-space(.)='Continue']]"
            ),
        ]

        for locator in candidates:
            with suppress(Exception):
                count = await locator.count()
                for index in range(count - 1, -1, -1):
                    button = locator.nth(index)
                    if not await button.is_visible(timeout=250):
                        continue
                    try:
                        await button.click(timeout=2000, force=True)
                        return True
                    except Exception:
                        with suppress(Exception):
                            await button.evaluate("(element) => element.click()")
                            return True

        with suppress(Exception):
            clicked = await page.evaluate(
                """
                () => {
                  const isVisible = (element) => {
                    const rect = element.getBoundingClientRect();
                    const style = window.getComputedStyle(element);
                    return rect.width > 0 && rect.height > 0 &&
                      style.visibility !== 'hidden' &&
                      style.display !== 'none';
                  };

                  const candidates = Array.from(document.querySelectorAll('button'))
                    .filter((button) => (button.innerText || '').trim() === 'Continue')
                    .filter(isVisible);

                  const button = candidates.at(-1);
                  if (!button) {
                    return false;
                  }

                  button.click();
                  return true;
                }
                """
            )
            if clicked:
                return True

        return False

    @staticmethod
    async def _is_claimed_state(page: Page, url: str) -> bool:
        button_claim_markers = [
            "IN LIBRARY",
            "OWNED",
            "IN YOUR LIBRARY",
            "ALREADY OWNED",
            "VIEW IN LIBRARY",
            "GO TO LIBRARY",
        ]
        page_claim_markers = [
            "THANK YOU FOR YOUR ORDER",
            "ORDER CONFIRMED",
            "IN YOUR LIBRARY",
            "VIEW IN LIBRARY",
            "GO TO LIBRARY",
        ]

        if URL_CART_SUCCESS in page.url:
            logger.success(f"Claim success inferred from cart success URL - {url=}")
            return True

        page_text = await EpicGames._page_text(page)
        button_text = await EpicGames._purchase_button_text(page)

        for marker in button_claim_markers:
            if marker in button_text:
                logger.success(
                    f"Claim success inferred from purchase button marker '{marker}' - {url=}"
                )
                return True

        for marker in page_claim_markers:
            if marker in page_text:
                logger.success(f"Claim success inferred from page text marker '{marker}' - {url=}")
                return True

        if "GET" == button_text and "DEVICE NOT SUPPORTED" in page_text:
            logger.warning(f"Page still shows Get and device modal text; claim is not complete - {url=}")

        return False

    @staticmethod
    async def _capture_purchase_debug(page: Page, reason: str, url: str):
        stamp = int(time.time())
        target = RUNTIME_DIR.joinpath("purchase_debug")
        target.mkdir(parents=True, exist_ok=True)
        safe_reason = reason.lower().replace(" ", "_")
        await page.screenshot(path=target.joinpath(f"{safe_reason}-{stamp}.png"), full_page=True)
        with suppress(Exception):
            page_text = await page.locator("body").text_content()
            target.joinpath(f"{safe_reason}-{stamp}.txt").write_text(
                f"URL: {page.url}\nSOURCE_URL: {url}\n\n{page_text or ''}",
                encoding="utf-8",
            )
        logger.info(f"Saved purchase debug screenshot - reason={reason} url={url}")

    @staticmethod
    async def _handle_device_not_supported_modal(page: Page, url: str, timeout_ms: int = 8000) -> bool:
        elapsed = 0
        captured = False

        while elapsed < timeout_ms:
            try:
                body_text = await EpicGames._page_text(page)
            except Exception:
                body_text = ""

            if "DEVICE NOT SUPPORTED" in body_text:
                logger.warning(f"Device not supported modal detected - attempting to continue. {url=}")
                if not captured:
                    await EpicGames._capture_purchase_debug(page, "device_not_supported", url)
                    captured = True

                try:
                    if await EpicGames._click_visible_continue_button(page):
                        await page.wait_for_timeout(2000)
                        if "DEVICE NOT SUPPORTED" not in await EpicGames._page_text(page):
                            logger.success("Dismissed device not supported modal")
                            return True

                        logger.warning("Device not supported modal is still visible after clicking Continue")
                    else:
                        logger.debug("Device modal is visible but its Continue button is not clickable yet")
                except Exception as err:
                    logger.warning(f"Failed to dismiss device not supported modal: {err}")
                    await EpicGames._capture_purchase_debug(
                        page, "device_not_supported_click_failed", url
                    )

            await page.wait_for_timeout(500)
            elapsed += 500

        if captured:
            logger.warning(f"Device not supported modal did not clear before timeout - {url=}")
            await EpicGames._capture_purchase_debug(page, "device_not_supported_timeout", url)

        return False

    @staticmethod
    async def _log_purchase_button_context(page: Page, purchase_btn, url: str):
        btn_text = (await purchase_btn.text_content() or "").strip()
        disabled = await purchase_btn.get_attribute("disabled")
        aria_disabled = await purchase_btn.get_attribute("aria-disabled")
        btn_class = await purchase_btn.get_attribute("class")
        btn_testid = await purchase_btn.get_attribute("data-testid")
        container_text = ""

        with suppress(Exception):
            container = purchase_btn.locator("xpath=ancestor::*[self::section or self::aside or self::div][1]")
            container_text = (await container.text_content() or "").strip()
            container_text = " ".join(container_text.split())[:800]

        logger.debug(
            "Purchase button context | url={} | text='{}' | disabled={} | aria-disabled={} | testid={} | class={} | container='{}'",
            url,
            btn_text,
            disabled,
            aria_disabled,
            btn_testid,
            btn_class,
            container_text,
        )
        return btn_text, container_text, disabled, aria_disabled

    @staticmethod
    async def _agree_license(page: Page):
        logger.debug("Agree license")
        with suppress(TimeoutError):
            await page.click("//label[@for='agree']", timeout=4000)
            accept = page.locator("//button//span[text()='Accept']")
            if await accept.is_enabled():
                await accept.click()

    @staticmethod
    async def _active_purchase_container(
        page: Page, place_order_timeout: int = 15000, confirm_timeout: int = 5000
    ):
        logger.debug("Scanning for purchase iframe...")
        iframe_selector = "//iframe[contains(@id, 'webPurchaseContainer') or contains(@src, 'purchase')]"
        wpc = page.frame_locator(iframe_selector).first

        logger.debug("Looking for 'PLACE ORDER' button...")
        place_order_btn = wpc.locator("button", has_text="PLACE ORDER")
        confirm_btn = wpc.locator("//button[contains(@class, 'payment-confirm__btn')]")
        
        try:
            await expect(place_order_btn).to_be_visible(timeout=place_order_timeout)
            logger.debug("✅ Found 'PLACE ORDER' button via text match")
            return wpc, place_order_btn
        except AssertionError:
            pass
            
        try:
            await expect(confirm_btn).to_be_visible(timeout=confirm_timeout)
            logger.debug("✅ Found button via CSS class match")
            return wpc, confirm_btn
        except AssertionError:
            logger.warning("Primary buttons not found in iframe.")
            raise AssertionError("Could not find Place Order button in iframe")

    @staticmethod
    async def _uk_confirm_order(wpc: FrameLocator):
        logger.debug("UK confirm order")
        with suppress(TimeoutError):
            accept = wpc.locator("//button[contains(@class, 'payment-confirm__btn')]")
            if await accept.is_enabled(timeout=5000):
                await accept.click()
                return True

    async def _wait_for_purchase_state(self, page: Page, url: str, timeout_ms: int = 20000):
        elapsed = 0

        while elapsed < timeout_ms:
            await self._handle_device_not_supported_modal(page, url, timeout_ms=1000)

            if await self._is_claimed_state(page, url):
                return "claimed", None

            try:
                return "checkout", await self._active_purchase_container(
                    page, place_order_timeout=1000, confirm_timeout=1000
                )
            except AssertionError:
                pass

            await page.wait_for_timeout(500)
            elapsed += 1500

        return "pending", None

    @staticmethod
    async def _is_checkout_security_check_visible(page: Page) -> bool:
        markers = [
            "ONE MORE STEP",
            "PLEASE COMPLETE A SECURITY CHECK TO CONTINUE",
            "PLEASE DRAG THE ICON ON THE BOTTOM TO THE PLACE WHERE IT FITS",
            "SKIP",
        ]
        page_text = await EpicGames._page_text(page)
        return any(marker in page_text for marker in markers)

    async def _resolve_checkout_security_check(
        self, page: Page, agent: AgentV, url: str, max_attempts: int = 3
    ) -> bool:
        if not await self._is_checkout_security_check_visible(page):
            return True

        logger.warning(f"Checkout security check detected - starting solve loop. {url=}")

        for attempt in range(1, max_attempts + 1):
            if not await self._is_checkout_security_check_visible(page):
                logger.success(f"Checkout security check cleared before solve attempt {attempt} - {url=}")
                return True

            logger.info(f"Solving checkout security check ({attempt}/{max_attempts})")
            await self._capture_purchase_debug(page, f"checkout_security_check_attempt_{attempt}", url)

            try:
                await agent.wait_for_challenge()
            except Exception as err:
                logger.warning(f"Checkout security check solve attempt failed ({attempt}/{max_attempts}): {err}")
                await self._capture_purchase_debug(
                    page, f"checkout_security_check_failed_{attempt}", url
                )

            await page.wait_for_timeout(1500)

            if not await self._is_checkout_security_check_visible(page):
                logger.success(f"Checkout security check solved successfully - {url=}")
                return True

        logger.warning(f"Checkout security check remained visible after retries - {url=}")
        await self._capture_purchase_debug(page, "checkout_security_check_unresolved", url)
        return False

    async def _handle_instant_checkout(self, page: Page, url: str) -> bool:
        logger.info("🚀 Triggering Instant Checkout Flow...")
        agent = AgentV(page=page, agent_config=settings)

        try:
            state, payload = await self._wait_for_purchase_state(page, url, timeout_ms=25000)
            if state == "claimed":
                logger.success(f"🎉 Instant checkout resolved to claimed state - {url=}")
                return True

            if state != "checkout" or payload is None:
                logger.warning(f"Instant checkout never reached a checkout container - {url=}")
                await self._capture_purchase_debug(page, "instant_checkout_not_reached", url)
                return False

            wpc, payment_btn = payload
            logger.debug(f"Clicking payment button: {await payment_btn.text_content()}")
            await payment_btn.click(force=True)
            await page.wait_for_timeout(3000)

            if await self._is_checkout_security_check_visible(page):
                if not await self._resolve_checkout_security_check(page, agent, url):
                    return False
            else:
                logger.debug("No checkout security check detected after Place Order")

            for _ in range(2):
                await self._handle_device_not_supported_modal(page, url, timeout_ms=3000)

                if await self._is_checkout_security_check_visible(page):
                    if not await self._resolve_checkout_security_check(page, agent, url):
                        return False

                if await self._is_claimed_state(page, url):
                    logger.success(f"🎉 Instant checkout confirmed claim state - {url=}")
                    return True

                with suppress(Exception):
                    if await payment_btn.is_visible(timeout=1000):
                        await payment_btn.click(force=True)
                        await page.wait_for_timeout(2000)

                state, _ = await self._wait_for_purchase_state(page, url, timeout_ms=10000)
                if state == "claimed":
                    logger.success(f"🎉 Instant checkout confirmed claim state after retry - {url=}")
                    return True
                if state != "checkout":
                    break

            logger.warning(f"Instant checkout ended without a confirmed claim state - {url=}")
            await self._capture_purchase_debug(page, "instant_checkout_unconfirmed", url)
            return False

        except Exception as err:
            logger.warning(f"Instant checkout warning: {err}")
            await self._capture_purchase_debug(page, "instant_checkout_warning", url)
            with suppress(Exception):
                logger.debug(f"Instant checkout fallback | current_url={page.url}")
            await self._handle_device_not_supported_modal(page, url, timeout_ms=5000)
            if await self._is_claimed_state(page, url):
                logger.success(f"🎉 Instant checkout recovered into claimed state - {url=}")
                return True
            try:
                await page.reload(timeout=10000)
            except Exception as reload_err:
                logger.warning(f"Page reload after instant checkout warning failed: {reload_err}")
                await self._capture_purchase_debug(page, "instant_checkout_reload_failed", url)

            if await self._is_claimed_state(page, url):
                logger.success(f"🎉 Instant checkout confirmed claim state after reload - {url=}")
                return True

            return False

    async def add_promotion_to_cart(self, page: Page, urls: List[str]) -> tuple[bool, int, List[str]]:
        has_pending_cart_items = False
        instant_claimed = 0
        failed_urls: List[str] = []
        owned_markers = [
            "IN LIBRARY",
            "OWNED",
            "ALREADY OWNED",
            "UNAVAILABLE",
            "COMING SOON",
            "IN YOUR LIBRARY",
            "OWN THIS GAME",
        ]

        for url in urls:
            await page.goto(url, wait_until="load")

            # 404 检测
            title = await page.title()
            if "404" in title or "Page Not Found" in title:
                logger.error(f"❌ Invalid URL (404 Page): {url}")
                continue

            # 处理年龄限制弹窗
            try:
                continue_btn = page.locator("//button//span[text()='Continue']")
                if await continue_btn.is_visible(timeout=5000):
                    await continue_btn.click()
            except Exception:
                pass 

            # ------------------------------------------------------------
            # 🔥 新思路：彻底解决按钮识别问题 (黑名单机制 + 智能点击)
            # ------------------------------------------------------------
            
            # 1. 尝试找到所有可能的“主按钮”
            # Epic 按钮通常有 'purchase-cta-button' 这个 TestID
            purchase_btn = page.locator("//button[@data-testid='purchase-cta-button']").first

            # 2. 如果没找到主按钮，尝试找“库中”状态
            try:
                if not await purchase_btn.is_visible(timeout=5000):
                    # 再次检查是否在库中 (有时按钮不叫 purchase-cta，而是简单的 disabled button)
                    all_text = (await page.locator("body").text_content() or "").upper()
                    if any(marker in all_text for marker in owned_markers):
                         logger.success(f"Already in the library (Page Text Scan) - {url=}")
                         continue
                    logger.warning(f"Could not find any purchase button - {url=}")
                    await self._capture_purchase_debug(page, "button_missing", url)
                    continue
            except Exception:
                pass

            # 3. 获取按钮上下文
            btn_text, container_text, disabled, aria_disabled = await self._log_purchase_button_context(
                page, purchase_btn, url
            )
            btn_text_upper = btn_text.upper()
            container_text_upper = container_text.upper()
            
            logger.debug(f"👉 Found Button: '{btn_text}'")

            # 4. 黑名单检查：只有这些情况绝对不能点
            # 如果是 'IN LIBRARY', 'OWNED', 'UNAVAILABLE', 'COMING SOON' -> 跳过
            if disabled is not None or aria_disabled == "true":
                logger.success(f"Purchase button disabled - Skipping. {url=}")
                await self._capture_purchase_debug(page, "button_disabled", url)
                continue

            if any(marker in btn_text_upper for marker in owned_markers) or any(
                marker in container_text_upper for marker in owned_markers
            ):
                logger.success(f"Game status is '{btn_text}' - Skipping.")
                continue

            # 5. 白名单检查 (Add to Cart 特殊处理)
            # 如果包含 'CART'，说明是加入购物车流程
            if "CART" in btn_text_upper:
                logger.debug(f"🛒 Logic: Add To Cart - {url=}")
                await purchase_btn.click()
                has_pending_cart_items = True
                continue
            
            # 6. 默认处理 (盲点逻辑)
            # 只要不是黑名单，也不是购物车，统统当做 "Get/Purchase" 直接点击！
            # 不管它写的是 'Get', 'Free', 'Purchase', 'Buy Now'，只要 API 说是免费的，我们就点！
            logger.debug(f"⚡️ Logic: Aggressive Click (Text: {btn_text}) - {url=}")
            try:
                await purchase_btn.click(timeout=10000)
                await self._handle_device_not_supported_modal(page, url)
            except TimeoutError:
                logger.warning(f"Standard click timed out, retrying with force click - {url=}")
                await self._capture_purchase_debug(page, "click_timeout", url)
                await purchase_btn.click(force=True, timeout=10000)
                await self._handle_device_not_supported_modal(page, url)
            except Exception:
                await self._capture_purchase_debug(page, "click_failed", url)
                raise
            
            # 点击后，转入即时结账流程
            if await self._handle_instant_checkout(page, url):
                instant_claimed += 1
            else:
                failed_urls.append(url)
            # ------------------------------------------------------------

        return has_pending_cart_items, instant_claimed, failed_urls

    async def _empty_cart(self, page: Page, wait_rerender: int = 30) -> bool | None:
        has_paid_free = False
        try:
            cards = await page.query_selector_all("//div[@data-testid='offer-card-layout-wrapper']")
            for card in cards:
                is_free = await card.query_selector("//span[text()='Free']")
                if not is_free:
                    has_paid_free = True
                    wishlist_btn = await card.query_selector(
                        "//button//span[text()='Move to wishlist']"
                    )
                    await wishlist_btn.click()

            if has_paid_free and wait_rerender:
                wait_rerender -= 1
                await page.wait_for_timeout(2000)
                return await self._empty_cart(page, wait_rerender)
            return True
        except TimeoutError as err:
            logger.warning("Failed to empty shopping cart", err=err)
            return False

    async def _purchase_free_game(self):
        await self.page.goto(URL_CART, wait_until="domcontentloaded")
        logger.debug("Move ALL paid games from the shopping cart out")
        await self._empty_cart(self.page)

        agent = AgentV(page=self.page, agent_config=settings)
        await self.page.click("//button//span[text()='Check Out']")
        await self._agree_license(self.page)

        try:
            logger.debug("Move to webPurchaseContainer iframe")
            wpc, payment_btn = await self._active_purchase_container(self.page)
            logger.debug("Click payment button")
            await self._uk_confirm_order(wpc)
            await agent.wait_for_challenge()
        except Exception as err:
            logger.warning(f"Failed to solve captcha - {err}")
            await self.page.reload()
            return await self._purchase_free_game()

    @retry(retry=retry_if_exception_type(TimeoutError), stop=stop_after_attempt(2), reraise=True)
    async def collect_weekly_games(self, promotions: List[PromotionGame]):
        urls = [p.url for p in promotions]
        has_cart_items, instant_claimed, failed_urls = await self.add_promotion_to_cart(self.page, urls)
        cart_claimed = False

        if has_cart_items:
            await self._purchase_free_game()
            try:
                await self.page.wait_for_url(URL_CART_SUCCESS)
                logger.success("🎉 Successfully collected cart games")
                cart_claimed = True
            except TimeoutError:
                logger.warning("Failed to collect cart games")

        if failed_urls:
            raise RuntimeError(
                "Failed to confirm claim flow for promotions: " + ", ".join(failed_urls)
            )

        if has_cart_items and not cart_claimed:
            raise RuntimeError("Failed to confirm cart checkout success")

        if instant_claimed:
            logger.success(f"🎉 Confirmed {instant_claimed} instant claim(s)")
        elif not has_cart_items:
            logger.success("🎉 Process completed (No cart items pending)")
