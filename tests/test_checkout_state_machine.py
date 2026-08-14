import asyncio
from types import SimpleNamespace

import pytest

import services.epic_games_service as epic_games_service
from services.epic_games_service import EpicFreeGameRateLimitError, EpicGames


class FakeClock:
    def __init__(self):
        self.value = 0.0

    def monotonic(self):
        return self.value

    async def wait(self, timeout_ms):
        self.value += timeout_ms / 1000


class MissingLocator:
    @property
    def first(self):
        return self

    async def is_visible(self):
        return False

    async def count(self):
        return 0


class SlowBodyLocator:
    def __init__(self, clock, scans):
        self.clock = clock
        self.scans = scans

    async def inner_text(self, timeout):
        self.scans.append(timeout)
        self.clock.value += timeout / 1000
        return "CHECKOUT ADD TO LIBRARY"


class SlowCheckoutContainer:
    url = "https://store.epicgames.com/purchase#/free-checkout"

    def __init__(self, clock, scans):
        self.clock = clock
        self.scans = scans

    def locator(self, selector, **kwargs):
        if selector == "body":
            return SlowBodyLocator(self.clock, self.scans)
        return MissingLocator()


class FakePage:
    def __init__(self, clock=None):
        self.clock = clock

    async def wait_for_timeout(self, timeout_ms):
        if self.clock is not None:
            await self.clock.wait(timeout_ms)


class TextBody:
    def __init__(self, text):
        self.text = text

    async def inner_text(self, timeout):
        return self.text


class TextFrame:
    def __init__(self, text):
        self.text = text

    def locator(self, selector):
        assert selector == "body"
        return TextBody(self.text)


class VisibleCheckoutButton:
    async def is_visible(self):
        return True

    async def text_content(self, timeout):
        return "Add to library"

    async def get_attribute(self, name, timeout):
        return None


class CheckoutCandidates:
    def __init__(self, button):
        self.button = button

    async def count(self):
        return 1

    def nth(self, index):
        assert index == 0
        return self.button


class StructuralCheckoutFrame:
    url = "https://store.epicgames.com/widget"

    def __init__(self, button):
        self.button = button

    def locator(self, selector, **kwargs):
        if selector == epic_games_service.CHECKOUT_SUBMIT_SELECTOR:
            return CheckoutCandidates(self.button)
        raise AssertionError("visible structural checkout button must be checked before body text")


class TextOnlyCheckoutFrame:
    def __init__(self, button):
        self.button = button

    def locator(self, selector, **kwargs):
        assert selector == epic_games_service.CHECKOUT_SUBMIT_SELECTOR
        return MissingLocator()

    def get_by_text(self, pattern):
        assert pattern.fullmatch("Add to library")
        return CheckoutCandidates(self.button)


class IframeLocator:
    def __init__(self, frame):
        self.frame = frame

    async def count(self):
        return 1

    def nth(self, index):
        assert index == 0
        return self.frame


class StructuralCheckoutPage(FakePage):
    def __init__(self, checkout_frame, fallback_frame):
        super().__init__()
        self.main_frame = object()
        self.frames = [self.main_frame, fallback_frame, checkout_frame]
        self.checkout_frame = checkout_frame

    def locator(self, selector):
        assert selector == epic_games_service.PURCHASE_IFRAME_SELECTOR
        return IframeLocator(self.checkout_frame)

    def frame_locator(self, selector):
        assert selector == epic_games_service.PURCHASE_IFRAME_SELECTOR
        return IframeLocator(self.checkout_frame)


def test_active_purchase_container_uses_one_total_timeout(monkeypatch):
    clock = FakeClock()
    scans = []
    page = FakePage(clock)
    containers = [SlowCheckoutContainer(clock, scans) for _ in range(3)]

    async def ordered_containers(_page):
        return containers

    monkeypatch.setattr(epic_games_service.time, "monotonic", clock.monotonic)
    monkeypatch.setattr(EpicGames, "_ordered_checkout_containers", staticmethod(ordered_containers))

    with pytest.raises(AssertionError, match="checkout submit button"):
        asyncio.run(
            EpicGames._active_purchase_container(
                page, place_order_timeout=500, confirm_timeout=500, log_missing=False
            )
        )

    assert len(scans) >= 3
    assert sum(scans) <= 500
    assert clock.value == pytest.approx(0.5)


