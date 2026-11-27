import asyncio

from services.browser_context import _install_hsw_identity_route


def test_hsw_route_forces_identity_without_dropping_request_headers():
    class Request:
        @staticmethod
        async def all_headers():
            return {"accept-encoding": "gzip, deflate", "x-request-id": "kept"}

    class Route:
        request = Request()
        continued_headers = None

        async def continue_(self, *, headers):
            self.continued_headers = headers

    class Context:
        pattern = None
        handler = None

        async def route(self, pattern, handler):
            self.pattern = pattern
            self.handler = handler

    async def scenario():
        context = Context()
        route = Route()
        await _install_hsw_identity_route(context)
        await context.handler(route)
        return context, route

    context, route = asyncio.run(scenario())

    assert context.pattern == "**/hsw.js*"
    assert route.continued_headers == {"accept-encoding": "identity", "x-request-id": "kept"}


def test_camoufox_unknown_property_is_classified_as_bootstrap_error():
    from services.browser_context import _is_camoufox_bootstrap_error

    class UnknownProperty(Exception):
        pass

    assert _is_camoufox_bootstrap_error(
        UnknownProperty("Unknown property navigator.appCodeName in config")
    )
    assert _is_camoufox_bootstrap_error(
        RuntimeError("Unknown property navigator.appCodeName in config")
    )


def test_camoufox_unknown_property_guard_drops_deprecated_keys_only(monkeypatch):
    import camoufox.utils as camoufox_utils
    from services.browser_context import _install_camoufox_unknown_property_guard

    received = {}

    def fake_load_properties(path=None):
        return {"screen.width": "uint", "navigator.userAgent": "str"}

    def fake_validate_config(config_map, path=None):
        received.clear()
        received.update(config_map)
        for key in config_map:
            if key not in fake_load_properties(path):
                raise RuntimeError(f"Unknown property {key} in config")

    monkeypatch.setattr(camoufox_utils, "_load_properties", fake_load_properties)
    monkeypatch.setattr(camoufox_utils, "validate_config", fake_validate_config)

    _install_camoufox_unknown_property_guard()
    config = {
        "screen.width": 1920,
        "navigator.appCodeName": "Mozilla",
        "navigator.userAgent": "Firefox",
    }
    camoufox_utils.validate_config(config)

    assert "navigator.appCodeName" not in config
    assert received == {"screen.width": 1920, "navigator.userAgent": "Firefox"}
