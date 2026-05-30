from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter
from fastapi.params import Path

from ristops_be_venue.domain.venue.schema import (
    VenueCreationRequest, VenueUpdateRequest, VenueResponse,
)
from ristops_be_venue.domain.venue.service import (
    create_venue, find_venue_or_throw, update_venue, remove_venue,
)
from ristops_lib_be.authz.policy import policy, BaseResourceResolver, Policy
from ristops_lib_core.exception import ErrorResponse
from ristops_lib_core.schema.authz import ResourceType
from ristops_lib_sql.engine import sql_transactional

_venue_path_resolver = BaseResourceResolver(ResourceType.VENUE)
venue_router = APIRouter(
    prefix="/venue",
    tags=["venue"],
)


@venue_router.post(
    "",
    response_model=VenueResponse,
    status_code=HTTPStatus.CREATED,
)
@policy()
@sql_transactional
async def create(request: VenueCreationRequest) -> VenueResponse:
    """Create a new venue."""
    venue = await create_venue(request)
    return VenueResponse.model_validate(venue, from_attributes=True)


@venue_router.get(
    "/{venue_id}",
    response_model=VenueResponse,
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Venue not found"},
    },
)
@policy(Policy(_venue_path_resolver, "venue~get"))
@sql_transactional
async def get(
        venue_id: Annotated[UUID, Path(description="Venue ID")],
) -> VenueResponse:
    """Return a venue by ID."""
    venue = await find_venue_or_throw(venue_id)
    return VenueResponse.model_validate(venue, from_attributes=True)


@venue_router.patch(
    "/{venue_id}",
    response_model=VenueResponse,
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Venue not found"},
    },
)
@policy(Policy(_venue_path_resolver, "venue~edit"))
@sql_transactional
async def update(
        venue_id: Annotated[UUID, Path(description="Venue ID")],
        request: VenueUpdateRequest,
) -> VenueResponse:
    """Update a venue. Only fields present in the request body are modified."""
    venue = await update_venue(venue_id, request)
    return VenueResponse.model_validate(venue, from_attributes=True)


@venue_router.delete(
    "/{venue_id}",
    status_code=HTTPStatus.NO_CONTENT,
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Venue not found"},
    },
)
@policy(Policy(_venue_path_resolver, "venue~remove"))
@sql_transactional
async def delete(
        venue_id: Annotated[UUID, Path(description="Venue ID")],
) -> None:
    """Delete a venue by ID."""
    await remove_venue(venue_id)
