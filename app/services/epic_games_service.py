# -*- coding: utf-8 -*-
# Time       : 2022/1/16 0:25
# Author     : QIN2DIM
# GitHub     : https://github.com/QIN2DIM
# Description: 游戏商城控制句柄

import asyncio
import json
import time
from contextlib import suppress
from json import JSONDecodeError
from typing import List

import httpx
from hcaptcha_challenger.agent import AgentV
from loguru import logger
from playwright.async_api import Frame, Page
from playwright.async_api import expect, TimeoutError, FrameLocator
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
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
PURCHASE_IFRAME_SELECTOR = (
    "//iframe[contains(@id, 'webPurchaseContainer') or contains(@src, 'purchase')]"
)
PurchaseContainer = FrameLocator | Frame | Page


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

    def _needs_privacy_policy_correction(self) -> bool:
        return "/id/login/correction/privacy-policy" in self.page.url

    async def _get_login_status(self) -> str | None:
        if self._needs_privacy_policy_correction():
            return None

        try:
            return await self.page.locator("//egs-navigation").get_attribute("isloggedin")
        except PlaywrightTimeoutError:
            logger.warning(
                "Timed out while waiting for //egs-navigation on claim page | current_url='{}'",
                self.page.url,
            )
            return None

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
        all_promotions = get_promotions()
        claimed_promotions = [p for p in all_promotions if p.namespace in self._namespaces]
        self._promotions = [p for p in all_promotions if p.namespace not in self._namespaces]

        for promotion in claimed_promotions:
            logger.success(
                f"Game already claimed previously - title='{promotion.title}' url='{promotion.url}'"
            )

    async def _should_ignore_task(self) -> bool:
        self._ctx_cookies_is_available = False
        await self.page.goto(URL_CLAIM, wait_until="domcontentloaded")

        if self._needs_privacy_policy_correction():
            raise RuntimeError(
                "Epic account requires a manual privacy-policy confirmation. "
                "Please sign in once in a normal browser, complete the confirmation page, "
                "and rerun the workflow."
            )

        status = await self._get_login_status()
        if status == "false":
            logger.error("❌ context cookies is not available")
            return False
        if status is None:
            raise RuntimeError(
                f"Could not determine Epic login state because //egs-navigation did not appear. "
                f"current_url={self.page.url}"
            )
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
            raise RuntimeError("Epic Games session cookies are unavailable after authentication")

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
                raise

        logger.debug("All tasks in the workflow have been completed")


