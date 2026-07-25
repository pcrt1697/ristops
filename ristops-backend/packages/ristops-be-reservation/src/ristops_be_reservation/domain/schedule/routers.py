from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query
from fastapi.params import Path

from ristops_be_reservation.domain.schedule.schema import (
    OpeningsUpsertRequest, OpeningsResponse, OpeningResponse,
    OpeningOverrideCreateRequest, OpeningOverrideUpdateRequest,
    OpeningOverrideResponse, OpeningOverrideSearchQuery,
    ServiceClosingCreateRequest, ServiceClosingUpdateRequest, ServiceClosingResponse,
    ServiceClosingSearchQuery,
    CapacityOverrideCreateRequest, CapacityOverrideUpdateRequest,
    CapacityOverrideResponse, CapacityOverrideSearchQuery,
    ConflictQuery, ConflictsResponse,
)
from ristops_be_reservation.domain.schedule.service import (
    upsert_service_openings, list_service_openings,
    create_service_opening_overrides, update_service_opening_override,
    remove_service_opening_override, search_service_opening_overrides,
    create_service_closings, update_service_closing,
    remove_service_closing, search_service_closings,
    create_service_capacity_overrides, update_service_capacity_override,
    remove_service_capacity_override, search_service_capacity_overrides,
    find_service_opening_override_conflicts_for, find_service_closing_conflicts_for,
    find_service_capacity_override_conflicts_for,
)
from ristops_lib_be.authz.policy import policy, BaseResourceResolver, Policy
from ristops_lib_core.exception import ErrorResponse
from ristops_lib_core.schema.authz import ResourceType
from ristops_lib_core.schema.pagination import Page
from ristops_lib_sql.engine import sql_transactional

_service_path_resolver = BaseResourceResolver(ResourceType.SERVICE)
schedule_router = APIRouter(
    prefix="/services",
    tags=["services"],
)


@schedule_router.put(
    "/{service_id}/openings",
    response_model=OpeningsResponse,
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Service not found"},
        HTTPStatus.CONFLICT: {"model": ErrorResponse, "description": "Venue is not accepting config changes"},
        HTTPStatus.UNPROCESSABLE_ENTITY: {
            "model": ErrorResponse, "description": "Duplicate weekday in openings list",
        },
    },
)
@policy(Policy(_service_path_resolver, "schedule:edit"))
@sql_transactional
async def upsert_openings(
        service_id: Annotated[UUID, Path(description="Service ID")],
        request: OpeningsUpsertRequest,
) -> OpeningsResponse:
    """Replace the full set of openings for a service with the given list: openings for
    weekdays present in the list are created or updated, openings for weekdays absent from
    the list are deleted. Authorized against the service itself."""
    openings = await upsert_service_openings(service_id, request)
    return OpeningsResponse(
        openings=[OpeningResponse.model_validate(opening, from_attributes=True) for opening in openings]
    )


@schedule_router.get(
    "/{service_id}/openings",
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
            bool, Query(description="Return openings even if the service has been deleted")
        ] = False,
) -> OpeningsResponse:
    """Return all openings for a service. Authorized against the service itself."""
    openings = await list_service_openings(service_id, include_deleted=include_deleted)
    return OpeningsResponse(
        openings=[OpeningResponse.model_validate(opening, from_attributes=True) for opening in openings]
    )


@schedule_router.post(
    "/{service_id}/opening-overrides",
    response_model=list[OpeningOverrideResponse],
    status_code=HTTPStatus.CREATED,
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Service not found"},
        HTTPStatus.CONFLICT: {
            "model": ErrorResponse,
            "description": "Venue is not accepting config changes, or the period conflicts with "
                           "an existing opening override",
        },
    },
)
@policy(Policy(_service_path_resolver, "schedule:add"))
@sql_transactional
async def create_opening_override(
        service_id: Annotated[UUID, Path(description="Service ID")],
        request: OpeningOverrideCreateRequest,
) -> list[OpeningOverrideResponse]:
    """Create one or more opening overrides for a service — one per weekday in the request
    (bulk, single transaction). Authorized against the service itself."""
    overrides = await create_service_opening_overrides(service_id, request)
    return [
        OpeningOverrideResponse.model_validate(override, from_attributes=True)
        for override in overrides
    ]


@schedule_router.patch(
    "/{service_id}/opening-overrides/{override_id}",
    response_model=OpeningOverrideResponse,
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Opening override not found"},
        HTTPStatus.CONFLICT: {
            "model": ErrorResponse,
            "description": "Venue is not accepting config changes, or the new period conflicts "
                           "with an existing opening override",
        },
    },
)
@policy(Policy(_service_path_resolver, "schedule:edit"))
@sql_transactional
async def update_opening_override(
        service_id: Annotated[UUID, Path(description="Service ID")],
        override_id: Annotated[UUID, Path(description="Opening override ID")],
        request: OpeningOverrideUpdateRequest,
) -> OpeningOverrideResponse:
    """Update an opening override. Only fields present in the request body are modified.
    Authorized against the service itself."""
    override = await update_service_opening_override(service_id, override_id, request)
    return OpeningOverrideResponse.model_validate(override, from_attributes=True)


