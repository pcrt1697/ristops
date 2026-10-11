import pytest
from fastapi import FastAPI

from helpers import make_client
from ristops_lib_core.app.health import HealthResponse, HealthStatus, get_health, health_router
from ristops_lib_core.auth.authn import IS_PUBLIC


def test_the_endpoint_is_public():
    assert getattr(get_health, IS_PUBLIC) is True


def test_the_response_model_only_allows_the_ok_status():
    assert HealthResponse(status=HealthStatus.OK).model_dump(mode="json") == {"status": "ok"}


@pytest.mark.anyio
async def test_reports_ok_when_the_router_is_included_in_an_app():
    app = FastAPI()
    app.include_router(health_router)

    async with make_client(app) as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_the_route_is_tagged_and_documented():
    app = FastAPI()
    app.include_router(health_router)

    operation = app.openapi()["paths"]["/health"]["get"]

    assert operation["tags"] == ["health"]
    assert operation["summary"] == "Liveness probe"
