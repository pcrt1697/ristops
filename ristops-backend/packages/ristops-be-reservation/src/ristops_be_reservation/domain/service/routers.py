from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query
from fastapi.params import Path

from ristops_be_reservation.domain.service.schema import (
    ServiceCreationRequest, ServiceResponse, ServiceSearchQuery,
    ServiceOpeningUpsertRequest, ServiceOpeningResponse,
    ServiceOpeningOverrideUpsertRequest, ServiceOpeningOverrideResponse,
    ServiceClosingUpsertRequest, ServiceClosingResponse,
)
from ristops_be_reservation.domain.service.service import (
    create_service, find_service_or_throw, remove_service, search_services,
    upsert_service_openings, list_service_openings,
    upsert_service_opening_overrides, list_service_opening_overrides,
    upsert_service_closings, list_service_closings,
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
    response_model=list[ServiceResponse],
)
@policy(Policy(_venue_query_resolver, "service:list"))
@sql_transactional
async def search(
        query: Annotated[ServiceSearchQuery, Query()],
) -> list[ServiceResponse]:
    """Return services for a venue matching the given filters, sorted per the query.
    Not paginated. Authorized against the venue."""
    return await search_services(query)


@service_router.post(
    "",
    response_model=ServiceResponse,
    status_code=HTTPStatus.CREATED,
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Venue not found"},
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


@service_router.delete(
    "/{service_id}",
    status_code=HTTPStatus.NO_CONTENT,
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Service not found"},
    },
)
@policy(Policy(_service_path_resolver, "service:remove"))
@sql_transactional
async def delete(
        service_id: Annotated[UUID, Path(description="Service ID")],
) -> None:
    """Delete a service by ID. Authorized against the service itself."""
    await remove_service(service_id)


@service_router.put(
    "/{service_id}/openings",
    response_model=list[ServiceOpeningResponse],
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Service not found"},
        HTTPStatus.BAD_REQUEST: {"model": ErrorResponse, "description": "Duplicate weekday in openings list"},
    },
)
@policy(Policy(_service_path_resolver, "service:edit"))
@sql_transactional
async def upsert_openings(
        service_id: Annotated[UUID, Path(description="Service ID")],
        request: list[ServiceOpeningUpsertRequest],
) -> list[ServiceOpeningResponse]:
    """Replace the full set of openings for a service with the given list: openings for
    weekdays present in the list are created or updated, openings for weekdays absent from
    the list are deleted. Authorized against the service itself."""
    openings = await upsert_service_openings(service_id, request)
    return [ServiceOpeningResponse.model_validate(opening, from_attributes=True) for opening in openings]


@service_router.get(
    "/{service_id}/openings",
    response_model=list[ServiceOpeningResponse],
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Service not found"},
    },
)
@policy(Policy(_service_path_resolver, "service:get"))
@sql_transactional
async def list_openings(
        service_id: Annotated[UUID, Path(description="Service ID")],
        include_deleted: Annotated[
            bool, Query(description="Return openings even if the service has been deleted")
        ] = False,
) -> list[ServiceOpeningResponse]:
    """Return all openings for a service. Authorized against the service itself."""
    openings = await list_service_openings(service_id, include_deleted=include_deleted)
    return [ServiceOpeningResponse.model_validate(opening, from_attributes=True) for opening in openings]


@service_router.put(
    "/{service_id}/opening-overrides",
    response_model=list[ServiceOpeningOverrideResponse],
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Service not found"},
        HTTPStatus.BAD_REQUEST: {
            "model": ErrorResponse, "description": "Duplicate or unknown id in opening overrides list",
        },
    },
)
@policy(Policy(_service_path_resolver, "service:edit"))
@sql_transactional
async def upsert_opening_overrides(
        service_id: Annotated[UUID, Path(description="Service ID")],
        request: list[ServiceOpeningOverrideUpsertRequest],
) -> list[ServiceOpeningOverrideResponse]:
    """Replace the full set of opening overrides for a service with the given list: items
    with an id update the matching row, items without an id are created, and existing rows
    absent from the list are deleted. Authorized against the service itself."""
    overrides = await upsert_service_opening_overrides(service_id, request)
    return [
        ServiceOpeningOverrideResponse.model_validate(override, from_attributes=True) for override in overrides
    ]


@service_router.get(
    "/{service_id}/opening-overrides",
    response_model=list[ServiceOpeningOverrideResponse],
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Service not found"},
    },
)
@policy(Policy(_service_path_resolver, "service:get"))
@sql_transactional
async def list_opening_overrides(
        service_id: Annotated[UUID, Path(description="Service ID")],
        include_deleted: Annotated[
            bool, Query(description="Return opening overrides even if the service has been deleted")
        ] = False,
) -> list[ServiceOpeningOverrideResponse]:
    """Return all opening overrides for a service. Authorized against the service itself."""
    overrides = await list_service_opening_overrides(service_id, include_deleted=include_deleted)
    return [
        ServiceOpeningOverrideResponse.model_validate(override, from_attributes=True) for override in overrides
    ]


@service_router.put(
    "/{service_id}/closings",
    response_model=list[ServiceClosingResponse],
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Service not found"},
        HTTPStatus.BAD_REQUEST: {"model": ErrorResponse, "description": "Duplicate or unknown id in closings list"},
    },
)
@policy(Policy(_service_path_resolver, "service:edit"))
@sql_transactional
async def upsert_closings(
        service_id: Annotated[UUID, Path(description="Service ID")],
        request: list[ServiceClosingUpsertRequest],
) -> list[ServiceClosingResponse]:
    """Replace the full set of closings for a service with the given list: items with an id
    update the matching row, items without an id are created, and existing rows absent from
    the list are deleted. Authorized against the service itself."""
    closings = await upsert_service_closings(service_id, request)
    return [ServiceClosingResponse.model_validate(closing, from_attributes=True) for closing in closings]


@service_router.get(
    "/{service_id}/closings",
    response_model=list[ServiceClosingResponse],
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Service not found"},
    },
)
@policy(Policy(_service_path_resolver, "service:get"))
@sql_transactional
async def list_closings(
        service_id: Annotated[UUID, Path(description="Service ID")],
        include_deleted: Annotated[
            bool, Query(description="Return closings even if the service has been deleted")
        ] = False,
) -> list[ServiceClosingResponse]:
    """Return all closings for a service. Authorized against the service itself."""
    closings = await list_service_closings(service_id, include_deleted=include_deleted)
    return [ServiceClosingResponse.model_validate(closing, from_attributes=True) for closing in closings]