def test_active_purchase_container_prioritizes_structural_checkout_frame():
    button = VisibleCheckoutButton()
    checkout_frame = StructuralCheckoutFrame(button)
    page = StructuralCheckoutPage(checkout_frame, SimpleNamespace(url="https://hcaptcha.com/1"))

    container, located_button = asyncio.run(
        EpicGames._active_purchase_container(
            page, place_order_timeout=500, confirm_timeout=500, log_missing=False
        )
    )

    assert container is checkout_frame
    assert located_button is button


def test_visible_checkout_submit_matches_title_case_text_fallback():
    button = VisibleCheckoutButton()

    located_button, text = asyncio.run(
        EpicGames._visible_checkout_submit(TextOnlyCheckoutFrame(button), timeout_ms=500)
    )

    assert located_button is button
    assert text == "ADD TO LIBRARY"


def test_free_game_rate_limit_requires_complete_epic_message():
    partial_page = SimpleNamespace(
        frames=[TextFrame("Your account is unable to download any more free games")]
    )
    limited_page = SimpleNamespace(
        frames=[
            TextFrame(
                "Your account is unable to download any more free games at this time, "
                "please wait 24 hours before trying to redeem a free game again."
            )
        ]
    )

    assert asyncio.run(EpicGames._is_free_game_rate_limited(partial_page)) is False
    assert asyncio.run(EpicGames._is_free_game_rate_limited(limited_page)) is True


def test_rate_limit_error_is_not_swallowed_by_checkout_fallback(monkeypatch):
    page = FakePage()
    game = EpicGames(page)

    async def rate_limited(*args, **kwargs):
        raise EpicFreeGameRateLimitError("wait 24 hours")

    async def unexpected_finalize(*args, **kwargs):
        pytest.fail("rate limiting must not enter final reconciliation")

    monkeypatch.setattr(epic_games_service, "AgentV", lambda **kwargs: object())
    monkeypatch.setattr(game, "_wait_for_purchase_state", rate_limited)
    monkeypatch.setattr(game, "_finalize_unconfirmed_checkout", unexpected_finalize)

    with pytest.raises(EpicFreeGameRateLimitError, match="wait 24 hours"):
        asyncio.run(
            game._handle_instant_checkout(
                page, SimpleNamespace(url="https://example.test/game"), timeout_ms=1000
            )
        )


def test_observe_checkout_outcome_returns_pending_without_container(monkeypatch):
    clock = FakeClock()
    page = FakePage(clock)
    game = EpicGames(page)
    scans = 0

    async def no_device_modal(*args, **kwargs):
        return False

    async def not_visible(*args, **kwargs):
        return False

    async def missing_container(*args, **kwargs):
        nonlocal scans
        scans += 1
        clock.value += 2
        raise AssertionError("missing")

    monkeypatch.setattr(epic_games_service.time, "monotonic", clock.monotonic)
    monkeypatch.setattr(game, "_handle_device_not_supported_modal", no_device_modal)
    monkeypatch.setattr(game, "_is_checkout_security_check_visible", not_visible)
    monkeypatch.setattr(game, "_is_claimed_state", not_visible)
    monkeypatch.setattr(game, "_active_purchase_container", missing_container)

    outcome = asyncio.run(
        game._observe_checkout_outcome(page, "https://example.test/game", timeout_ms=1000)
    )

    assert outcome == "pending"
    assert scans == 1


def test_security_clearance_requires_recoverable_checkout_state(monkeypatch):
    page = FakePage()
    game = EpicGames(page)
    visibility = iter([True, False])

    async def security_visibility(*args, **kwargs):
        return next(visibility)

    async def not_claimed(*args, **kwargs):
        return False

    async def pending_outcome(*args, **kwargs):
        return "pending"

    monkeypatch.setattr(game, "_is_checkout_security_check_visible", security_visibility)
    monkeypatch.setattr(game, "_is_claimed_state", not_claimed)
    monkeypatch.setattr(game, "_observe_checkout_outcome", pending_outcome)

    recovered = asyncio.run(
        game._resolve_checkout_security_check(
            page, object(), "https://example.test/game", max_wait_ms=1000
        )
    )

    assert recovered is False


