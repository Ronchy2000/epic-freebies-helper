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
