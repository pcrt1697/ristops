import logging
from http import HTTPStatus
from uuid import UUID, uuid4

from fastapi import HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, ScalarResult, ColumnElement

from ristops_be_venue.domain.venue.entities import VenueEntity
from ristops_be_venue.domain.venue.schema import (
    VenueCreationRequest, VenueUpdateRequest, VenueResponse,
    VenueSearchFilter, VenueSearchQuery,
)
from ristops_be_venue.services.resource import publish_resource_created_event, publish_resource_deleted_event
from ristops_lib_core.schema.authz import ResourceType, ListUserResourceGrantsResponse
from ristops_lib_core.schema.pagination import Page
from ristops_lib_sql.engine import get_sql_session
from ristops_lib_sql.search import SearchQueryExecutor

_logger = logging.getLogger(__name__)


class VenueSearchScope(BaseModel):
    """Visibility scope ANDed into a venue search to limit results to the user's venues."""

    venue_ids: list[str] | None = Field(
        description="Venues the user may see. `None` is unrestricted; an empty list is no access.",
    )

    @classmethod
    def from_grants(cls, venue_grants: ListUserResourceGrantsResponse | None) -> "VenueSearchScope":
        """Build a scope from authz grants; `None` grants mean unrestricted access."""
        if venue_grants is None:
            return VenueSearchScope(venue_ids=None)
        venue_ids = [grant.resource.resource_id for grant in venue_grants.grants]
        return VenueSearchScope(venue_ids=venue_ids)


def _build_venue_conditions(
        venue_filter: VenueSearchFilter,
        venue_scope: VenueSearchScope,
) -> list[ColumnElement[bool]]:
    """Build the WHERE conditions from the user filter and the visibility scope."""
    where_conditions = []

    if venue_scope.venue_ids is not None:
        where_conditions.append(VenueEntity.id.in_(venue_scope.venue_ids))

    if venue_filter.name is not None:
        where_conditions.append(
            VenueEntity.name.ilike(f"%{venue_filter.name}%")
        )

    return where_conditions


search_query_executor = SearchQueryExecutor[
    VenueSearchQuery,
    VenueSearchScope,
    VenueEntity,
    VenueResponse
](
    entity_class=VenueEntity,
    response_class=VenueResponse,
    condition_builder=_build_venue_conditions,
)


async def create_venue(request: VenueCreationRequest) -> VenueEntity:
    """Create a new venue."""
    session = get_sql_session()
    venue = VenueEntity(
        id=uuid4(),
        name=request.name,
        address=request.address,
        description=request.description,
    )
    session.add(venue)
    await session.flush()
    await session.refresh(venue)
    await publish_resource_created_event(
        str(venue.id),
        ResourceType.VENUE,
        "*",
        ResourceType.APP,
    )
    _logger.info("Created venue: %s", venue.id)
    return venue


async def find_venue_or_throw(venue_id: UUID) -> VenueEntity:
    """Return the venue with the given ID, or raise HTTP 404."""
    return await _find_venue_by_or_throw(VenueEntity.id == str(venue_id))


async def update_venue(venue_id: UUID, request: VenueUpdateRequest) -> VenueEntity:
    """Update a venue. Only fields present in the request body are modified."""
    venue = await find_venue_or_throw(venue_id)
    fields_to_update = request.model_fields_set

    if "name" in fields_to_update and request.name is not None:
        venue.name = request.name
    if "address" in fields_to_update and request.address is not None:
        venue.address = request.address
    if "description" in fields_to_update:
        venue.description = request.description

    session = get_sql_session()
    await session.flush()
    await session.refresh(venue)
    _logger.info("Updated venue: %s", venue.id)
    return venue


async def remove_venue(venue_id: UUID) -> None:
    """Delete the venue with the given ID. Raises HTTP 404 if not found."""
    venue = await find_venue_or_throw(venue_id)
    session = get_sql_session()
    await session.delete(venue)
    await publish_resource_deleted_event(str(venue_id), ResourceType.VENUE)
    _logger.info("Deleted venue: %s", venue_id)


async def _find_venue_by(query: ColumnElement[bool]) -> VenueEntity | None:
    """Return the first venue matching the given query, or None."""
    session = get_sql_session()
    result: ScalarResult[VenueEntity] = await session.scalars(
        select(VenueEntity).where(query).limit(1)
    )
    return result.one_or_none()


async def _find_venue_by_or_throw(query: ColumnElement[bool]) -> VenueEntity:
    """Return the first venue matching the given query, or raise HTTP 404."""
    venue = await _find_venue_by(query)
    if venue is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Venue not found",
        )
    return venue


async def search_venue(
        query: VenueSearchQuery,
        scope: VenueSearchScope
) -> Page[VenueResponse]:
    """Return a page of venues matching the given query."""
    return await search_query_executor.execute(query, scope)
