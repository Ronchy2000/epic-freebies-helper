"""Epic 移动端限免（Android / iOS）的发现与注入。

移动端限免与 PC 限免是两个独立商品页（例如 ``/p/<slug>-android-<hash>`` 与
``/p/<slug>-ios-<hash>``），但领取走的是同一套桌面网页 0 元结账流程，因此本模块
只负责「发现」，把结果转换成 :class:`models.PromotionGame` 追加进待领列表，后续
登录、结账、验证码、订单核对全部复用既有流程。

两个开关都默认关闭：

- ``EPIC_MOBILE_ANDROID``
- ``EPIC_MOBILE_IOS``

移动端目录接口只接受来自店铺页面自身的请求（纯 HTTP 客户端会被 Cloudflare 拒绝），
所以发现阶段需要一个已登录的 ``Page``，由调用方传入。

本模块的任何失败都不会向上抛出：移动端是增量能力，不能影响 PC 限免的领取。
"""

from __future__ import annotations

import json
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress

from loguru import logger
from models import PromotionGame
from playwright.async_api import Page

# Epic 移动端店铺首页接口；PC 的 freeGames 源里没有移动端条目。
DISCOVER_API = (
    "https://egs-platform-service.store.epicgames.com/api/v2/public/discover/home"
    "?count=10&country={country}&locale={locale}&platform={platform}&start=0&store=EGS"
)
LOCALE = "en"
# 目录按国家区分，同一款游戏的 offer 不随国家变化（实测 US/CN 的 offerId 相同），
# 依次查询并合并可覆盖区域差异，且不需要新增配置项。
COUNTRIES = ("US", "CN")

VALID_PLATFORMS = ("android", "ios")
PLATFORM_LABELS = {"android": "Android", "ios": "iOS"}
PLATFORM_FLAGS = {"android": "EPIC_MOBILE_ANDROID", "ios": "EPIC_MOBILE_IOS"}

_TRUTHY = {"1", "true", "yes", "on"}

FETCH_JSON_JS = """
async (url) => {
  try {
    const response = await fetch(url, {
      headers: {accept: 'application/json'},
      credentials: 'include',
    });
    if (!response.ok) {
      return {ok: false, status: response.status, body: ''};
    }
    return {ok: true, status: response.status, body: await response.text()};
  } catch (error) {
    return {ok: false, status: 0, body: '', error: String(error)};
  }
}
"""


def enabled_platforms() -> list[str]:
    """读取两个独立开关，返回本次需要处理的平台。"""
    platforms: list[str] = []
    for platform in VALID_PLATFORMS:
        raw = (os.getenv(PLATFORM_FLAGS[platform]) or "").strip().lower()
        if raw in _TRUTHY:
            platforms.append(platform)
    return platforms


def is_claimable_free(content: dict) -> bool:
    """判断移动端条目当前是否处于「限免中」而不是促销结束后的付费入口。"""
    for entry in content.get("purchase") or []:
        if not isinstance(entry, dict):
            continue
        price = entry.get("price") or {}
        if entry.get("purchaseType") == "Claim" and price.get("decimalPrice") == 0:
            return True
    return False


def parse_free_games(payload: dict, platform: str) -> list[dict]:
    """从一个 discover 响应里取出当期限免的移动端商品。纯函数，无 IO。"""
    games: list[dict] = []
    for section in payload.get("data") or []:
        if not isinstance(section, dict) or section.get("type") != "freeGame":
            continue
        for offer in section.get("offers") or []:
            if not isinstance(offer, dict):
                continue
            content = offer.get("content") or {}
            if not isinstance(content, dict):
                continue
            slug = ((content.get("mapping") or {}).get("slug") or "").strip()
            if not slug or not is_claimable_free(content):
                continue

            offer_id = ""
            namespace = ""
            for entry in content.get("purchase") or []:
                if not isinstance(entry, dict) or entry.get("purchaseType") != "Claim":
                    continue
                purchase_payload = entry.get("purchasePayload") or {}
                offer_id = (purchase_payload.get("offerId") or "").strip()
                # 校验过的映射：订单历史里 item.offerId 对应 offerId，
                # item.namespace 对应 sandboxId（M0c 用 instant checkout 直链验证过）。
                namespace = (purchase_payload.get("sandboxId") or "").strip()
                break

            games.append(
                {
                    "slug": slug,
                    "title": (content.get("title") or slug).strip(),
                    "platform": platform,
                    "offer_id": offer_id or (offer.get("offerId") or "").strip(),
                    "namespace": namespace,
                }
            )
    return games


