from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query
from fastapi.params import Path

from ristops_be_reservation.domain.service.schema import (
    ServiceCreationRequest, ServiceUpdateRequest, ServiceResponse, ServicesResponse, ServiceListQuery,
)
from ristops_be_reservation.domain.service.service import (
    create_service, find_service_or_throw, remove_service, list_services, update_service,
)
from ristops_lib_be.authz.policy import (
    policy, BaseResourceResolver, Policy, resolve_body_attribute, resolve_query_attribute,
)
from ristops_lib_core.exception import ErrorResponse
from ristops_lib_core.schema.authz import ResourceType
from ristops_lib_sql.engine import sql_transactional

_venue_body_resolver = BaseResourceResolver(ResourceType.VENUE, resolver=resolve_body_attribute)
_venue_query_resolver = BaseResourceResolver(
    ResourceType.VENUE, field="filter.venue_id", resolver=resolve_query_attribute,
)
_service_path_resolver = BaseResourceResolver(ResourceType.SERVICE)
service_router = APIRouter(
    prefix="/services",
    tags=["services"],
)


@service_router.get(
    "",
    response_model=ServicesResponse,
)
@policy(Policy(_venue_query_resolver, "service:list"))
@sql_transactional
async def get_services(
        query: Annotated[ServiceListQuery, Query()],
) -> ServicesResponse:
    """Return services for a venue matching the given filters, sorted per the query.
    Not paginated. Authorized against the venue."""
    services = await list_services(query)
    return ServicesResponse(services=services)


@service_router.post(
    "",
    response_model=ServiceResponse,
    status_code=HTTPStatus.CREATED,
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Venue not found"},
        HTTPStatus.CONFLICT: {"model": ErrorResponse, "description": "Venue is not accepting config changes"},
    },
)
@policy(Policy(_venue_body_resolver, "service:add"))
@sql_transactional
async def create(
        request: ServiceCreationRequest,
) -> ServiceResponse:
    """Create a new service under a venue. Authorized against the venue, since the service
    does not exist yet."""
    service = await create_service(request)
    return ServiceResponse.model_validate(service, from_attributes=True)


@service_router.get(
    "/{service_id}",
    response_model=ServiceResponse,
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Service not found"},
    },
)
@policy(Policy(_service_path_resolver, "service:get"))
@sql_transactional
async def get(
        service_id: Annotated[UUID, Path(description="Service ID")],
        include_deleted: Annotated[
            bool, Query(description="Return the service even if it has been deleted")
        ] = False,
) -> ServiceResponse:
    """Return a service by ID. Authorized against the service itself, inheriting grants from
    its venue via the ReBAC hierarchy."""
    service = await find_service_or_throw(service_id, include_deleted=include_deleted)
    return ServiceResponse.model_validate(service, from_attributes=True)


@service_router.patch(
    "/{service_id}",
    response_model=ServiceResponse,
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Service not found"},
        HTTPStatus.CONFLICT: {"model": ErrorResponse, "description": "Venue is not accepting config changes"},
    },
)
@policy(Policy(_service_path_resolver, "service:edit"))
@sql_transactional
async def update(
        service_id: Annotated[UUID, Path(description="Service ID")],
        request: ServiceUpdateRequest,
) -> ServiceResponse:
    """Update a service. Only fields present in the request body are modified. Authorized
    against the service itself."""
    service = await update_service(service_id, request)
    return ServiceResponse.model_validate(service, from_attributes=True)


@service_router.delete(
    "/{service_id}",
    status_code=HTTPStatus.NO_CONTENT,
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Service not found"},
        HTTPStatus.CONFLICT: {"model": ErrorResponse, "description": "Venue is not accepting config changes"},
    },
)
@policy(Policy(_service_path_resolver, "service:remove"))
@sql_transactional
async def delete(
        service_id: Annotated[UUID, Path(description="Service ID")],
) -> None:
    """Delete a service by ID. Authorized against the service itself."""
    await remove_service(service_id)
