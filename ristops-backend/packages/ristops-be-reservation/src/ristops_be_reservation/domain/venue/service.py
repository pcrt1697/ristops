import logging
from datetime import date
from http import HTTPStatus
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select, ScalarResult, ColumnElement
from sqlalchemy.dialects.postgresql import insert

from ristops_be_reservation.domain.models import (
    Weekday, normalize_weekdays, weekday_scope_overlap_condition,
)
from ristops_be_reservation.domain.schedule.schema import (
    ConflictQuery, ConflictSource, ConflictsResponse, DateRangeFilter, ScheduleConflict,
)
from ristops_be_reservation.domain.venue.entities import VenueClosingEntity
from ristops_be_reservation.domain.venue.entities import VenueEntity
from ristops_be_reservation.domain.venue.events import VenueLifecycleEvent
from ristops_be_reservation.domain.venue.models import VenueStatus
from ristops_be_reservation.domain.venue.schema import (
    VenueClosingSearchQuery, VenueClosingResponse,
    VenueClosingUpdateRequest, VenueClosingCreateRequest
)
from ristops_lib_be.events import LifecycleOperationType
from ristops_lib_core.schema.pagination import Page
from ristops_lib_redis.engine import StreamPayload
from ristops_lib_sql.engine import get_sql_session, sql_session_provider
from ristops_lib_sql.search import PaginatedSearchQueryExecutor

_logger = logging.getLogger(__name__)


async def find_venue_or_throw(venue_id: UUID, for_update: bool = False) -> VenueEntity:
    """Return the local venue read-model for the given ID, or raise HTTP 404.

    Set ``for_update=True`` from a mutating path that needs to serialize against concurrent
    conflict-checked writes on the same venue: it takes a ``SELECT ... FOR UPDATE`` row lock,
    held until the transaction commits. Leave it false on read paths so plain GETs never block.
    """
    session = get_sql_session()
    stmt = select(VenueEntity).where(VenueEntity.id == venue_id).limit(1)
    if for_update:
        stmt = stmt.with_for_update()
    result: ScalarResult[VenueEntity] = await session.scalars(stmt)
    venue = result.one_or_none()
    if venue is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Venue not found")
    return venue


def check_venue_accepts_config_changes(venue: VenueEntity) -> None:
    """Raise HTTP 409 if the given venue's status doesn't allow config writes (DISABLED or
    CLOSED). PENDING and ACTIVE are allowed — PENDING is exactly the state config is written
    during. Use this directly when the caller already has the venue in hand, to avoid a
    redundant fetch; use `ensure_venue_accepts_config_changes` otherwise."""
    if VenueStatus(venue.status) in (VenueStatus.DISABLED, VenueStatus.CLOSED):
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail=f"Venue is {venue.status}; configuration changes are not allowed",
        )


async def ensure_venue_accepts_config_changes(venue_id: UUID, for_update: bool = False) -> None:
    """Fetch the venue by ID and raise HTTP 409 if its status doesn't allow config writes.

    Pass ``for_update=True`` from a venue-scoped write (e.g. a venue-closing create/update) to
    also take the venue row lock in the same fetch, serializing concurrent conflict-checked writes.
    """
    venue = await find_venue_or_throw(venue_id, for_update=for_update)
    check_venue_accepts_config_changes(venue)


async def upsert_venue(venue_id: str, timezone: str, status: VenueStatus) -> None:
    """Create or update the local venue read-model. Idempotent: re-running with the same payload is a no-op."""
    session = get_sql_session()
    insert_stmt = insert(VenueEntity).values(
        id=venue_id,
        timezone=timezone,
        status=status,
    )
    upsert_stmt = insert_stmt.on_conflict_do_update(
        index_elements=[VenueEntity.id],
        set_={
            "timezone": insert_stmt.excluded.timezone,
            "status": insert_stmt.excluded.status,
        },
    )
    await session.execute(upsert_stmt)
    _logger.info("Upserted venue read-model: %s", venue_id)


