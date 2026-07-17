import logging
from http import HTTPStatus
from uuid import UUID, uuid4

from fastapi import HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, ScalarResult, ColumnElement

from ristops_be_venue.domain.models import VenueStatus, VenueActionType
from ristops_be_venue.domain.venue.entities import VenueEntity
from ristops_be_venue.domain.venue.schema import (
    VenueCreationRequest, VenueUpdateRequest, VenueResponse,
    VenueSearchFilter, VenueSearchQuery,
)
from ristops_be_venue.services.resource import publish_resource_created_event
from ristops_be_venue.services.venue_events import (
    publish_venue_created_event, publish_venue_updated_event,
)
from ristops_lib_core.schema.authz import ResourceType, ListUserResourceGrantsResponse
from ristops_lib_core.schema.pagination import Page
from ristops_lib_sql.engine import get_sql_session
from ristops_lib_sql.search import PaginatedSearchQueryExecutor

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


search_query_executor = PaginatedSearchQueryExecutor[
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
    """Create a new venue. Starts out PENDING: no owner assigned, no config yet."""
    session = get_sql_session()
    venue = VenueEntity(
        id=uuid4(),
        name=request.name,
        address=request.address,
        description=request.description,
        timezone=request.timezone,
        status=VenueStatus.PENDING,
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
    await publish_venue_created_event(str(venue.id), venue.timezone, VenueStatus(venue.status))
    _logger.info("Created venue: %s", venue.id)
    return venue


async def find_venue_or_throw(venue_id: UUID) -> VenueEntity:
    """Return the venue with the given ID, or raise HTTP 404."""
    return await _find_venue_by_or_throw(VenueEntity.id == str(venue_id))


async def update_venue(venue_id: UUID, request: VenueUpdateRequest) -> VenueEntity:
    """Update a venue. Only fields present in the request body are modified. Status is not
    settable here — it only changes via activate/close/disable/enable."""
    venue = await find_venue_or_throw(venue_id)
    fields_to_update = request.model_fields_set

    if "name" in fields_to_update and request.name is not None:
        venue.name = request.name
    if "address" in fields_to_update and request.address is not None:
        venue.address = request.address
    if "description" in fields_to_update:
        venue.description = request.description
    if "timezone" in fields_to_update and request.timezone is not None:
        venue.timezone = request.timezone

    session = get_sql_session()
    await session.flush()
    await session.refresh(venue)
    await publish_venue_updated_event(str(venue.id), venue.timezone, VenueStatus(venue.status))
    _logger.info("Updated venue: %s", venue.id)
    return venue


async def activate_venue(venue_id: UUID) -> VenueEntity:
    """Activate a venue: owner action, valid from PENDING (first launch) or CLOSED (reopen)."""
    venue = await find_venue_or_throw(venue_id)
    if VenueStatus(venue.status) not in (VenueStatus.PENDING, VenueStatus.CLOSED):
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail=f"Cannot activate a venue with status {venue.status}",
        )
    return await _set_venue_status(venue, VenueStatus.ACTIVE)


async def close_venue(venue_id: UUID) -> VenueEntity:
    """Close a venue: owner action, valid only from ACTIVE. Soft — config and ACL grants are
    preserved so the owner can reopen without data loss."""
    venue = await find_venue_or_throw(venue_id)
    if VenueStatus(venue.status) != VenueStatus.ACTIVE:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail=f"Cannot close a venue with status {venue.status}",
        )
    return await _set_venue_status(venue, VenueStatus.CLOSED)


async def disable_venue(venue_id: UUID) -> VenueEntity:
    """Disable a venue: app-admin action, valid from PENDING or ACTIVE. The owner is fully
    locked out while DISABLED — only an admin can move it out."""
    venue = await find_venue_or_throw(venue_id)
    if VenueStatus(venue.status) not in (VenueStatus.PENDING, VenueStatus.ACTIVE):
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail=f"Cannot disable a venue with status {venue.status}",
        )
    return await _set_venue_status(venue, VenueStatus.DISABLED)


async def enable_venue(venue_id: UUID) -> VenueEntity:
    """Re-enable a venue: app-admin action, valid only from DISABLED."""
    venue = await find_venue_or_throw(venue_id)
    if VenueStatus(venue.status) != VenueStatus.DISABLED:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail=f"Cannot enable a venue with status {venue.status}",
        )
    return await _set_venue_status(venue, VenueStatus.ACTIVE)


async def _set_venue_status(venue: VenueEntity, status: VenueStatus) -> VenueEntity:
    venue.status = status
    session = get_sql_session()
    await session.flush()
    await session.refresh(venue)
    await publish_venue_updated_event(str(venue.id), venue.timezone, status)
    _logger.info("Venue %s status set to %s", venue.id, status)
    return venue


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


_venue_action_dispatch = {
    VenueActionType.ACTIVATE: activate_venue,
    VenueActionType.CLOSE: close_venue,
    VenueActionType.DISABLE: disable_venue,
    VenueActionType.ENABLE: enable_venue,
}


async def dispatch_venue_action(action_type: VenueActionType, venue_id: UUID) -> VenueEntity:
    return await _venue_action_dispatch[action_type](venue_id)