async def _fetch_json(page: Page, url: str) -> dict | None:
    """在店铺页面上下文里请求 JSON；任何失败都返回 None。

    店铺页面已经渲染完成时，页面内 ``fetch`` 最贴近真实客户端；某些页面状态
    （正在跳转、CSP 差异）下它会直接失败，此时退回 ``page.request``：它沿用同一
    浏览器上下文的 cookie 与网络栈，只是不受 CORS 约束。
    """
    try:
        result = await page.evaluate(FETCH_JSON_JS, url)
    except Exception as err:  # noqa: BLE001 - 探测失败不应影响主流程
        logger.debug("Epic mobile: in-page fetch raised | url={} | err={!r}", url, err)
        result = None

    if isinstance(result, dict) and result.get("ok"):
        try:
            return json.loads(result.get("body") or "{}")
        except ValueError as err:
            logger.debug("Epic mobile: invalid JSON payload | err={!r}", err)
            return None

    if isinstance(result, dict):
        logger.debug(
            "Epic mobile: in-page fetch rejected | status={!r} | err={!r} | page_url={}",
            result.get("status"),
            result.get("error"),
            getattr(page, "url", "?"),
        )

    # 页面可能仍在跳转中，稍等再试一次页面内 fetch（成功路径最接近真实客户端）。
    try:
        await page.wait_for_timeout(1500)
        result = await page.evaluate(FETCH_JSON_JS, url)
        if isinstance(result, dict) and result.get("ok"):
            return json.loads(result.get("body") or "{}")
    except Exception as err:  # noqa: BLE001 - 同上
        logger.debug("Epic mobile: in-page fetch retry failed | url={} | err={!r}", url, err)

    response = None
    try:
        response = await page.request.get(
            url,
            headers={"accept": "application/json", "referer": "https://store.epicgames.com/"},
            timeout=20000,
        )
    except Exception as err:  # noqa: BLE001 - 同上
        logger.debug("Epic mobile: page.request failed | url={} | err={!r}", url, err)
        return None

    if response is None or not response.ok:
        logger.debug(
            "Epic mobile: page.request non-OK | status={!r}", getattr(response, "status", None)
        )
        return None
    try:
        return json.loads(await response.text())
    except ValueError as err:
        logger.debug("Epic mobile: page.request invalid JSON | err={!r}", err)
        return None


async def _discover_platform(page: Page, platform: str) -> list[dict]:
    """查询一个平台的移动端限免，跨国家合并去重（按 slug）。"""
    found: list[dict] = []
    seen: set[str] = set()
    for country in COUNTRIES:
        url = DISCOVER_API.format(country=country, locale=LOCALE, platform=platform)
        payload = await _fetch_json(page, url)
        if payload is None:
            continue
        for game in parse_free_games(payload, platform):
            if game["slug"] in seen:
                continue
            seen.add(game["slug"])
            found.append(game)
    logger.debug("Epic mobile: discovered {} ({})", len(found), platform)
    return found


@asynccontextmanager
async def _store_origin_page(page: Page) -> AsyncIterator[Page]:
    """保证在同源的 store 页面上发请求。

    发现接口只接受来自 ``store.epicgames.com`` 自身的请求。调用方传进来的页面
    可能停在 ``accounts.epicgames.com``（订单历史就是直接跳转到原始 JSON 接口），
    那种状态下页面内 fetch 会被 CORS 拒绝、``page.request`` 会被 Cloudflare 403。
    此时临时开一个 store 页面做发现，用完立即关闭，不干扰主流程的页面状态。
    """
    if "store.epicgames.com" in (page.url or ""):
        yield page
        return

    temp_page = await page.context.new_page()
    try:
        await temp_page.goto(
            "https://store.epicgames.com/en-US/", wait_until="domcontentloaded", timeout=60000
        )
        yield temp_page
    finally:
        with suppress(Exception):
            await temp_page.close()


def _to_promotion(game: dict, product_url_prefix: str) -> PromotionGame:
    platform_label = PLATFORM_LABELS.get(game["platform"], game["platform"])
    return PromotionGame(
        title=f"{game['title']} ({platform_label})",
        id=game["offer_id"],
        namespace=game["namespace"],
        description=f"Epic Games mobile freebie ({platform_label})",
        offerType="BASE_GAME",
        url=f"{product_url_prefix.rstrip('/')}/{game['slug']}",
    )


async def append_mobile_promotions(
    page: Page,
    promotions: list[PromotionGame],
    product_url_prefix: str,
    exclude_offer_ids: set[str] | None = None,
) -> list[PromotionGame]:
    """把当期限免的移动端商品追加到待领列表。

    ``product_url_prefix`` 由调用方传入主项目既有的商品页前缀
    (``epic_games_service.URL_PRODUCT_PAGE``), 保证语言与 PC 一致。
    ``exclude_namespaces`` 是订单历史里已拥有的 namespace 集合，用于跳过已经
    领取过的移动端商品（移动端 SKU 的 namespace 就是 discover 返回的 sandboxId）。

    返回值永远是列表：失败时原样返回传入的 ``promotions``。
    """
    platforms = enabled_platforms()
    if not platforms:
        return promotions

    logger.debug("Epic mobile: discovering on page={}", getattr(page, "url", "?"))

    owned = exclude_offer_ids or set()
    try:
        existing_urls = {promotion.url for promotion in promotions}
        extras: list[PromotionGame] = []
        async with _store_origin_page(page) as discovery_page:
            logger.debug("Epic mobile: discovering on page={}", discovery_page.url)
            for platform in platforms:
                for game in await _discover_platform(discovery_page, platform):
                    promotion = _to_promotion(game, product_url_prefix)
                    if promotion.url in existing_urls:
                        logger.debug("Epic mobile: skip duplicate url={}", promotion.url)
                        continue
                    if promotion.id and promotion.id in owned:
                        logger.success(
                            "Game already claimed previously - title='{}' url='{}'",
                            promotion.title,
                            promotion.url,
                        )
                        continue
                    existing_urls.add(promotion.url)
                    extras.append(promotion)
    except Exception as err:  # noqa: BLE001 - 移动端失败不得影响 PC 领取
        logger.warning("Epic mobile: discovery failed, continuing with PC only | err={!r}", err)
        return promotions

    if not extras:
        logger.info("Epic mobile: no free mobile game found this week")
        return promotions

    logger.info(
        "📱 Epic mobile: including {} free mobile item(s) | {}",
        len(extras),
        ", ".join(f"{item.title} -> {item.url}" for item in extras),
    )
    return [*promotions, *extras]