@schedule_router.delete(
    "/{service_id}/opening-overrides/{override_id}",
    status_code=HTTPStatus.NO_CONTENT,
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Opening override not found"},
        HTTPStatus.CONFLICT: {"model": ErrorResponse, "description": "Venue is not accepting config changes"},
    },
)
@policy(Policy(_service_path_resolver, "schedule:remove"))
@sql_transactional
async def delete_opening_override(
        service_id: Annotated[UUID, Path(description="Service ID")],
        override_id: Annotated[UUID, Path(description="Opening override ID")],
) -> None:
    """Delete an opening override. Authorized against the service itself."""
    await remove_service_opening_override(service_id, override_id)


@schedule_router.get(
    "/{service_id}/opening-overrides/conflicts",
    response_model=ConflictsResponse,
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Service not found"},
    },
)
@policy(Policy(_service_path_resolver, "schedule:list"))
@sql_transactional
async def get_opening_override_conflicts(
        service_id: Annotated[UUID, Path(description="Service ID")],
        query: Annotated[ConflictQuery, Query()],
) -> ConflictsResponse:
    """Read-only preview of which existing opening overrides a candidate period+weekdays would
    conflict with (what a create would 409 on). Authorized against the service itself."""
    return await find_service_opening_override_conflicts_for(service_id, query)


@schedule_router.get(
    "/{service_id}/opening-overrides",
    response_model=Page[OpeningOverrideResponse],
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Service not found"},
    },
)
@policy(Policy(_service_path_resolver, "schedule:list"))
@sql_transactional
async def get_service_opening_overrides(
        service_id: Annotated[UUID, Path(description="Service ID")],
        query: Annotated[OpeningOverrideSearchQuery, Query()],
) -> Page[OpeningOverrideResponse]:
    """Return a paginated, date-range-filtered page of opening overrides for a service.
    Authorized against the service itself."""
    return await search_service_opening_overrides(service_id, query)


@schedule_router.post(
    "/{service_id}/closings",
    response_model=list[ServiceClosingResponse],
    status_code=HTTPStatus.CREATED,
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Service not found"},
        HTTPStatus.CONFLICT: {
            "model": ErrorResponse,
            "description": "Venue is not accepting config changes, or the period conflicts with "
                           "an existing service closing or venue closing",
        },
    },
)
@policy(Policy(_service_path_resolver, "schedule:add"))
@sql_transactional
async def create_closing(
        service_id: Annotated[UUID, Path(description="Service ID")],
        request: ServiceClosingCreateRequest,
) -> list[ServiceClosingResponse]:
    """Create one or more closings for a service — one per weekday in the request (bulk,
    single transaction). Authorized against the service itself."""
    closings = await create_service_closings(service_id, request)
    return [
        ServiceClosingResponse.model_validate(closing, from_attributes=True)
        for closing in closings
    ]


@schedule_router.patch(
    "/{service_id}/closings/{closing_id}",
    response_model=ServiceClosingResponse,
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Closing not found"},
        HTTPStatus.CONFLICT: {
            "model": ErrorResponse,
            "description": "Venue is not accepting config changes, or the new period conflicts "
                           "with an existing service closing or venue closing",
        },
    },
)
@policy(Policy(_service_path_resolver, "schedule:edit"))
@sql_transactional
async def update_closing(
        service_id: Annotated[UUID, Path(description="Service ID")],
        closing_id: Annotated[UUID, Path(description="Closing ID")],
        request: ServiceClosingUpdateRequest,
) -> ServiceClosingResponse:
    """Update a closing. Only fields present in the request body are modified. Authorized
    against the service itself."""
    closing = await update_service_closing(service_id, closing_id, request)
    return ServiceClosingResponse.model_validate(closing, from_attributes=True)


@schedule_router.delete(
    "/{service_id}/closings/{closing_id}",
    status_code=HTTPStatus.NO_CONTENT,
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Closing not found"},
        HTTPStatus.CONFLICT: {"model": ErrorResponse, "description": "Venue is not accepting config changes"},
    },
)
@policy(Policy(_service_path_resolver, "schedule:remove"))
@sql_transactional
async def delete_closing(
        service_id: Annotated[UUID, Path(description="Service ID")],
        closing_id: Annotated[UUID, Path(description="Closing ID")],
) -> None:
    """Delete a closing. Authorized against the service itself."""
    await remove_service_closing(service_id, closing_id)


