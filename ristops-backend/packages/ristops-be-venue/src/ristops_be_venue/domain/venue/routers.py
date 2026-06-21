from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query
from fastapi.params import Path, Depends

from ristops_be_venue.domain.venue.schema import (
    VenueCreationRequest, VenueUpdateRequest, VenueResponse, VenueSearchQuery,
)
from ristops_be_venue.domain.venue.service import (
    create_venue, find_venue_or_throw, update_venue, remove_venue, search_venue, VenueSearchScope,
)
from ristops_be_venue.services.authz import authz_client_factory
from ristops_lib_be.authz.client import AuthorizationResourceGrantsFetcher
from ristops_lib_be.authz.policy import policy, BaseResourceResolver, Policy, resolve_static_resource
from ristops_lib_core.exception import ErrorResponse
from ristops_lib_core.schema.authz import ResourceType, ListUserResourceGrantsResponse
from ristops_lib_core.schema.pagination import Page
from ristops_lib_sql.engine import sql_transactional

_venue_path_resolver = BaseResourceResolver(ResourceType.VENUE)
venue_router = APIRouter(
    prefix="/venue",
    tags=["venue"],
)


@venue_router.get(
    "",
    response_model=Page[VenueResponse],
)
@policy()
@sql_transactional
async def list_venues(
        query: Annotated[VenueSearchQuery, Query()],
        venue_grants: Annotated[
            ListUserResourceGrantsResponse,
            Depends(
                AuthorizationResourceGrantsFetcher(
                    authz_client_factory,
                    ResourceType.VENUE,
                    "venue~get",
                    override_policies=(Policy(resolve_static_resource("*", ResourceType.APP), "venue~list"),)
                )
            )
        ]
) -> Page[VenueResponse]:
    """
    Return a paginated, filtered, sorted list of venues.
    Results are filtered base on venues the user has access to.
    """
    scope = VenueSearchScope.from_grants(venue_grants)
    return await search_venue(query, scope)


@venue_router.post(
    "",
    response_model=VenueResponse,
    status_code=HTTPStatus.CREATED,
)
@policy(Policy(resolve_static_resource("*", ResourceType.APP), "venue~add"))
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