async def on_venue_event(_: str, payload: StreamPayload) -> None:
    event = VenueLifecycleEvent.model_validate(payload)
    async with sql_session_provider.context():
        if event.operation in (LifecycleOperationType.CREATED, LifecycleOperationType.UPDATED):
            await upsert_venue(event.id, event.timezone, event.status)


# --- Venue-wide closings -----------------------------------------------------

def _venue_date_range_conditions(
        venue_id: UUID,
        date_filter: DateRangeFilter,
) -> list[ColumnElement[bool]]:
    """Scope to the venue and overlap the `[date_from, date_to]` window (either bound optional)."""
    conditions: list[ColumnElement[bool]] = [VenueClosingEntity.venue_id == venue_id]
    if date_filter.date_from is not None:
        conditions.append(VenueClosingEntity.date_end >= date_filter.date_from)
    if date_filter.date_to is not None:
        conditions.append(VenueClosingEntity.date_start <= date_filter.date_to)
    return conditions


_venue_closing_search_executor = PaginatedSearchQueryExecutor[
    VenueClosingSearchQuery, UUID, VenueClosingEntity, VenueClosingResponse
](
    entity_class=VenueClosingEntity,
    response_class=VenueClosingResponse,
    condition_builder=lambda query, venue_id: _venue_date_range_conditions(venue_id, query),
)


async def find_venue_closing_or_throw(venue_id: UUID, closing_id: UUID) -> VenueClosingEntity:
    """Return the venue closing with the given ID under the given venue, or raise HTTP 404."""
    session = get_sql_session()
    result: ScalarResult[VenueClosingEntity] = await session.scalars(
        select(VenueClosingEntity).where(
            VenueClosingEntity.id == closing_id,
            VenueClosingEntity.venue_id == venue_id,
        ).limit(1)
    )
    closing = result.one_or_none()
    if closing is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Venue closing not found")
    return closing


async def find_venue_closing_conflicts(
        venue_id: UUID,
        date_start: date,
        date_end: date,
        weekday: Weekday | None,
        exclude_id: UUID | None = None,
) -> list[VenueClosingEntity]:
    """Return all venue closings on ``venue_id`` that overlap the given period and weekday scope.

    Overlap = date ranges intersect (inclusive) and weekday scopes intersect (see
    ``weekday_scope_overlap_condition``). ``exclude_id`` drops one row from the check, used when
    previewing/validating an in-place edit so it can't conflict with itself. Public: the
    service-closing rule (in schedule/service.py) reuses it to check the venue side."""
    session = get_sql_session()
    conditions: list[ColumnElement[bool]] = [
        VenueClosingEntity.venue_id == venue_id,
        VenueClosingEntity.date_end >= date_start,
        VenueClosingEntity.date_start <= date_end,
        weekday_scope_overlap_condition(VenueClosingEntity.weekday, weekday),
    ]
    if exclude_id is not None:
        conditions.append(VenueClosingEntity.id != exclude_id)
    result: ScalarResult[VenueClosingEntity] = await session.scalars(
        select(VenueClosingEntity).where(*conditions)
    )
    return list(result.all())


async def ensure_no_venue_closing_conflict(
        venue_id: UUID,
        date_start: date,
        date_end: date,
        weekday: Weekday | None,
        exclude_id: UUID | None = None,
) -> None:
    """Raise HTTP 409 if a venue closing already overlaps the given period and weekday scope."""
    conflicts = await find_venue_closing_conflicts(
        venue_id, date_start, date_end, weekday, exclude_id=exclude_id
    )
    if conflicts:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail="The period conflicts with an existing venue closing",
        )