def test_security_recovery_does_not_consume_submission_attempts(monkeypatch):
    page = FakePage()
    game = EpicGames(page)
    button = SimpleNamespace(text_content=lambda: None)
    purchase_payload = (object(), button)
    states = iter(
        [
            ("checkout", purchase_payload),
            ("security", None),
            ("checkout", purchase_payload),
            ("security", None),
            ("checkout", purchase_payload),
            ("security", None),
            ("checkout", purchase_payload),
        ]
    )
    submissions = 0
    security_resolutions = 0

    async def button_text_content():
        return "Add to library"

    button.text_content = button_text_content

    async def next_state(*args, **kwargs):
        return next(states)

    async def submit(*args, **kwargs):
        nonlocal submissions
        submissions += 1
        return True

    async def security_not_visible(*args, **kwargs):
        return False

    async def resolve_security(*args, **kwargs):
        nonlocal security_resolutions
        security_resolutions += 1
        return True

    async def probe(*args, **kwargs):
        return False

    async def observe(*args, **kwargs):
        return "claimed" if submissions == 4 else "security"

    async def unexpected_finalize(*args, **kwargs):
        pytest.fail("successful fourth submission must not enter final reconciliation")

    monkeypatch.setattr(epic_games_service, "AgentV", lambda **kwargs: object())
    monkeypatch.setattr(game, "_wait_for_purchase_state", next_state)
    monkeypatch.setattr(game, "_submit_place_order", submit)
    monkeypatch.setattr(game, "_is_checkout_security_check_visible", security_not_visible)
    monkeypatch.setattr(game, "_resolve_checkout_security_check", resolve_security)
    monkeypatch.setattr(game, "_probe_checkout_challenge", probe)
    monkeypatch.setattr(game, "_observe_checkout_outcome", observe)
    monkeypatch.setattr(game, "_finalize_unconfirmed_checkout", unexpected_finalize)

    claimed = asyncio.run(
        game._handle_instant_checkout(
            page,
            SimpleNamespace(url="https://example.test/game"),
            allow_finalize=False,
            timeout_ms=60000,
        )
    )

    assert claimed is True
    assert submissions == 4
    assert security_resolutions == 3


def test_initial_security_state_refreshes_checkout_before_submission(monkeypatch):
    page = FakePage()
    game = EpicGames(page)

    async def button_text_content():
        return "Add to library"

    button = SimpleNamespace(text_content=button_text_content)
    states = iter([("security", None), ("checkout", (object(), button))])
    submissions = 0

    async def next_state(*args, **kwargs):
        return next(states)

    async def resolve_security(*args, **kwargs):
        return True

    async def submit(*args, **kwargs):
        nonlocal submissions
        submissions += 1
        return True

    async def security_not_visible(*args, **kwargs):
        return False

    async def probe(*args, **kwargs):
        return False

    async def claimed_outcome(*args, **kwargs):
        return "claimed"

    monkeypatch.setattr(epic_games_service, "AgentV", lambda **kwargs: object())
    monkeypatch.setattr(game, "_wait_for_purchase_state", next_state)
    monkeypatch.setattr(game, "_resolve_checkout_security_check", resolve_security)
    monkeypatch.setattr(game, "_submit_place_order", submit)
    monkeypatch.setattr(game, "_is_checkout_security_check_visible", security_not_visible)
    monkeypatch.setattr(game, "_probe_checkout_challenge", probe)
    monkeypatch.setattr(game, "_observe_checkout_outcome", claimed_outcome)

    claimed = asyncio.run(
        game._handle_instant_checkout(
            page,
            SimpleNamespace(url="https://example.test/game"),
            allow_finalize=False,
            timeout_ms=60000,
        )
    )

    assert claimed is True
    assert submissions == 1