@schedule_router.get(
    "/{service_id}/closings",
    response_model=Page[ServiceClosingResponse],
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Service not found"},
    },
)
@policy(Policy(_service_path_resolver, "schedule:list"))
@sql_transactional
async def get_service_closings(
        service_id: Annotated[UUID, Path(description="Service ID")],
        query: Annotated[ServiceClosingSearchQuery, Query()],
) -> Page[ServiceClosingResponse]:
    """Return a paginated, date-range-filtered page of closings for a service.
    Authorized against the service itself."""
    return await search_service_closings(service_id, query)


@schedule_router.get(
    "/{service_id}/closings/conflicts",
    response_model=ConflictsResponse,
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Service not found"},
    },
)
@policy(Policy(_service_path_resolver, "schedule:list"))
@sql_transactional
async def get_service_closing_conflicts(
        service_id: Annotated[UUID, Path(description="Service ID")],
        query: Annotated[ConflictQuery, Query()],
) -> ConflictsResponse:
    """Read-only preview of which existing service closings (this service) or venue closings (its
    venue) a candidate period+weekdays would conflict with. Authorized against the service itself."""
    return await find_service_closing_conflicts_for(service_id, query)


@schedule_router.post(
    "/{service_id}/capacity-overrides",
    response_model=list[CapacityOverrideResponse],
    status_code=HTTPStatus.CREATED,
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Service not found"},
        HTTPStatus.CONFLICT: {
            "model": ErrorResponse,
            "description": "Venue is not accepting config changes, or the period conflicts with "
                           "an existing capacity override",
        },
    },
)
@policy(Policy(_service_path_resolver, "schedule:add"))
@sql_transactional
async def create_capacity_override(
        service_id: Annotated[UUID, Path(description="Service ID")],
        request: CapacityOverrideCreateRequest,
) -> list[CapacityOverrideResponse]:
    """Create one or more capacity overrides for a service — one per weekday in the request
    (bulk, single transaction). Authorized against the service itself."""
    capacity_overrides = await create_service_capacity_overrides(service_id, request)
    return [
        CapacityOverrideResponse.model_validate(capacity_override, from_attributes=True)
        for capacity_override in capacity_overrides
    ]


@schedule_router.patch(
    "/{service_id}/capacity-overrides/{capacity_override_id}",
    response_model=CapacityOverrideResponse,
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Capacity override not found"},
        HTTPStatus.CONFLICT: {
            "model": ErrorResponse,
            "description": "Venue is not accepting config changes, or the new period conflicts "
                           "with an existing capacity override",
        },
    },
)
@policy(Policy(_service_path_resolver, "schedule:edit"))
@sql_transactional
async def update_capacity_override(
        service_id: Annotated[UUID, Path(description="Service ID")],
        capacity_override_id: Annotated[UUID, Path(description="Capacity override ID")],
        request: CapacityOverrideUpdateRequest,
) -> CapacityOverrideResponse:
    """Update a capacity override. Only fields present in the request body are modified.
    Authorized against the service itself."""
    capacity_override = await update_service_capacity_override(service_id, capacity_override_id, request)
    return CapacityOverrideResponse.model_validate(capacity_override, from_attributes=True)


@schedule_router.delete(
    "/{service_id}/capacity-overrides/{capacity_override_id}",
    status_code=HTTPStatus.NO_CONTENT,
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Capacity override not found"},
        HTTPStatus.CONFLICT: {"model": ErrorResponse, "description": "Venue is not accepting config changes"},
    },
)
@policy(Policy(_service_path_resolver, "schedule:remove"))
@sql_transactional
async def delete_capacity_override(
        service_id: Annotated[UUID, Path(description="Service ID")],
        capacity_override_id: Annotated[UUID, Path(description="Capacity override ID")],
) -> None:
    """Delete a capacity override. Authorized against the service itself."""
    await remove_service_capacity_override(service_id, capacity_override_id)


@schedule_router.get(
    "/{service_id}/capacity-overrides",
    response_model=Page[CapacityOverrideResponse],
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Service not found"},
    },
)
@policy(Policy(_service_path_resolver, "schedule:list"))
@sql_transactional
async def get_service_capacity_overrides(
        service_id: Annotated[UUID, Path(description="Service ID")],
        query: Annotated[CapacityOverrideSearchQuery, Query()],
) -> Page[CapacityOverrideResponse]:
    """Return a paginated, date-range-filtered page of capacity overrides for a service.
    Authorized against the service itself."""
    return await search_service_capacity_overrides(service_id, query)


@schedule_router.get(
    "/{service_id}/capacity-overrides/conflicts",
    response_model=ConflictsResponse,
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Service not found"},
    },
)
@policy(Policy(_service_path_resolver, "schedule:list"))
@sql_transactional
async def get_capacity_override_conflicts(
        service_id: Annotated[UUID, Path(description="Service ID")],
        query: Annotated[ConflictQuery, Query()],
) -> ConflictsResponse:
    """Read-only preview of which existing capacity overrides a candidate period+weekdays would
    conflict with (what a create would 409 on). Authorized against the service itself."""
    return await find_service_capacity_override_conflicts_for(service_id, query)
