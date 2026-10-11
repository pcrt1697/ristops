import pytest
from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.responses import PlainTextResponse
from starlette.routing import Route

from helpers import MARKER, build_marked_app, make_scope
import ristops_lib_core.app.routes as routes_module
from ristops_lib_core.app.routes import RouteAttributeRegistry, get_routes_with_attr, iter_api_routes


class TestIterApiRoutes:

    def test_yields_routes_added_through_nested_include_router(self):
        paths = {path for _, path in iter_api_routes(build_marked_app())}

        assert {"/api/inner/items/{item_id}", "/api/things", "/api/unmarked", "/direct", "/multi"} <= paths

    def test_paths_carry_every_include_prefix(self):
        paths = {path for _, path in iter_api_routes(build_marked_app())}

        assert "/items/{item_id}" not in paths
        assert "/inner/items/{item_id}" not in paths

    def test_the_route_itself_does_not_know_the_prefix_added_when_its_router_was_included(self):
        route, path = next(item for item in iter_api_routes(build_marked_app()) if "items" in item[1])

        assert route.path == "/inner/items/{item_id}"
        assert path == "/api/inner/items/{item_id}"

    def test_yields_only_api_routes(self):
        app = build_marked_app()
        app.add_route("/plain", lambda request: PlainTextResponse("ok"))

        routes = list(iter_api_routes(app))

        assert routes and all(isinstance(route, APIRoute) for route, _ in routes)
        assert not {path for _, path in routes} & {"/plain", "/sub", "/docs", "/openapi.json"}

    def test_an_app_without_api_routes_yields_nothing(self):
        assert list(iter_api_routes(FastAPI())) == []

    def test_exposes_methods_and_endpoint(self):
        route, _ = next(item for item in iter_api_routes(build_marked_app()) if item[1] == "/api/things")

        assert route.methods == {"POST"}
        assert route.endpoint.__name__ == "create_thing"

    def test_a_route_without_a_readable_path_is_reported(self, monkeypatch: pytest.MonkeyPatch):
        async def endpoint() -> None: ...

        class Unreadable:
            original_route = APIRoute("/x", endpoint)
            path = None

        monkeypatch.setattr(routes_module, "iter_route_contexts", lambda routes: iter([Unreadable()]))

        with pytest.raises(RuntimeError, match="Cannot read the path of route"):
            list(iter_api_routes(FastAPI()))


class TestGetRoutesWithAttr:

    def test_maps_method_and_full_path_to_the_marker_value(self):
        routes = get_routes_with_attr(build_marked_app(), MARKER)

        assert routes[("get", "/api/inner/items/{item_id}")] == "inner-get"
        assert routes[("post", "/api/things")] == "outer-post"
        assert routes[("get", "/direct")] == "direct"

    def test_skips_routes_without_the_marker(self):
        routes = get_routes_with_attr(build_marked_app(), MARKER)

        assert ("get", "/api/unmarked") not in routes
        assert set(routes.values()) == {"inner-get", "outer-post", "direct", "multi"}

    def test_a_route_with_several_methods_gets_an_entry_per_method(self):
        routes = get_routes_with_attr(build_marked_app(), MARKER)

        assert routes[("get", "/multi")] == routes[("put", "/multi")] == "multi"

    def test_methods_are_lowercase(self):
        assert all(method == method.lower() for method, _ in get_routes_with_attr(build_marked_app(), MARKER))

    def test_the_root_path_prefixes_every_path(self):
        routes = get_routes_with_attr(build_marked_app(root_path="/svc"), MARKER)

        assert ("get", "/svc/direct") in routes
        assert ("post", "/svc/api/things") in routes

    def test_an_unknown_attribute_matches_nothing(self):
        assert get_routes_with_attr(build_marked_app(), "_no_such_attribute") == {}


class TestRouteAttributeRegistry:

    @pytest.fixture
    def registry(self) -> RouteAttributeRegistry[str]:
        return RouteAttributeRegistry[str](build_marked_app(), MARKER)

    def test_has_routes_when_a_route_is_marked(self, registry: RouteAttributeRegistry[str]):
        assert registry.has_routes is True

    @pytest.mark.parametrize("method, path, expected", [
        ("GET", "/direct", "direct"),
        ("POST", "/api/things", "outer-post"),
        ("GET", "/api/inner/items/42", "inner-get"),
        ("PUT", "/multi", "multi"),
    ])
    def test_finds_the_marker_of_the_matching_route(
            self, registry: RouteAttributeRegistry[str], method: str, path: str, expected: str,
    ):
        assert registry.get(make_scope(method, path)) == expected

    def test_a_path_parameter_matches_any_value(self, registry: RouteAttributeRegistry[str]):
        assert registry.get(make_scope("GET", "/api/inner/items/anything-at-all")) == "inner-get"

    @pytest.mark.parametrize("method, path", [
        ("DELETE", "/direct"),
        ("GET", "/api/things"),
        ("GET", "/api/unmarked"),
        ("GET", "/nothing/here"),
        ("GET", "/items/42"),
    ])
    def test_returns_the_default_when_no_marked_route_matches(
            self, registry: RouteAttributeRegistry[str], method: str, path: str,
    ):
        assert registry.get(make_scope(method, path)) is None
        assert registry.get(make_scope(method, path), "fallback") == "fallback"

    def test_an_app_without_marked_routes_gives_an_empty_registry(self):
        registry = RouteAttributeRegistry[str](build_marked_app(), "_no_such_attribute")

        assert registry.has_routes is False
        assert registry.get(make_scope("GET", "/direct")) is None

    def test_handles_a_route_registered_on_a_plain_starlette_route(self):
        app = FastAPI()
        app.router.routes.append(Route("/plain", lambda request: PlainTextResponse("ok")))

        assert RouteAttributeRegistry[str](app, MARKER).has_routes is False
