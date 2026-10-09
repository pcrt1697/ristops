from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query
from fastapi.params import Path

from ristops_be_reservation.domain.service.schema import (
    ClosingCreateRequest, ClosingResponse, ClosingSearchQuery, ClosingUpdateRequest,
    OpeningResponse, OpeningsResponse, OpeningsUpsertRequest, ServiceCreationRequest,
    ServiceListQuery, ServiceResponse, ServiceUpdateRequest, ServicesResponse,
)
from ristops_be_reservation.domain.service.service import (
    create_closing, create_service, find_service_or_throw, list_service_openings, list_services,
    remove_closing, remove_service, search_closings, update_closing, update_service,
    upsert_service_openings,
)
from ristops_lib_be.authz.policy import (
    policy, BaseResourceResolver, Policy, resolve_body_attribute, resolve_query_attribute,
)
from ristops_lib_core.exception import ErrorResponse
from ristops_lib_core.schema.authz import ResourceType
from ristops_lib_core.schema.pagination import Page
from ristops_lib_sql.engine import sql_transactional

_venue_body_resolver = BaseResourceResolver(ResourceType.VENUE, resolver=resolve_body_attribute)
_venue_query_resolver = BaseResourceResolver(
    ResourceType.VENUE, field="filter.venue_id", resolver=resolve_query_attribute,
)
_service_path_resolver = BaseResourceResolver(ResourceType.SERVICE)
_venue_path_resolver = BaseResourceResolver(ResourceType.VENUE)
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
        HTTPStatus.CONFLICT: {
            "model": ErrorResponse,
            "description": "Venue is not accepting config changes, or the service would be open "
                           "at the same time as another service of the venue",
        },
    },
)
@policy(Policy(_venue_body_resolver, "service:add"))
@sql_transactional
async def create(
        request: ServiceCreationRequest,
) -> ServiceResponse:
    """Create a new service under a venue. Authorized against the venue, since the service
    does not exist yet. Its hours are set separately, through the openings endpoint."""
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
        HTTPStatus.CONFLICT: {
            "model": ErrorResponse,
            "description": "Venue is not accepting config changes, or the new validity period "
                           "would make the service overlap another service of the venue",
        },
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


schedule_router = APIRouter(
    tags=["schedule"],
)


@schedule_router.put(
    "/services/{service_id}/openings",
    response_model=OpeningsResponse,
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Service not found"},
        HTTPStatus.CONFLICT: {
            "model": ErrorResponse,
            "description": "Venue is not accepting config changes, or the hours would make the "
                           "service overlap another service of the venue",
        },
    },
)
@policy(Policy(_service_path_resolver, "schedule:edit"))
@sql_transactional
async def upsert_openings(
        service_id: Annotated[UUID, Path(description="Service ID")],
        request: OpeningsUpsertRequest,
) -> OpeningsResponse:
    """Replace a service's weekly opening hours with the submitted set. Authorized against the
    service itself."""
    openings = await upsert_service_openings(service_id, request)
    return OpeningsResponse(openings=[
        OpeningResponse.model_validate(opening, from_attributes=True)
        for opening in openings
    ])


@schedule_router.get(
    "/services/{service_id}/openings",
    response_model=OpeningsResponse,
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Service not found"},
    },
)
@policy(Policy(_service_path_resolver, "schedule:list"))
@sql_transactional
async def get_service_openings(
        service_id: Annotated[UUID, Path(description="Service ID")],
        include_deleted: Annotated[
            bool, Query(description="Return the openings even if the service has been deleted")
        ] = False,
) -> OpeningsResponse:
    """Return a service's weekly opening hours. Authorized against the service itself."""
    openings = await list_service_openings(service_id, include_deleted=include_deleted)
    return OpeningsResponse(openings=[
        OpeningResponse.model_validate(opening, from_attributes=True)
        for opening in openings
    ])


@schedule_router.post(
    "/venues/{venue_id}/closings",
    response_model=ClosingResponse,
    status_code=HTTPStatus.CREATED,
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Venue or service not found"},
        HTTPStatus.CONFLICT: {
            "model": ErrorResponse, "description": "Venue is not accepting config changes",
        },
    },
)
@policy(Policy(_venue_path_resolver, "schedule:add"))
@sql_transactional
async def create_venue_closing(
        venue_id: Annotated[UUID, Path(description="Venue ID")],
        request: ClosingCreateRequest,
) -> ClosingResponse:
    """Close one or more of the venue's services over a date range. Pass every service for a
    venue-wide shutdown. Authorized against the venue itself."""
    return await create_closing(venue_id, request)


@schedule_router.get(
    "/venues/{venue_id}/closings",
    response_model=Page[ClosingResponse],
)
@policy(Policy(_venue_path_resolver, "schedule:list"))
@sql_transactional
async def get_venue_closings(
        venue_id: Annotated[UUID, Path(description="Venue ID")],
        query: Annotated[ClosingSearchQuery, Query()],
) -> Page[ClosingResponse]:
    """Return the venue's closings matching the query, paginated. Authorized against the venue."""
    return await search_closings(venue_id, query)


@schedule_router.patch(
    "/venues/{venue_id}/closings/{closing_id}",
    response_model=ClosingResponse,
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Closing or service not found"},
        HTTPStatus.CONFLICT: {
            "model": ErrorResponse,
            "description": "Venue is not accepting config changes, or shrinking the closing "
                           "would leave two services open at the same time",
        },
    },
)
@policy(Policy(_venue_path_resolver, "schedule:edit"))
@sql_transactional
async def update_venue_closing(
        venue_id: Annotated[UUID, Path(description="Venue ID")],
        closing_id: Annotated[UUID, Path(description="Closing ID")],
        request: ClosingUpdateRequest,
) -> ClosingResponse:
    """Update a closing. Authorized against the venue itself."""
    return await update_closing(venue_id, closing_id, request)


@schedule_router.delete(
    "/venues/{venue_id}/closings/{closing_id}",
    status_code=HTTPStatus.NO_CONTENT,
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Closing not found"},
        HTTPStatus.CONFLICT: {
            "model": ErrorResponse,
            "description": "Venue is not accepting config changes, or removing the closing "
                           "would leave two services open at the same time",
        },
    },
)
@policy(Policy(_venue_path_resolver, "schedule:remove"))
@sql_transactional
async def delete_venue_closing(
        venue_id: Annotated[UUID, Path(description="Venue ID")],
        closing_id: Annotated[UUID, Path(description="Closing ID")],
) -> None:
    """Delete a closing. Authorized against the venue itself."""
    await remove_closing(venue_id, closing_id)