async def create_venue_closings(
        venue_id: UUID,
        request: VenueClosingCreateRequest,
) -> list[VenueClosingEntity]:
    """Create one or more venue-wide closings in a single transaction — one row per weekday in
    ``request.weekdays`` (normalized: empty/all-seven collapses to a single every-day row).
    Authorized against the venue itself. Raises HTTP 409 if any row would overlap an existing
    venue closing."""
    await ensure_venue_accepts_config_changes(venue_id, for_update=True)
    weekdays = normalize_weekdays(request.weekdays)
    for weekday in weekdays:
        await ensure_no_venue_closing_conflict(
            venue_id, request.date_start, request.date_end, weekday
        )
    session = get_sql_session()
    closings = [
        VenueClosingEntity(
            venue_id=venue_id,
            date_start=request.date_start,
            date_end=request.date_end,
            weekday=weekday,
            description=request.description,
        )
        for weekday in weekdays
    ]
    session.add_all(closings)
    await session.flush()
    for closing in closings:
        await session.refresh(closing)
    _logger.info("Created %d venue closing(s) for venue %s", len(closings), venue_id)
    return closings


async def update_venue_closing(
        venue_id: UUID,
        closing_id: UUID,
        request: VenueClosingUpdateRequest,
) -> VenueClosingEntity:
    """Update a venue closing. Only fields present in the request body are modified. The weekday
    scope is immutable. Raises HTTP 409 if the new period would overlap another venue closing."""
    closing = await find_venue_closing_or_throw(venue_id, closing_id)
    await ensure_venue_accepts_config_changes(venue_id, for_update=True)
    fields_to_update = request.model_fields_set

    if "date_start" in fields_to_update and request.date_start is not None:
        closing.date_start = request.date_start
    if "date_end" in fields_to_update and request.date_end is not None:
        closing.date_end = request.date_end
    if "description" in fields_to_update:
        closing.description = request.description

    await ensure_no_venue_closing_conflict(
        venue_id,
        closing.date_start,
        closing.date_end,
        Weekday(closing.weekday) if closing.weekday is not None else None,
        exclude_id=closing.id,
    )

    session = get_sql_session()
    await session.flush()
    await session.refresh(closing)
    _logger.info("Updated venue closing %s for venue %s", closing_id, venue_id)
    return closing


async def remove_venue_closing(venue_id: UUID, closing_id: UUID) -> None:
    """Delete a venue closing. Raises HTTP 404 if not found."""
    closing = await find_venue_closing_or_throw(venue_id, closing_id)
    await ensure_venue_accepts_config_changes(venue_id)
    session = get_sql_session()
    await session.delete(closing)
    _logger.info("Deleted venue closing %s for venue %s", closing_id, venue_id)


async def search_venue_closings(
        venue_id: UUID,
        query: VenueClosingSearchQuery,
) -> Page[VenueClosingResponse]:
    """Return a paginated, date-range-filtered page of venue-wide closings for a venue."""
    await find_venue_or_throw(venue_id)
    return await _venue_closing_search_executor.execute(query, venue_id)


async def find_venue_closing_conflicts_for(
        venue_id: UUID,
        query: ConflictQuery,
) -> ConflictsResponse:
    """Read-only preview: which existing venue closings a candidate period+weekdays would conflict
    with, across every normalized weekday of the candidate. Lock-free — no venue row lock — since
    it never writes. Mirrors what ``create_venue_closings`` would reject."""
    await find_venue_or_throw(venue_id)
    conflicts: list[ScheduleConflict] = []
    for weekday in normalize_weekdays(query.weekdays):
        rows = await find_venue_closing_conflicts(
            venue_id, query.date_start, query.date_end, weekday, exclude_id=query.exclude_id
        )
        conflicts.extend(
            ScheduleConflict(
                weekday=weekday,
                source=ConflictSource.VENUE_CLOSING,
                conflicting_id=row.id,
                conflicting_date_start=row.date_start,
                conflicting_date_end=row.date_end,
                conflicting_weekday=Weekday(row.weekday) if row.weekday is not None else None,
            )
            for row in rows
        )
    return ConflictsResponse(conflicts=conflicts)
