from enum import StrEnum

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ristops_lib_core.auth.authn import public

health_router = APIRouter(tags=["health"])


class HealthStatus(StrEnum):
    OK = "ok"


class HealthResponse(BaseModel):
    """ Liveness probe payload. """
    status: HealthStatus = Field(description="Liveness status of the service.")


@health_router.get(
    "/health",
    response_model=HealthResponse,
    summary="Liveness probe",
    description=(
        "Returns as soon as the app is able to serve requests. Deliberately checks no "
        "downstream dependency: container orchestration uses it to decide whether the "
        "process is up, not whether the whole stack is."
    ),
)
@public
async def get_health() -> HealthResponse:
    """ Return a static liveness response. """
    return HealthResponse(status=HealthStatus.OK)