class EpicGames:
    def __init__(self, page: Page):
        self.page = page
        self._promotions: List[PromotionGame] = []

    @staticmethod
    async def _locator_visible_text(locator, timeout: int | None = None) -> str:
        with suppress(Exception):
            options = {} if timeout is None else {"timeout": timeout}
            return " ".join(((await locator.inner_text(**options)) or "").upper().split())
        return ""

    @staticmethod
    async def _page_text(page: Page, timeout: int | None = None) -> str:
        return await EpicGames._locator_visible_text(page.locator("body"), timeout=timeout)

    @staticmethod
    async def _frame_texts(page: Page, timeout: int | None = None) -> list[str]:
        texts: list[str] = []
        options = {} if timeout is None else {"timeout": timeout}
        for frame in page.frames:
            with suppress(Exception):
                body = frame.locator("body")
                text = await body.inner_text(**options)
                if text:
                    texts.append(" ".join(text.upper().split()))
        return texts

    @staticmethod
    async def _combined_text(
        page: Page, timeout: int | None = None, frame_timeout: int | None = None
    ) -> str:
        chunks = [await EpicGames._page_text(page, timeout=timeout)]
        chunks.extend(
            await EpicGames._frame_texts(
                page, timeout=frame_timeout if frame_timeout is not None else timeout
            )
        )
        return "\n".join(filter(None, chunks))

    @staticmethod
    async def _purchase_button_text(page: Page) -> str:
        purchase_btn = page.locator("//button[@data-testid='purchase-cta-button']").first
        with suppress(Exception):
            if await purchase_btn.is_visible(timeout=500):
                return ((await purchase_btn.text_content()) or "").strip().upper()
        return ""

    @staticmethod
    async def _purchase_frame_text(page: Page) -> str:
        with suppress(Exception):
            purchase_frame_body = page.frame_locator(PURCHASE_IFRAME_SELECTOR).first.locator("body")
            frame_text = await purchase_frame_body.inner_text()
            if frame_text:
                return " ".join(frame_text.upper().split())
        return ""

    @staticmethod
    async def _visible_hcaptcha_frame_urls(
        page: Page, min_width: int = 160, min_height: int = 40
    ) -> list[str]:
        urls: list[str] = []

        for frame in page.frames:
            frame_url = (frame.url or "").lower()
            if "hcaptcha" not in frame_url:
                continue

            with suppress(Exception):
                frame_element = await frame.frame_element()
                frame_box = await frame_element.evaluate(
                    """
                    (element) => {
                      const rect = element.getBoundingClientRect();
                      const style = window.getComputedStyle(element);
                      return {
                        width: rect.width,
                        height: rect.height,
                        visible:
                          rect.width > 0 &&
                          rect.height > 0 &&
                          style.visibility !== 'hidden' &&
                          style.display !== 'none' &&
                          style.opacity !== '0'
                      };
                    }
                    """
                )
                if (
                    isinstance(frame_box, dict)
                    and frame_box.get("visible")
                    and frame_box.get("width", 0) >= min_width
                    and frame_box.get("height", 0) >= min_height
                ):
                    urls.append(frame.url)

        return urls

    @staticmethod
    async def _is_locator_visible(locator, timeout: int = 300) -> bool:
        with suppress(Exception):
            return await locator.first.is_visible(timeout=timeout)
        return False

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
    async def _claim_state_reason(page: Page, url: str) -> str | None:
        button_claim_markers = [
            "IN LIBRARY",
            "OWNED",
            "IN YOUR LIBRARY",
            "ALREADY OWNED",
            "VIEW IN LIBRARY",
            "GO TO LIBRARY",
        ]

        if URL_CART_SUCCESS in page.url:
            return "cart success URL"

        combined_text = await EpicGames._combined_text(page)
        button_text = await EpicGames._purchase_button_text(page)

        visible_order_confirmation = [
            page.get_by_text("Thanks for your order", exact=False),
            page.get_by_text("Thank you for your order", exact=False),
        ]
        visible_order_supporting = [
            page.get_by_text("Order number", exact=False),
            page.get_by_text("Ready to install your product", exact=False),
            page.get_by_text("Continue browsing", exact=False),
            page.get_by_text("Download launcher", exact=False),
        ]

        if any(
            [await EpicGames._is_locator_visible(locator) for locator in visible_order_confirmation]
        ) and any(
            [await EpicGames._is_locator_visible(locator) for locator in visible_order_supporting]
        ):
            return "visible checkout order confirmation modal"

        order_popup_markers = [
            ("THANK YOU FOR YOUR ORDER", "ORDER NUMBER"),
            ("THANK YOU FOR YOUR ORDER", "READY TO INSTALL YOUR PRODUCT"),
            ("THANKS FOR YOUR ORDER", "ORDER NUMBER"),
            ("THANKS FOR YOUR ORDER", "READY TO INSTALL YOUR PRODUCT"),
        ]
        page_claim_markers = [
            "ORDER CONFIRMED",
            "IN LIBRARY",
            "IN YOUR LIBRARY",
            "VIEW IN LIBRARY",
            "GO TO LIBRARY",
        ]

        for marker in button_claim_markers:
            if marker in button_text:
                return f"purchase button marker '{marker}'"

        for primary_marker, secondary_marker in order_popup_markers:
            if primary_marker in combined_text and secondary_marker in combined_text:
                return (
                    f"checkout order confirmation markers '{primary_marker}' + '{secondary_marker}'"
                )

        for marker in page_claim_markers:
            if marker in combined_text:
                return f"page/frame marker '{marker}'"

        if "GET" == button_text and "DEVICE NOT SUPPORTED" in combined_text:
            logger.warning(
                f"Page still shows Get and device modal text; claim is not complete - {url=}"
            )

        return None

    @staticmethod
    async def _is_claimed_state(page: Page, url: str) -> bool:
        reason = await EpicGames._claim_state_reason(page, url)
        if reason:
            logger.success(f"Game already claimed / in library ({reason}) - {url=}")
            return True

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
            frame_texts = await EpicGames._frame_texts(page)
            target.joinpath(f"{safe_reason}-{stamp}.txt").write_text(
                (
                    f"URL: {page.url}\nSOURCE_URL: {url}\n\n"
                    f"[MAIN PAGE]\n{page_text or ''}\n\n"
                    f"[FRAMES]\n" + "\n\n--- FRAME ---\n".join(frame_texts)
                ),
                encoding="utf-8",
            )
        logger.info(f"Saved purchase debug screenshot - reason={reason} url={url}")

    @staticmethod
    async def _goto_product_page(page: Page, url: str, title: str, attempts: int = 3) -> bool:
        for attempt in range(1, attempts + 1):
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=45000)
                with suppress(Exception):
                    await page.wait_for_load_state("networkidle", timeout=8000)
                return True
            except TimeoutError as err:
                logger.warning(
                    "Product page navigation timed out ({}/{}) - title='{}' url='{}' err={}",
                    attempt,
                    attempts,
                    title,
                    url,
                    err,
                )
                with suppress(Exception):
                    await page.evaluate("window.stop()")

                if url.rstrip("/") in page.url.rstrip("/"):
                    purchase_btn = page.locator(
                        "//button[@data-testid='purchase-cta-button']"
                    ).first
                    body_text = ""
                    with suppress(Exception):
                        body_text = await page.locator("body").text_content(timeout=2000) or ""
                    if await EpicGames._is_locator_visible(purchase_btn, timeout=1000) or body_text:
                        logger.warning(
                            "Continuing with partially loaded product page - title='{}' url='{}'",
                            title,
                            url,
                        )
                        return True

                if attempt < attempts:
                    await page.wait_for_timeout(2000 * attempt)
                    continue

        await EpicGames._capture_purchase_debug(page, "navigation_failed", url)
        return False

    @staticmethod
    async def _is_device_not_supported_visible(page: Page) -> bool:
        try:
            body_text = await EpicGames._combined_text(page, timeout=500, frame_timeout=300)
        except Exception:
            body_text = ""

        candidates = [
            page.get_by_role("button", name="Continue"),
            page.locator(
                "//button[normalize-space(.)='Continue' or .//span[normalize-space(.)='Continue']]"
            ),
        ]
        continue_visible = False
        for locator in candidates:
            if await EpicGames._is_locator_visible(locator, timeout=250):
                continue_visible = True
                break

        if "DEVICE NOT SUPPORTED" in body_text and continue_visible:
            return True

        if "NOT COMPATIBLE WITH YOUR CURRENT DEVICE" in body_text and continue_visible:
            return True

        return False

    @staticmethod
    async def _has_purchase_progress(page: Page, url: str) -> bool:
        if URL_CART_SUCCESS in page.url:
            return True

        if await EpicGames._is_claimed_state(page, url):
            return True

        if await EpicGames._is_checkout_security_check_visible(page):
            return True

        with suppress(Exception):
            iframe = page.locator(PURCHASE_IFRAME_SELECTOR).first
            if await iframe.is_visible(timeout=500):
                return True

        with suppress(Exception):
            button_text = await EpicGames._purchase_button_text(page)
            if any(marker in button_text for marker in ("IN CART", "VIEW IN CART", "CHECK OUT")):
                return True

        for frame_text in await EpicGames._frame_texts(page):
            if EpicGames._looks_like_checkout_frame(frame_text):
                return True

        return False

    @staticmethod
    def _looks_like_checkout_frame(text: str) -> bool:
        normalized = " ".join((text or "").upper().split())
        if not normalized:
            return False

        checkout_markers = (
            ("CHECKOUT", "PLACE ORDER"),
            ("REVIEW AND PLACE ORDER", "ORDER SUMMARY"),
            ("VERIFY YOUR INFORMATION", "ORDER SUMMARY"),
        )
        return any(all(marker in normalized for marker in markers) for markers in checkout_markers)

    @staticmethod
    async def _click_by_coordinates(page: Page, locator) -> None:
        box = await locator.bounding_box(timeout=2000)
        if not box:
            raise RuntimeError("button bounding box is unavailable")
        await page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)

    async def _click_purchase_button(self, page: Page, purchase_btn, url: str) -> bool:
        with suppress(Exception):
            await purchase_btn.scroll_into_view_if_needed(timeout=2000)

        click_attempts = (
            ("standard", lambda: purchase_btn.click(timeout=5000, no_wait_after=True)),
            ("dispatch", lambda: purchase_btn.dispatch_event("click")),
            ("dom", lambda: purchase_btn.evaluate("(button) => button.click()")),
            ("coordinate", lambda: self._click_by_coordinates(page, purchase_btn)),
            ("force", lambda: purchase_btn.click(force=True, timeout=5000, no_wait_after=True)),
        )

        for name, action in click_attempts:
            if await EpicGames._is_device_not_supported_visible(page):
                logger.warning(
                    "Device not supported modal blocking purchase click - dismissing before {} attempt - {}",
                    name,
                    url,
                )
                await EpicGames._handle_device_not_supported_modal(page, url, timeout_ms=5000)

            try:
                await asyncio.wait_for(action(), timeout=7000)
            except Exception as err:
                logger.warning("Purchase button {} click failed - {} err={!r}", name, url, err)
                continue

            await page.wait_for_timeout(2500)

            if await EpicGames._is_device_not_supported_visible(page):
                logger.warning(
                    "Device not supported modal appeared after {} click - dismissing - {}",
                    name,
                    url,
                )
                await EpicGames._handle_device_not_supported_modal(page, url, timeout_ms=5000)
                await page.wait_for_timeout(1500)

            if await self._has_purchase_progress(page, url):
                logger.debug("Purchase button {} click produced progress - {}", name, url)
                return True

            logger.debug(
                "Purchase button {} click returned without visible progress - {}", name, url
            )

        await self._capture_purchase_debug(page, "click_no_effect", url)
        return False

    @staticmethod
    async def _handle_device_not_supported_modal(
        page: Page, url: str, timeout_ms: int = 8000
    ) -> bool:
        elapsed = 0
        captured = False

        while elapsed < timeout_ms:
            if await EpicGames._is_device_not_supported_visible(page):
                logger.warning(
                    f"Device not supported modal detected - attempting to continue. {url=}"
                )
                if not captured:
                    await EpicGames._capture_purchase_debug(page, "device_not_supported", url)
                    captured = True

                try:
                    if await EpicGames._click_visible_continue_button(page):
                        await page.wait_for_timeout(2000)
                        if not await EpicGames._is_device_not_supported_visible(page):
                            logger.success("Dismissed device not supported modal")
                            return True

                        logger.warning(
                            "Device not supported modal is still visible after clicking Continue"
                        )
                    else:
                        logger.debug(
                            "Device modal is visible but its Continue button is not clickable yet"
                        )
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
            container = purchase_btn.locator(
                "xpath=ancestor::*[self::section or self::aside or self::div][1]"
            )
            container_text = (await container.text_content() or "").strip()
            container_text = " ".join(container_text.split())[:800]

        logger.debug(
            (
                "Purchase button context | url={} | text='{}' | disabled={} | "
                "aria-disabled={} | testid={} | class={} | container='{}'"
            ),
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
        wpc = page.frame_locator(PURCHASE_IFRAME_SELECTOR).first

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
            pass

        logger.debug(
            "Primary checkout buttons not found with purchase iframe selector; scanning frames."
        )

        containers = [*page.frames, page]
        for container in containers:
            with suppress(Exception):
                body_text = await container.locator("body").inner_text(timeout=500)
                if not EpicGames._looks_like_checkout_frame(body_text):
                    continue

                place_order_btn = container.locator("button", has_text="PLACE ORDER")
                confirm_btn = container.locator(
                    "//button[contains(@class, 'payment-confirm__btn')]"
                )

                try:
                    await expect(place_order_btn).to_be_visible(timeout=place_order_timeout)
                    logger.debug("✅ Found 'PLACE ORDER' button by scanning checkout containers")
                    return container, place_order_btn
                except AssertionError:
                    pass

                try:
                    await expect(confirm_btn).to_be_visible(timeout=confirm_timeout)
                    logger.debug("✅ Found payment confirm button by scanning checkout containers")
                    return container, confirm_btn
                except AssertionError:
                    pass

        logger.warning("Primary buttons not found in checkout containers.")
        raise AssertionError("Could not find Place Order button in checkout containers")

    @staticmethod
    async def _uk_confirm_order(wpc: PurchaseContainer):
        logger.debug("UK confirm order")
        with suppress(TimeoutError):
            accept = wpc.locator("//button[contains(@class, 'payment-confirm__btn')]")
            if await accept.is_enabled(timeout=5000):
                await accept.click()
                return True

    @staticmethod
    async def _has_disabled_payment_state(payment_btn) -> bool:
        disabled = await payment_btn.get_attribute("disabled")
        aria_disabled = await payment_btn.get_attribute("aria-disabled")
        class_name = (await payment_btn.get_attribute("class") or "").lower()

        return (
            disabled is not None
            or aria_disabled == "true"
            or "payment-btn--disabled" in class_name
            or "disabled" in class_name.split()
        )

    @staticmethod
    async def _visible_talon_overlay_id(page: Page) -> str | None:
        overlay = page.locator(
            "//*[contains(@id, 'talon_container') or contains(@class, 'talon_container')]"
        )
        count = await overlay.count()

        for index in range(count - 1, -1, -1):
            candidate = overlay.nth(index)
            with suppress(Exception):
                if not await candidate.is_visible(timeout=200):
                    continue
                overlay_id = await candidate.get_attribute("id")
                if overlay_id:
                    return overlay_id
                return "talon_overlay"

        return None

    async def _wait_for_checkout_ready(
        self, page: Page, url: str, timeout_ms: int = 15000
    ) -> tuple[PurchaseContainer, object] | None:
        elapsed = 0

        while elapsed < timeout_ms:
            if await self._is_checkout_security_check_visible(page):
                logger.debug(f"Checkout readiness interrupted by security check. {url=}")
                return None

            try:
                payload = await self._active_purchase_container(
                    page, place_order_timeout=500, confirm_timeout=500
                )
            except AssertionError:
                await page.wait_for_timeout(500)
                elapsed += 500
                continue

            _wpc, payment_btn = payload
            overlay_id = await self._visible_talon_overlay_id(page)
            disabled_state = await self._has_disabled_payment_state(payment_btn)

            if not overlay_id and not disabled_state:
                return payload

            logger.debug(
                "Checkout container is visible but not ready yet. {} | overlay={} | button={}",
                url,
                overlay_id,
                await self._payment_button_state(payment_btn),
            )
            await page.wait_for_timeout(750)
            elapsed += 750

        logger.debug(f"Checkout container never became ready before timeout. {url=}")
        return None

    async def _wait_for_purchase_state(self, page: Page, url: str, timeout_ms: int = 20000):
        elapsed = 0

        while elapsed < timeout_ms:
            await self._handle_device_not_supported_modal(page, url, timeout_ms=1000)

            if await self._is_claimed_state(page, url):
                return "claimed", None

            if await self._is_checkout_security_check_visible(page):
                return "security", None

            payload = await self._wait_for_checkout_ready(page, url, timeout_ms=1000)
            if payload is not None:
                return "checkout", payload

            await page.wait_for_timeout(500)
            elapsed += 1500

        return "pending", None

    @staticmethod
    async def _is_checkout_security_check_visible(page: Page) -> bool:
        page_markers = [
            "ONE MORE STEP",
            "PLEASE COMPLETE A SECURITY CHECK TO CONTINUE",
            "PLEASE DRAG THE ICON ON THE BOTTOM TO THE PLACE WHERE IT FITS",
            "PLEASE DRAG THE ICON ON THE LEFT TO THE PLACE WHERE IT FITS",
            "VERIFY THAT YOU ARE HUMAN",
            "VERIFY YOU ARE HUMAN",
        ]
        purchase_frame_markers = [*page_markers, "I AM HUMAN", "SKIP"]

        visible_locators = [
            page.get_by_text("One more step", exact=False),
            page.get_by_text("Please complete a security check to continue", exact=False),
            page.locator("//iframe[contains(@src, 'hcaptcha') or contains(@title, 'hCaptcha')]"),
            page.frame_locator(PURCHASE_IFRAME_SELECTOR).first.locator(
                "//iframe[contains(@src, 'hcaptcha') or contains(@title, 'hCaptcha')]"
            ),
        ]

        for locator in visible_locators:
            with suppress(Exception):
                if await locator.first.is_visible(timeout=300):
                    return True

        if await EpicGames._visible_hcaptcha_frame_urls(page):
            return True

        page_text = await EpicGames._page_text(page)
        if any(marker in page_text for marker in page_markers):
            return True

        purchase_frame_text = await EpicGames._purchase_frame_text(page)
        return any(marker in purchase_frame_text for marker in purchase_frame_markers)

    async def _resolve_checkout_security_check(
        self, page: Page, agent: AgentV, url: str, max_wait_ms: int = 600000
    ) -> bool:
        if not await self._is_checkout_security_check_visible(page):
            return True

        logger.warning(f"Checkout security check detected - starting solve loop. {url=}")

        started_at = time.monotonic()
        attempt = 0

        while (time.monotonic() - started_at) * 1000 < max_wait_ms:
            attempt += 1

            if await self._is_claimed_state(page, url):
                logger.success(f"Checkout security check resolved into claimed state - {url=}")
                return True

            if not await self._is_checkout_security_check_visible(page):
                logger.success(
                    f"Checkout security check cleared before solve attempt {attempt} - {url=}"
                )
                return True

            elapsed_seconds = int(time.monotonic() - started_at)
            logger.info(
                f"Solving checkout security check (attempt {attempt}, elapsed {elapsed_seconds}s)"
            )

            if attempt <= 3 or attempt % 2 == 0:
                await self._capture_purchase_debug(
                    page, f"checkout_security_check_attempt_{attempt}", url
                )

            await page.wait_for_timeout(2500)

            try:
                await agent.wait_for_challenge()
            except Exception as err:
                logger.warning(
                    f"Checkout security check solve attempt failed (attempt {attempt}): {err}"
                )
                if attempt <= 3 or attempt % 2 == 0:
                    await self._capture_purchase_debug(
                        page, f"checkout_security_check_failed_{attempt}", url
                    )

            await page.wait_for_timeout(1500)

            if await self._is_claimed_state(page, url):
                logger.success(
                    f"Checkout security check solved successfully into claimed state - {url=}"
                )
                return True

            if not await self._is_checkout_security_check_visible(page):
                logger.success(f"Checkout security check solved successfully - {url=}")
                return True

            outcome = await self._observe_checkout_outcome(page, url, timeout_ms=10000)
            logger.debug(
                f"Checkout security check follow-up outcome after attempt {attempt}: {outcome} | {url=}"
            )
            if outcome == "claimed":
                logger.success(f"Checkout security check resolved into claimed state - {url=}")
                return True
            if outcome == "checkout":
                logger.success(f"Checkout security check cleared back to checkout - {url=}")
                return True

        logger.warning(f"Checkout security check remained visible after timeout - {url=}")
        await self._capture_purchase_debug(page, "checkout_security_check_unresolved", url)
        return False

    async def _probe_checkout_challenge(self, page: Page, agent: AgentV, url: str) -> bool:
        logger.debug(f"Probing checkout for latent challenge. {url=}")
        if await self._is_checkout_security_check_visible(page):
            logger.debug(f"Checkout challenge probe found visible challenge before waiting. {url=}")
            return True

        try:
            await asyncio.wait_for(agent.wait_for_challenge(), timeout=25)
        except Exception as err:
            if await self._is_checkout_security_check_visible(page):
                logger.warning(
                    f"Checkout challenge probe detected challenge artifacts after wait failure: {err} | {url=}"
                )
                return True
            logger.info(f"No solvable latent checkout challenge detected: {err}")
            return False

        await page.wait_for_timeout(1500)
        await self._capture_purchase_debug(page, "checkout_challenge_probe", url)
        return True

    async def _extended_checkout_challenge_probe(
        self, page: Page, agent: AgentV, url: str, timeout_seconds: int = 90
    ) -> bool:
        logger.warning(
            "Checkout remained on Place Order after repeated attempts - running extended challenge probe. {}",
            url,
        )

        try:
            await asyncio.wait_for(agent.wait_for_challenge(), timeout=timeout_seconds)
        except Exception as err:
            if await self._is_checkout_security_check_visible(page):
                logger.warning(
                    f"Extended checkout challenge probe left a visible challenge behind: {err} | {url=}"
                )
                await self._capture_purchase_debug(page, "checkout_challenge_extended_visible", url)
                return True

            logger.info(
                f"Extended checkout challenge probe ended without a solvable challenge: {err}"
            )
            return False

        await page.wait_for_timeout(1500)
        await self._capture_purchase_debug(page, "checkout_challenge_extended_probe", url)
        return True

    async def _is_promotion_in_order_history(self, promotion: PromotionGame) -> bool:
        try:
            await self.page.goto(
                "https://www.epicgames.com/account/v2/payment/ajaxGetOrderHistory",
                wait_until="domcontentloaded",
                timeout=15000,
            )
            text_content = await self.page.text_content("//pre")
            payload = json.loads(text_content or "{}")
        except Exception as err:
            logger.warning(
                f"Failed to verify order history for promotion '{promotion.title}': {err!r}"
            )
            return False

        for order_payload in payload.get("orders", []):
            with suppress(Exception):
                order = Order(**order_payload)
                if order.orderType != "PURCHASE":
                    continue
                for item in order.items:
                    if item.namespace == promotion.namespace or item.offerId == promotion.id:
                        logger.success(
                            "Promotion found in order history - title='{}' namespace='{}' offer='{}'",
                            promotion.title,
                            promotion.namespace,
                            promotion.id,
                        )
                        return True

        return False

    async def _finalize_unconfirmed_checkout(self, page: Page, promotion: PromotionGame) -> bool:
        url = promotion.url

        await self._handle_device_not_supported_modal(page, url, timeout_ms=5000)
        if await self._is_claimed_state(page, url):
            logger.success(
                f"🎉 Instant checkout confirmed claim state during final verification - {url=}"
            )
            return True

        if await self._is_promotion_in_order_history(promotion):
            logger.success(f"🎉 Instant checkout confirmed via order history - {url=}")
            return True

        try:
            await page.goto(url, wait_until="load", timeout=15000)
            await page.wait_for_timeout(2500)
        except Exception as reload_err:
            logger.warning(f"Final instant checkout page revisit failed: {reload_err}")
            await self._capture_purchase_debug(page, "instant_checkout_final_reload_failed", url)
            return False

        if await self._is_claimed_state(page, url):
            logger.success(f"🎉 Instant checkout confirmed claim state after final reload - {url=}")
            return True

        if await self._is_promotion_in_order_history(promotion):
            logger.success(f"🎉 Instant checkout confirmed via order history after reload - {url=}")
            return True

        return False

    @staticmethod
    async def _payment_button_state(payment_btn) -> str:
        parts: list[str] = []

        with suppress(Exception):
            text = ((await payment_btn.text_content()) or "").strip()
            if text:
                parts.append(f"text='{text}'")

        for attr in ("disabled", "aria-disabled", "aria-busy", "class"):
            with suppress(Exception):
                value = await payment_btn.get_attribute(attr)
                if value:
                    parts.append(f"{attr}='{value}'")

        return " | ".join(parts) if parts else "state_unavailable"

    async def _submit_place_order(self, payment_btn, url: str) -> None:
        logger.debug(
            "Submitting place order. {} | before={}",
            url,
            await self._payment_button_state(payment_btn),
        )

        with suppress(Exception):
            await payment_btn.scroll_into_view_if_needed(timeout=2000)

        click_attempts = (
            ("standard", lambda: payment_btn.click(timeout=5000)),
            ("force", lambda: payment_btn.click(force=True, timeout=5000)),
            ("dispatch", lambda: payment_btn.dispatch_event("click")),
            ("dom", lambda: payment_btn.evaluate("(button) => button.click()")),
            ("keyboard", lambda: payment_btn.press("Enter", timeout=2000)),
        )

        for name, action in click_attempts:
            try:
                await action()
            except TimeoutError as err:
                logger.warning(f"Place Order {name} click timed out. {url=} err={err}")
                continue
            except Exception as err:
                logger.warning(f"Place Order {name} click failed. {url=} err={err}")
                continue

            await self.page.wait_for_timeout(1500)
            if not await self._is_locator_visible(payment_btn, timeout=750):
                logger.debug(f"Place Order button disappeared after {name} click. {url=}")
                return

            logger.debug(
                "Place Order state after {} click: {} | {}",
                name,
                url,
                await self._payment_button_state(payment_btn),
            )
            return

        logger.warning(
            "All Place Order submission strategies completed without a visible click success. {} | {}",
            url,
            await self._payment_button_state(payment_btn),
        )
        await self.page.wait_for_timeout(1500)

    async def _observe_checkout_outcome(self, page: Page, url: str, timeout_ms: int = 20000) -> str:
        elapsed = 0

        while elapsed < timeout_ms:
            await self._handle_device_not_supported_modal(page, url, timeout_ms=1000)

            if await self._is_checkout_security_check_visible(page):
                return "security"

            if await self._is_claimed_state(page, url):
                return "claimed"

            with suppress(Exception):
                await self._active_purchase_container(
                    page, place_order_timeout=500, confirm_timeout=500
                )

            await page.wait_for_timeout(1000)
            elapsed += 1500

        return "checkout"

    async def _handle_instant_checkout(self, page: Page, promotion: PromotionGame) -> bool:
        url = promotion.url
        logger.info("🚀 Triggering Instant Checkout Flow...")
        agent = AgentV(page=page, agent_config=settings)

        try:
            state, payload = await self._wait_for_purchase_state(page, url, timeout_ms=25000)
            if state == "claimed":
                logger.success(f"🎉 Instant checkout resolved to claimed state - {url=}")
                return True

            if state == "security":
                if not await self._resolve_checkout_security_check(page, agent, url):
                    return False
                state = "checkout"
                payload = None

            if state != "checkout" or payload is None:
                logger.warning(f"Instant checkout never reached a checkout container - {url=}")
                await self._capture_purchase_debug(page, "instant_checkout_not_reached", url)
                return False

            for attempt in range(1, 5):
                if state == "claimed":
                    logger.success(f"🎉 Instant checkout confirmed claim state - {url=}")
                    return True

                if state != "checkout" or payload is None:
                    state, payload = await self._wait_for_purchase_state(
                        page, url, timeout_ms=10000
                    )
                    if state == "claimed":
                        logger.success(
                            f"🎉 Instant checkout confirmed claim state after state refresh - {url=}"
                        )
                        return True
                    if state == "security":
                        if not await self._resolve_checkout_security_check(page, agent, url):
                            return False
                        state = "checkout"
                        payload = None
                        continue
                    if state != "checkout" or payload is None:
                        break

                _wpc, payment_btn = payload
                logger.debug(
                    "Place Order submission cycle ({}/{}) | button_text={}",
                    attempt,
                    4,
                    await payment_btn.text_content(),
                )
                await self._submit_place_order(payment_btn, url)

                if await self._is_checkout_security_check_visible(page):
                    if not await self._resolve_checkout_security_check(page, agent, url):
                        return False
                    outcome = await self._observe_checkout_outcome(page, url, timeout_ms=20000)
                    logger.debug(
                        f"Checkout outcome after solving security check: {outcome} | {url=}"
                    )
                    if outcome == "claimed":
                        logger.success(
                            f"🎉 Instant checkout confirmed claim state after security check - {url=}"
                        )
                        return True
                    state = "checkout" if outcome == "checkout" else outcome
                    payload = None
                    continue

                logger.debug("No explicit checkout security check detected after Place Order")
                with suppress(Exception):
                    await self._probe_checkout_challenge(page, agent, url)

                outcome = await self._observe_checkout_outcome(page, url, timeout_ms=20000)
                logger.debug(f"Checkout outcome after Place Order: {outcome} | {url=}")
                if outcome == "claimed":
                    logger.success(
                        f"🎉 Instant checkout confirmed claim state after Place Order - {url=}"
                    )
                    return True
                if outcome == "checkout" and attempt >= 2:
                    challenge_detected = await self._extended_checkout_challenge_probe(
                        page, agent, url
                    )
                    if challenge_detected and await self._is_checkout_security_check_visible(page):
                        if not await self._resolve_checkout_security_check(page, agent, url):
                            return False
                    if challenge_detected:
                        outcome = await self._observe_checkout_outcome(page, url, timeout_ms=30000)
                        logger.debug(f"Checkout outcome after extended probe: {outcome} | {url=}")
                        if outcome == "claimed":
                            logger.success(
                                f"🎉 Instant checkout confirmed claim state after extended probe - {url=}"
                            )
                            return True
                state = "checkout" if outcome == "checkout" else outcome
                payload = None

            logger.warning(f"Instant checkout ended without a confirmed claim state - {url=}")
            await self._capture_purchase_debug(page, "instant_checkout_unconfirmed", url)
            return await self._finalize_unconfirmed_checkout(page, promotion)

        except Exception as err:
            logger.warning(f"Instant checkout warning: {err}")
            await self._capture_purchase_debug(page, "instant_checkout_warning", url)
            with suppress(Exception):
                logger.debug(f"Instant checkout fallback | current_url={page.url}")
            await self._handle_device_not_supported_modal(page, url, timeout_ms=5000)
            if await self._is_claimed_state(page, url):
                logger.success(f"🎉 Instant checkout recovered into claimed state - {url=}")
                return True

            return await self._finalize_unconfirmed_checkout(page, promotion)

    async def add_promotion_to_cart(
        self, page: Page, promotions: List[PromotionGame]
    ) -> tuple[bool, int, List[str]]:
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

        for promotion in promotions:
            url = promotion.url
            game_title = promotion.title
            if not await self._goto_product_page(page, url, game_title):
                failed_urls.append(url)
                continue

            # 404 检测
            title = await page.title()
            if "404" in title or "Page Not Found" in title:
                logger.error(f"❌ Invalid URL (404 Page): {url}")
                failed_urls.append(url)
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
                        logger.success(
                            "Game already claimed / already in library (page text scan) - "
                            f"title='{game_title}' url='{url}'"
                        )
                        continue
                    logger.warning(f"Could not find any purchase button - {url=}")
                    await self._capture_purchase_debug(page, "button_missing", url)
                    failed_urls.append(url)
                    continue
            except Exception:
                pass

            # 3. 获取按钮上下文
            btn_text, container_text, disabled, aria_disabled = (
                await self._log_purchase_button_context(page, purchase_btn, url)
            )
            btn_text_upper = btn_text.upper()
            container_text_upper = container_text.upper()

            logger.debug(f"👉 Found Button: '{btn_text}'")

            # 4. 黑名单检查：只有这些情况绝对不能点
            # 如果是 'IN LIBRARY', 'OWNED', 'UNAVAILABLE', 'COMING SOON' -> 跳过
            if disabled is not None or aria_disabled == "true":
                logger.success(
                    "Game already claimed / unavailable (purchase button disabled) - "
                    f"title='{game_title}' text='{btn_text}' url='{url}'"
                )
                await self._capture_purchase_debug(page, "button_disabled", url)
                continue

            if any(marker in btn_text_upper for marker in owned_markers) or any(
                marker in container_text_upper for marker in owned_markers
            ):
                logger.success(
                    f"Game already claimed / already in library - title='{game_title}' text='{btn_text}' url='{url}'"
                )
                continue

            # 5. 白名单检查 (Add to Cart 特殊处理)
            # 如果包含 'CART'，说明是加入购物车流程
            if "CART" in btn_text_upper:
                logger.debug(f"🛒 Logic: Add To Cart - {url=}")
                if not await self._click_purchase_button(page, purchase_btn, url):
                    failed_urls.append(url)
                    continue
                has_pending_cart_items = True
                continue

            # 6. 默认处理 (盲点逻辑)
            # 只要不是黑名单，也不是购物车，统统当做 "Get/Purchase" 直接点击！
            # 不管它写的是 'Get', 'Free', 'Purchase', 'Buy Now'，只要 API 说是免费的，我们就点！
            logger.debug(f"⚡️ Logic: Aggressive Click (Text: {btn_text}) - {url=}")
            if await EpicGames._is_device_not_supported_visible(page):
                logger.warning(
                    f"Pre-click: device not supported modal detected, dismissing first. {url=}"
                )
                await EpicGames._handle_device_not_supported_modal(page, url, timeout_ms=5000)

            if not await self._click_purchase_button(page, purchase_btn, url):
                failed_urls.append(url)
                continue

            await self._handle_device_not_supported_modal(page, url)

            # 点击后，转入即时结账流程
            if await self._handle_instant_checkout(page, promotion):
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
        has_cart_items, instant_claimed, failed_urls = await self.add_promotion_to_cart(
            self.page, promotions
        )
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
