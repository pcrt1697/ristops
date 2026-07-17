from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query
from fastapi.params import Path

from ristops_be_reservation.domain.schedule.schema import (
    OpeningsUpsertRequest, OpeningsResponse, OpeningResponse,
    OpeningOverrideCreateRequest, OpeningOverrideUpdateRequest,
    OpeningOverrideResponse, OpeningOverridesResponse,
    ClosingCreateRequest, ClosingUpdateRequest, ClosingResponse,
    ClosingsResponse,
)
from ristops_be_reservation.domain.schedule.service import (
    upsert_service_openings, list_service_openings,
    create_service_opening_override, update_service_opening_override,
    remove_service_opening_override, list_service_opening_overrides,
    create_service_closing, update_service_closing,
    remove_service_closing, list_service_closings,
)
from ristops_lib_be.authz.policy import policy, BaseResourceResolver, Policy
from ristops_lib_core.exception import ErrorResponse
from ristops_lib_core.schema.authz import ResourceType
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
@policy(Policy(_service_path_resolver, "service:edit"))
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
@policy(Policy(_service_path_resolver, "service:get"))
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
    response_model=OpeningOverrideResponse,
    status_code=HTTPStatus.CREATED,
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Service not found"},
        HTTPStatus.CONFLICT: {"model": ErrorResponse, "description": "Venue is not accepting config changes"},
    },
)
@policy(Policy(_service_path_resolver, "service:edit"))
@sql_transactional
async def create_opening_override(
        service_id: Annotated[UUID, Path(description="Service ID")],
        request: OpeningOverrideCreateRequest,
) -> OpeningOverrideResponse:
    """Create a new opening override for a service. Authorized against the service itself."""
    override = await create_service_opening_override(service_id, request)
    return OpeningOverrideResponse.model_validate(override, from_attributes=True)


@schedule_router.patch(
    "/{service_id}/opening-overrides/{override_id}",
    response_model=OpeningOverrideResponse,
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Opening override not found"},
        HTTPStatus.CONFLICT: {"model": ErrorResponse, "description": "Venue is not accepting config changes"},
    },
)
@policy(Policy(_service_path_resolver, "service:edit"))
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
@policy(Policy(_service_path_resolver, "service:edit"))
@sql_transactional
async def delete_opening_override(
        service_id: Annotated[UUID, Path(description="Service ID")],
        override_id: Annotated[UUID, Path(description="Opening override ID")],
) -> None:
    """Delete an opening override. Authorized against the service itself."""
    await remove_service_opening_override(service_id, override_id)


@schedule_router.get(
    "/{service_id}/opening-overrides",
    response_model=OpeningOverridesResponse,
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Service not found"},
    },
)
@policy(Policy(_service_path_resolver, "service:get"))
@sql_transactional
async def get_service_opening_overrides(
        service_id: Annotated[UUID, Path(description="Service ID")],
        include_deleted: Annotated[
            bool, Query(description="Return opening overrides even if the service has been deleted")
        ] = False,
) -> OpeningOverridesResponse:
    """Return all opening overrides for a service. Authorized against the service itself."""
    overrides = await list_service_opening_overrides(service_id, include_deleted=include_deleted)
    return OpeningOverridesResponse(
        opening_overrides=[
            OpeningOverrideResponse.model_validate(override, from_attributes=True) for override in overrides
        ]
    )


@schedule_router.post(
    "/{service_id}/closings",
    response_model=ClosingResponse,
    status_code=HTTPStatus.CREATED,
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Service not found"},
        HTTPStatus.CONFLICT: {"model": ErrorResponse, "description": "Venue is not accepting config changes"},
    },
)
@policy(Policy(_service_path_resolver, "service:edit"))
@sql_transactional
async def create_closing(
        service_id: Annotated[UUID, Path(description="Service ID")],
        request: ClosingCreateRequest,
) -> ClosingResponse:
    """Create a new closing for a service. Authorized against the service itself."""
    closing = await create_service_closing(service_id, request)
    return ClosingResponse.model_validate(closing, from_attributes=True)


@schedule_router.patch(
    "/{service_id}/closings/{closing_id}",
    response_model=ClosingResponse,
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Closing not found"},
        HTTPStatus.CONFLICT: {"model": ErrorResponse, "description": "Venue is not accepting config changes"},
    },
)
@policy(Policy(_service_path_resolver, "service:edit"))
@sql_transactional
async def update_closing(
        service_id: Annotated[UUID, Path(description="Service ID")],
        closing_id: Annotated[UUID, Path(description="Closing ID")],
        request: ClosingUpdateRequest,
) -> ClosingResponse:
    """Update a closing. Only fields present in the request body are modified. Authorized
    against the service itself."""
    closing = await update_service_closing(service_id, closing_id, request)
    return ClosingResponse.model_validate(closing, from_attributes=True)


@schedule_router.delete(
    "/{service_id}/closings/{closing_id}",
    status_code=HTTPStatus.NO_CONTENT,
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Closing not found"},
        HTTPStatus.CONFLICT: {"model": ErrorResponse, "description": "Venue is not accepting config changes"},
    },
)
@policy(Policy(_service_path_resolver, "service:edit"))
@sql_transactional
async def delete_closing(
        service_id: Annotated[UUID, Path(description="Service ID")],
        closing_id: Annotated[UUID, Path(description="Closing ID")],
) -> None:
    """Delete a closing. Authorized against the service itself."""
    await remove_service_closing(service_id, closing_id)


@schedule_router.get(
    "/{service_id}/closings",
    response_model=ClosingsResponse,
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Service not found"},
    },
)
@policy(Policy(_service_path_resolver, "service:get"))
@sql_transactional
async def get_service_closings(
        service_id: Annotated[UUID, Path(description="Service ID")],
        include_deleted: Annotated[
            bool, Query(description="Return closings even if the service has been deleted")
        ] = False,
) -> ClosingsResponse:
    """Return all closings for a service. Authorized against the service itself."""
    closings = await list_service_closings(service_id, include_deleted=include_deleted)
    return ClosingsResponse(
        closings=[ClosingResponse.model_validate(closing, from_attributes=True) for closing in closings]
    )
