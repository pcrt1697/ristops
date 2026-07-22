from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query
from fastapi.params import Path

from ristops_be_reservation.domain.venue.schema import (
    VenueClosingCreateRequest, VenueClosingUpdateRequest,
    VenueClosingResponse, VenueClosingSearchQuery,
)
from ristops_be_reservation.domain.venue.service import (
    create_venue_closings, update_venue_closing,
    remove_venue_closing, search_venue_closings,
)
from ristops_lib_be.authz.policy import policy, BaseResourceResolver, Policy
from ristops_lib_core.exception import ErrorResponse
from ristops_lib_core.schema.authz import ResourceType
from ristops_lib_core.schema.pagination import Page
from ristops_lib_sql.engine import sql_transactional

_venue_path_resolver = BaseResourceResolver(ResourceType.VENUE)
venue_closing_router = APIRouter(
    prefix="/venues",
    tags=["venue-closings"],
)


@venue_closing_router.post(
    "/{venue_id}/closings",
    response_model=list[VenueClosingResponse],
    status_code=HTTPStatus.CREATED,
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Venue not found"},
        HTTPStatus.CONFLICT: {"model": ErrorResponse, "description": "Venue is not accepting config changes"},
    },
)
@policy(Policy(_venue_path_resolver, "schedule:edit"))
@sql_transactional
async def create_closing(
        venue_id: Annotated[UUID, Path(description="Venue ID")],
        request: VenueClosingCreateRequest,
) -> list[VenueClosingResponse]:
    """Create one or more venue-wide closings — one per weekday in the request (bulk, single
    transaction). Authorized against the venue itself."""
    closings = await create_venue_closings(venue_id, request)
    return [
        VenueClosingResponse.model_validate(closing, from_attributes=True)
        for closing in closings
    ]


@venue_closing_router.patch(
    "/{venue_id}/closings/{closing_id}",
    response_model=VenueClosingResponse,
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Venue closing not found"},
        HTTPStatus.CONFLICT: {"model": ErrorResponse, "description": "Venue is not accepting config changes"},
    },
)
@policy(Policy(_venue_path_resolver, "schedule:edit"))
@sql_transactional
async def update_closing(
        venue_id: Annotated[UUID, Path(description="Venue ID")],
        closing_id: Annotated[UUID, Path(description="Venue closing ID")],
        request: VenueClosingUpdateRequest,
) -> VenueClosingResponse:
    """Update a venue closing. Only fields present in the request body are modified.
    Authorized against the venue itself."""
    closing = await update_venue_closing(venue_id, closing_id, request)
    return VenueClosingResponse.model_validate(closing, from_attributes=True)


@venue_closing_router.delete(
    "/{venue_id}/closings/{closing_id}",
    status_code=HTTPStatus.NO_CONTENT,
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Venue closing not found"},
        HTTPStatus.CONFLICT: {"model": ErrorResponse, "description": "Venue is not accepting config changes"},
    },
)
@policy(Policy(_venue_path_resolver, "schedule:edit"))
@sql_transactional
async def delete_closing(
        venue_id: Annotated[UUID, Path(description="Venue ID")],
        closing_id: Annotated[UUID, Path(description="Venue closing ID")],
) -> None:
    """Delete a venue closing. Authorized against the venue itself."""
    await remove_venue_closing(venue_id, closing_id)


@venue_closing_router.get(
    "/{venue_id}/closings",
    response_model=Page[VenueClosingResponse],
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Venue not found"},
    },
)
@policy(Policy(_venue_path_resolver, "schedule:list"))
@sql_transactional
async def get_venue_closings(
        venue_id: Annotated[UUID, Path(description="Venue ID")],
        query: Annotated[VenueClosingSearchQuery, Query()],
) -> Page[VenueClosingResponse]:
    """Return a paginated, date-range-filtered page of venue-wide closings for a venue.
    Authorized against the venue itself."""
    return await search_venue_closings(venue_id, query)
