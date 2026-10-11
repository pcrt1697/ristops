import pytest
from fastapi import APIRouter, FastAPI
from pydantic import BaseModel

from helpers import make_client
from ristops_lib_core.app.openapi import OpenAPIConfiguration
from ristops_lib_core.auth.authn import public


class Payload(BaseModel):
    name: str


def build_app(bearer_auth: bool = True, **app_kwargs) -> FastAPI:
    app = FastAPI(title="Demo", version="2.0", **app_kwargs)
    router = APIRouter(prefix="/api")

    @router.get("/open")
    @public
    async def open_route() -> dict:
        return {}

    @router.post("/closed")
    async def closed_route(payload: Payload) -> Payload:
        return payload

    app.include_router(router)

    @app.get("/direct-open")
    @public
    async def direct_open() -> dict:
        return {}

    @app.get("/direct-closed")
    async def direct_closed() -> dict:
        return {}

    app.openapi = OpenAPIConfiguration(app, bearer_auth)
    return app


def operation(schema: dict, path: str, method: str) -> dict:
    return schema["paths"][path][method]


def test_keeps_the_title_and_version_of_the_app():
    schema = build_app().openapi()

    assert schema["info"]["title"] == "Demo"
    assert schema["info"]["version"] == "2.0"


def test_declares_the_bearer_scheme_when_enabled():
    schema = build_app().openapi()

    assert schema["components"]["securitySchemes"] == {
        "BearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"},
    }


def test_does_not_declare_the_scheme_when_disabled():
    schema = build_app(bearer_auth=False).openapi()

    assert "securitySchemes" not in schema.get("components", {})


def test_public_routes_have_an_explicitly_empty_security_requirement():
    schema = build_app().openapi()

    assert operation(schema, "/api/open", "get")["security"] == []
    assert operation(schema, "/direct-open", "get")["security"] == []


def test_every_other_route_requires_the_bearer_token():
    schema = build_app().openapi()

    assert operation(schema, "/api/closed", "post")["security"] == [{"BearerAuth": []}]
    assert operation(schema, "/direct-closed", "get")["security"] == [{"BearerAuth": []}]


def test_routes_included_through_a_prefixed_router_are_found_under_their_full_path():
    schema = build_app().openapi()

    assert {"/api/open", "/api/closed", "/direct-open", "/direct-closed"} <= set(schema["paths"])


def test_works_with_a_root_path():
    schema = build_app(root_path="/svc").openapi()

    assert operation(schema, "/api/open", "get")["security"] == []
    assert operation(schema, "/api/closed", "post")["security"] == [{"BearerAuth": []}]


def test_each_call_returns_an_equal_schema():
    app = build_app()

    assert app.openapi() == app.openapi()


@pytest.mark.anyio
async def test_serves_the_schema_through_the_openapi_url():
    async with make_client(build_app()) as client:
        response = await client.get("/openapi.json")

    assert response.status_code == 200
    assert "BearerAuth" in response.json()["components"]["securitySchemes"]


@pytest.mark.xfail(strict=True, raises=KeyError, reason="OpenAPIConfiguration assumes the schema has components")
def test_an_app_without_any_schema_component_still_gets_the_bearer_scheme():
    app = FastAPI()

    @app.get("/plain")
    async def plain() -> dict:
        return {}

    app.openapi = OpenAPIConfiguration(app, True)

    assert "BearerAuth" in app.openapi()["components"]["securitySchemes"]
