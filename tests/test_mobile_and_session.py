import asyncio
from types import SimpleNamespace

import pytest

import services.epic_games_service as epic_games_service
from models import OrderItem, PromotionGame
from services.epic_games_service import (
    EpicAgent,
    EpicSessionExpiredError,
    _is_promotion_owned_in_orders,
)
from services.epic_mobile_service import (
    append_mobile_promotions,
    enabled_platforms,
    parse_free_games,
)


def test_mobile_platforms_default_disabled_and_toggle_independently(monkeypatch):
    monkeypatch.delenv("EPIC_MOBILE_ANDROID", raising=False)
    monkeypatch.delenv("EPIC_MOBILE_IOS", raising=False)
    assert enabled_platforms() == []

    monkeypatch.setenv("EPIC_MOBILE_ANDROID", "true")
    assert enabled_platforms() == ["android"]

    monkeypatch.setenv("EPIC_MOBILE_IOS", "1")
    assert enabled_platforms() == ["android", "ios"]


def test_parse_free_games_extracts_claimable_zero_price_mobile_offers():
    payload = {
        "data": [
            {
                "type": "freeGame",
                "offers": [
                    {
                        "offerId": "fallback-id",
                        "content": {
                            "title": "Knightica",
                            "mapping": {"slug": "knightica-android-ad8285"},
                            "purchase": [
                                {
                                    "purchaseType": "Claim",
                                    "price": {"decimalPrice": 0},
                                    "purchasePayload": {
                                        "offerId": "offer-android-1",
                                        "sandboxId": "ns-shared-1234567890123456789012",
                                    },
                                }
                            ],
                        },
                    },
                    {
                        "offerId": "paid-offer",
                        "content": {
                            "title": "Paid Mobile Game",
                            "mapping": {"slug": "paid-mobile"},
                            "purchase": [{"purchaseType": "Buy", "price": {"decimalPrice": 4.99}}],
                        },
                    },
                ],
            }
        ]
    }

    parsed = parse_free_games(payload, "android")

    assert parsed == [
        {
            "slug": "knightica-android-ad8285",
            "title": "Knightica",
            "platform": "android",
            "offer_id": "offer-android-1",
            "namespace": "ns-shared-1234567890123456789012",
        }
    ]


def test_append_mobile_promotions_skips_owned_offer_ids_and_keeps_unowned(monkeypatch):
    monkeypatch.setenv("EPIC_MOBILE_ANDROID", "true")
    monkeypatch.setenv("EPIC_MOBILE_IOS", "true")

    async def fake_discover(_page, platform):
        return [
            {
                "slug": f"demo-{platform}",
                "title": "Demo",
                "platform": platform,
                "offer_id": f"offer-{platform}",
                "namespace": "ns-shared-1234567890123456789012",
            }
        ]

    monkeypatch.setattr("services.epic_mobile_service._discover_platform", fake_discover)
    page = SimpleNamespace(url="https://store.epicgames.com/en-US/free-games")

    result = asyncio.run(
        append_mobile_promotions(
            page,
            [],
            product_url_prefix="https://store.epicgames.com/en-US/p/",
            exclude_offer_ids={"offer-android"},
        )
    )

    assert len(result) == 1
    assert result[0].title == "Demo (iOS)"
    assert result[0].id == "offer-ios"


def test_check_orders_raises_session_expired_and_captures_debug_via_epic_games(monkeypatch):
    captured = []
    page = SimpleNamespace(url="https://www.epicgames.com/id/login")
    agent = EpicAgent(page)

    async def fail_sync():
        return False

    async def fake_capture(target_page, reason, url):
        captured.append((target_page, reason, url))

    monkeypatch.setattr(agent, "_sync_order_history", fail_sync)
    monkeypatch.setattr(agent.epic_games, "_capture_purchase_debug", fake_capture)

    with pytest.raises(EpicSessionExpiredError):
        asyncio.run(agent._check_orders())

    assert len(captured) == 1
    assert captured[0][1] == "session_probe_failed"


def test_pc_order_check_matches_offer_id_before_shared_namespace(monkeypatch):
    shared_ns = "a" * 32
    pc_promo = PromotionGame(
        title="Shared Game",
        id="offer-pc",
        namespace=shared_ns,
        description="",
        offerType="BASE_GAME",
        url="https://store.epicgames.com/en-US/p/shared-game",
    )
    android_order = OrderItem(
        description="Shared Game (Android)", offerId="offer-android", namespace=shared_ns
    )

    assert _is_promotion_owned_in_orders(pc_promo, [android_order]) is False
    assert (
        _is_promotion_owned_in_orders(
            pc_promo,
            [
                android_order,
                OrderItem(description="Shared Game", offerId="offer-pc", namespace=shared_ns),
            ],
        )
        is True
    )
    monkeypatch.setattr(epic_games_service, "get_promotions", lambda: [pc_promo])
    monkeypatch.setattr(epic_games_service, "append_mobile_promotions", None)
    agent = EpicAgent(SimpleNamespace(url="https://store.epicgames.com/en-US/free-games"))
    agent._orders = [android_order]

    async def synced():
        return True

    monkeypatch.setattr(agent, "_sync_order_history", synced)
    asyncio.run(agent._check_orders())
    assert [p.id for p in agent._promotions] == ["offer-pc"]
