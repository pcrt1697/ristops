import logging
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from http import HTTPStatus
from typing import NamedTuple
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select, delete, ScalarResult, ColumnElement

from ristops_be_reservation.domain.models import (
    Weekday, normalize_weekdays, weekday_scope_overlap_condition,
)
from ristops_be_reservation.domain.schedule.entities import (
    OpeningEntity, OpeningOverrideEntity, ServiceClosingEntity, CapacityOverrideEntity,
)
from ristops_be_reservation.domain.schedule.schema import (
    OpeningsUpsertRequest, OpeningOverrideCreateRequest,
    OpeningOverrideUpdateRequest, ServiceClosingCreateRequest, ServiceClosingUpdateRequest,
    OpeningOverrideResponse, OpeningOverrideSearchQuery,
    ServiceClosingResponse, ServiceClosingSearchQuery, DateRangeFilter,
    CapacityOverrideCreateRequest, CapacityOverrideUpdateRequest,
    CapacityOverrideResponse, CapacityOverrideSearchQuery,
    ConflictQuery, ConflictSource, ConflictsResponse, ScheduleConflict, OpeningConflictQuery,
)
from ristops_be_reservation.domain.service.entities import ServiceEntity
from ristops_be_reservation.domain.service.service import find_service_or_throw
from ristops_be_reservation.domain.venue.entities import VenueClosingEntity
from ristops_be_reservation.domain.venue.service import (
    ensure_venue_accepts_config_changes, find_venue_closing_conflicts,
)
from ristops_lib_core.schema.pagination import Page
from ristops_lib_sql.engine import get_sql_session
from ristops_lib_sql.search import PaginatedSearchQueryExecutor

_logger = logging.getLogger(__name__)


def _date_range_conditions(
        entity: type[OpeningOverrideEntity] | type[ServiceClosingEntity] | type[CapacityOverrideEntity],
        service_id: UUID,
        date_filter: DateRangeFilter,
) -> list[ColumnElement[bool]]:
    """Scope to the service and overlap the `[date_from, date_to]` window (either bound
    optional). Overlap = the item's period covers at least one day of the window."""
    conditions: list[ColumnElement[bool]] = [entity.service_id == service_id]
    if date_filter.date_from is not None:
        conditions.append(entity.date_end >= date_filter.date_from)
    if date_filter.date_to is not None:
        conditions.append(entity.date_start <= date_filter.date_to)
    return conditions


_override_search_executor = PaginatedSearchQueryExecutor[
    OpeningOverrideSearchQuery, UUID, OpeningOverrideEntity, OpeningOverrideResponse
](
    entity_class=OpeningOverrideEntity,
    response_class=OpeningOverrideResponse,
    condition_builder=lambda query, service_id: _date_range_conditions(
        OpeningOverrideEntity, service_id, query
    ),
)

_service_closing_search_executor = PaginatedSearchQueryExecutor[
    ServiceClosingSearchQuery, UUID, ServiceClosingEntity, ServiceClosingResponse
](
    entity_class=ServiceClosingEntity,
    response_class=ServiceClosingResponse,
    condition_builder=lambda query, service_id: _date_range_conditions(
        ServiceClosingEntity, service_id, query
    ),
)

_capacity_override_search_executor = PaginatedSearchQueryExecutor[
    CapacityOverrideSearchQuery, UUID, CapacityOverrideEntity, CapacityOverrideResponse
](
    entity_class=CapacityOverrideEntity,
    response_class=CapacityOverrideResponse,
    condition_builder=lambda query, service_id: _date_range_conditions(
        CapacityOverrideEntity, service_id, query
    ),
)


#
# Each exception kind only conflicts with its own kind on the same service (service closings
# additionally check venue closings — handled in `_ensure_no_service_closing_conflict`). Two rows
# conflict when their date ranges intersect (inclusive) AND their weekday scopes intersect.

_ServiceExceptionEntity = (
    type[OpeningOverrideEntity] | type[ServiceClosingEntity] | type[CapacityOverrideEntity]
)


async def _find_service_exception_conflicts(
        entity: _ServiceExceptionEntity,
        service_id: UUID,
        date_start: date,
        date_end: date,
        weekday: Weekday | None,
        exclude_id: UUID | None = None,
) -> list[OpeningOverrideEntity | ServiceClosingEntity | CapacityOverrideEntity]:
    """Return all rows of ``entity`` on ``service_id`` overlapping the given period and weekday
    scope. ``exclude_id`` drops one row (used to let an in-place edit not conflict with itself)."""
    conditions: list[ColumnElement[bool]] = [
        entity.service_id == service_id,
        entity.date_end >= date_start,
        entity.date_start <= date_end,
        weekday_scope_overlap_condition(entity.weekday, weekday),
    ]
    if exclude_id is not None:
        conditions.append(entity.id != exclude_id)
    session = get_sql_session()
    result = await session.scalars(select(entity).where(*conditions))
    return list(result.all())


async def _ensure_no_opening_override_conflict(
        service_id: UUID,
        date_start: date,
        date_end: date,
        weekday: Weekday | None,
        exclude_id: UUID | None = None,
) -> None:
    """Raise HTTP 409 if another opening override already overlaps this period and weekday scope."""
    if await _find_service_exception_conflicts(
            OpeningOverrideEntity, service_id, date_start, date_end, weekday, exclude_id=exclude_id
    ):
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail="The period conflicts with an existing opening override",
        )


async def _ensure_no_capacity_override_conflict(
        service_id: UUID,
        date_start: date,
        date_end: date,
        weekday: Weekday | None,
        exclude_id: UUID | None = None,
) -> None:
    """Raise HTTP 409 if another capacity override already overlaps this period and weekday scope."""
    if await _find_service_exception_conflicts(
            CapacityOverrideEntity, service_id, date_start, date_end, weekday, exclude_id=exclude_id
    ):
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail="The period conflicts with an existing capacity override",
        )


async def _ensure_no_service_closing_conflict(
        service_id: UUID,
        venue_id: UUID,
        date_start: date,
        date_end: date,
        weekday: Weekday | None,
        exclude_id: UUID | None = None,
) -> None:
    """Raise HTTP 409 if the period overlaps another service closing on this service, or any venue
    closing on the service's venue. ``exclude_id`` applies only to the same-table (service-closing)
    check — a service-closing id can never identify a venue-closing row."""
    if await _find_service_exception_conflicts(
            ServiceClosingEntity, service_id, date_start, date_end, weekday, exclude_id=exclude_id
    ):
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail="The period conflicts with an existing service closing",
        )
    if await find_venue_closing_conflicts(venue_id, date_start, date_end, weekday):
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail="The period conflicts with an existing venue closing",
        )


async def upsert_service_openings(
        service_id: UUID,
        request: OpeningsUpsertRequest,
) -> list[OpeningEntity]:
    """Replace the full set of openings for a service: existing openings are dropped and the
    submitted list is inserted fresh.

    No diff/reconcile-in-place, unlike overrides/closings' per-item CRUD — an opening's `id`
    carries no identity anything else references, so there's nothing to preserve across a
    replace. Duplicate weekdays in the request are rejected at the schema layer
    (`OpeningsUpsertRequest`).
    """
    service = await find_service_or_throw(service_id)
    # Lock the venue row to serialize concurrent schedule writes across the venue's services while
    # the cross-service overlap check reads their openings.
    await ensure_venue_accepts_config_changes(service.venue_id, for_update=True)
    await ensure_no_cross_service_opening_overlap_for_openings(
        service_id, service.venue_id, request.openings
    )

    session = get_sql_session()
    await session.execute(
        delete(OpeningEntity).where(OpeningEntity.service_id == service_id)
    )

    openings = [
        OpeningEntity(
            service_id=service_id,
            weekday=item.weekday,
            capacity=item.capacity,
            start_time=item.start_time,
            end_time=item.end_time,
            description=item.description,
        )
        for item in request.openings
    ]
    session.add_all(openings)

    await session.flush()
    for opening in openings:
        await session.refresh(opening)
    _logger.info("Replaced openings for service %s with %d entries", service_id, len(openings))
    return openings


async def list_service_openings(service_id: UUID, include_deleted: bool = False) -> list[OpeningEntity]:
    """Return all openings for a service."""
    await find_service_or_throw(service_id, include_deleted=include_deleted)
    session = get_sql_session()
    result: ScalarResult[OpeningEntity] = await session.scalars(
        select(OpeningEntity).where(OpeningEntity.service_id == service_id)
    )
    return list(result.all())


async def find_service_opening_override_or_throw(
        service_id: UUID,
        override_id: UUID,
) -> OpeningOverrideEntity:
    """Return the opening override with the given ID under the given service, or raise HTTP 404."""
    session = get_sql_session()
    result: ScalarResult[OpeningOverrideEntity] = await session.scalars(
        select(OpeningOverrideEntity).where(
            OpeningOverrideEntity.id == override_id,
            OpeningOverrideEntity.service_id == service_id,
        ).limit(1)
    )
    override = result.one_or_none()
    if override is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Opening override not found")
    return override


async def create_service_opening_overrides(
        service_id: UUID,
        request: OpeningOverrideCreateRequest,
) -> list[OpeningOverrideEntity]:
    """Create one or more opening overrides for a service in a single transaction — one row per
    weekday in ``request.weekdays`` (normalized: empty/all-seven collapses to a single every-day
    row). Overrides are one-off special cases, so unlike openings this is a plain bulk create,
    not a reconcile. Raises HTTP 409 if any row would overlap an existing opening override."""
    service = await find_service_or_throw(service_id, for_update=True)
    await ensure_venue_accepts_config_changes(service.venue_id, for_update=True)
    weekdays = normalize_weekdays(request.weekdays)
    for weekday in weekdays:
        await _ensure_no_opening_override_conflict(
            service_id, request.date_start, request.date_end, weekday
        )
        override_candidate = _OverrideCandidate(
            request.date_start, request.date_end, weekday,
            request.start_time, request.end_time,
        )
        await ensure_no_cross_service_opening_overlap_for_override(
            service_id, service.venue_id, override_candidate,
        )
        await ensure_no_self_overnight_overlap_for_override(service, override_candidate)
    session = get_sql_session()
    overrides = [
        OpeningOverrideEntity(
            service_id=service_id,
            date_start=request.date_start,
            date_end=request.date_end,
            weekday=weekday,
            capacity=request.capacity,
            start_time=request.start_time,
            end_time=request.end_time,
            description=request.description,
        )
        for weekday in weekdays
    ]
    session.add_all(overrides)
    await session.flush()
    for override in overrides:
        await session.refresh(override)
    _logger.info(
        "Created %d opening override(s) for service %s", len(overrides), service_id
    )
    return overrides


async def update_service_opening_override(
        service_id: UUID,
        override_id: UUID,
        request: OpeningOverrideUpdateRequest,
) -> OpeningOverrideEntity:
    """Update an opening override. Only fields present in the request body are modified. The
    weekday scope is immutable. Raises HTTP 409 if the new period would overlap another opening
    override."""
    override = await find_service_opening_override_or_throw(service_id, override_id)
    service = await find_service_or_throw(service_id, for_update=True)
    await ensure_venue_accepts_config_changes(service.venue_id, for_update=True)
    fields_to_update = request.model_fields_set

    if "date_start" in fields_to_update and request.date_start is not None:
        override.date_start = request.date_start
    if "date_end" in fields_to_update and request.date_end is not None:
        override.date_end = request.date_end
    if "capacity" in fields_to_update and request.capacity is not None:
        override.capacity = request.capacity
    if "start_time" in fields_to_update and request.start_time is not None:
        override.start_time = request.start_time
    if "end_time" in fields_to_update and request.end_time is not None:
        override.end_time = request.end_time
    if "description" in fields_to_update:
        override.description = request.description

    override_weekday = Weekday(override.weekday) if override.weekday is not None else None
    await _ensure_no_opening_override_conflict(
        service_id,
        override.date_start,
        override.date_end,
        override_weekday,
        exclude_id=override.id,
    )
    override_candidate = _OverrideCandidate(
        override.date_start, override.date_end, override_weekday,
        override.start_time, override.end_time,
    )
    await ensure_no_cross_service_opening_overlap_for_override(
        service_id, service.venue_id, override_candidate,
    )
    await ensure_no_self_overnight_overlap_for_override(
        service, override_candidate, exclude_override_id=override.id,
    )

    session = get_sql_session()
    await session.flush()
    await session.refresh(override)
    _logger.info("Updated opening override %s for service %s", override_id, service_id)
    return override


async def remove_service_opening_override(service_id: UUID, override_id: UUID) -> None:
    """Delete an opening override. Raises HTTP 404 if not found."""
    override = await find_service_opening_override_or_throw(service_id, override_id)
    service = await find_service_or_throw(service_id)
    await ensure_venue_accepts_config_changes(service.venue_id)
    session = get_sql_session()
    await session.delete(override)
    _logger.info("Deleted opening override %s for service %s", override_id, service_id)


async def search_service_opening_overrides(
        service_id: UUID,
        query: OpeningOverrideSearchQuery,
) -> Page[OpeningOverrideResponse]:
    """Return a paginated, date-range-filtered page of opening overrides for a service."""
    await find_service_or_throw(service_id, include_deleted=query.include_deleted)
    return await _override_search_executor.execute(query, service_id)


async def find_service_closing_or_throw(service_id: UUID, closing_id: UUID) -> ServiceClosingEntity:
    """Return the closing with the given ID under the given service, or raise HTTP 404."""
    session = get_sql_session()
    result: ScalarResult[ServiceClosingEntity] = await session.scalars(
        select(ServiceClosingEntity).where(
            ServiceClosingEntity.id == closing_id,
            ServiceClosingEntity.service_id == service_id,
        ).limit(1)
    )
    closing = result.one_or_none()
    if closing is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Closing not found")
    return closing


async def create_service_closings(
        service_id: UUID,
        request: ServiceClosingCreateRequest,
) -> list[ServiceClosingEntity]:
    """Create one or more closings for a service in a single transaction — one row per weekday
    in ``request.weekdays`` (normalized: empty/all-seven collapses to a single every-day row).
    Closings are one-off special cases, so unlike openings this is a plain bulk create, not a
    reconcile. Raises HTTP 409 if any row would overlap an existing service closing, or a venue
    closing on the service's venue."""
    service = await find_service_or_throw(service_id, for_update=True)
    await ensure_venue_accepts_config_changes(service.venue_id, for_update=True)
    weekdays = normalize_weekdays(request.weekdays)
    for weekday in weekdays:
        await _ensure_no_service_closing_conflict(
            service_id, service.venue_id, request.date_start, request.date_end, weekday
        )
    session = get_sql_session()
    closings = [
        ServiceClosingEntity(
            service_id=service_id,
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
    _logger.info("Created %d closing(s) for service %s", len(closings), service_id)
    return closings


async def update_service_closing(
        service_id: UUID,
        closing_id: UUID,
        request: ServiceClosingUpdateRequest,
) -> ServiceClosingEntity:
    """Update a closing. Only fields present in the request body are modified. The weekday scope
    is immutable. Raises HTTP 409 if the new period would overlap another service closing, or a
    venue closing on the service's venue."""
    closing = await find_service_closing_or_throw(service_id, closing_id)
    service = await find_service_or_throw(service_id, for_update=True)
    await ensure_venue_accepts_config_changes(service.venue_id, for_update=True)
    fields_to_update = request.model_fields_set

    if "date_start" in fields_to_update and request.date_start is not None:
        closing.date_start = request.date_start
    if "date_end" in fields_to_update and request.date_end is not None:
        closing.date_end = request.date_end
    if "description" in fields_to_update:
        closing.description = request.description

    await _ensure_no_service_closing_conflict(
        service_id,
        service.venue_id,
        closing.date_start,
        closing.date_end,
        Weekday(closing.weekday) if closing.weekday is not None else None,
        exclude_id=closing.id,
    )

    session = get_sql_session()
    await session.flush()
    await session.refresh(closing)
    _logger.info("Updated closing %s for service %s", closing_id, service_id)
    return closing


async def remove_service_closing(service_id: UUID, closing_id: UUID) -> None:
    """Delete a closing. Raises HTTP 404 if not found."""
    closing = await find_service_closing_or_throw(service_id, closing_id)
    service = await find_service_or_throw(service_id)
    await ensure_venue_accepts_config_changes(service.venue_id)
    session = get_sql_session()
    await session.delete(closing)
    _logger.info("Deleted closing %s for service %s", closing_id, service_id)


async def search_service_closings(
        service_id: UUID,
        query: ServiceClosingSearchQuery,
) -> Page[ServiceClosingResponse]:
    """Return a paginated, date-range-filtered page of closings for a service."""
    await find_service_or_throw(service_id, include_deleted=query.include_deleted)
    return await _service_closing_search_executor.execute(query, service_id)


async def find_service_capacity_override_or_throw(
        service_id: UUID,
        capacity_override_id: UUID,
) -> CapacityOverrideEntity:
    """Return the capacity override with the given ID under the given service, or raise HTTP 404."""
    session = get_sql_session()
    result: ScalarResult[CapacityOverrideEntity] = await session.scalars(
        select(CapacityOverrideEntity).where(
            CapacityOverrideEntity.id == capacity_override_id,
            CapacityOverrideEntity.service_id == service_id,
        ).limit(1)
    )
    capacity_override = result.one_or_none()
    if capacity_override is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Capacity override not found")
    return capacity_override


async def create_service_capacity_overrides(
        service_id: UUID,
        request: CapacityOverrideCreateRequest,
) -> list[CapacityOverrideEntity]:
    """Create one or more capacity overrides for a service in a single transaction — one row per
    weekday in ``request.weekdays`` (normalized: empty/all-seven collapses to a single every-day
    row). A one-off seat delta, so a plain bulk create. Raises HTTP 409 if any row would overlap
    an existing capacity override."""
    service = await find_service_or_throw(service_id, for_update=True)
    await ensure_venue_accepts_config_changes(service.venue_id)
    weekdays = normalize_weekdays(request.weekdays)
    for weekday in weekdays:
        await _ensure_no_capacity_override_conflict(
            service_id, request.date_start, request.date_end, weekday
        )
    session = get_sql_session()
    capacity_overrides = [
        CapacityOverrideEntity(
            service_id=service_id,
            date_start=request.date_start,
            date_end=request.date_end,
            weekday=weekday,
            capacity_delta=request.capacity_delta,
            description=request.description,
        )
        for weekday in weekdays
    ]
    session.add_all(capacity_overrides)
    await session.flush()
    for capacity_override in capacity_overrides:
        await session.refresh(capacity_override)
    _logger.info(
        "Created %d capacity override(s) for service %s", len(capacity_overrides), service_id
    )
    return capacity_overrides


async def update_service_capacity_override(
        service_id: UUID,
        capacity_override_id: UUID,
        request: CapacityOverrideUpdateRequest,
) -> CapacityOverrideEntity:
    """Update a capacity override. Only fields present in the request body are modified. The
    weekday scope is immutable. Raises HTTP 409 if the new period would overlap another capacity
    override."""
    capacity_override = await find_service_capacity_override_or_throw(service_id, capacity_override_id)
    service = await find_service_or_throw(service_id, for_update=True)
    await ensure_venue_accepts_config_changes(service.venue_id)
    fields_to_update = request.model_fields_set

    if "date_start" in fields_to_update and request.date_start is not None:
        capacity_override.date_start = request.date_start
    if "date_end" in fields_to_update and request.date_end is not None:
        capacity_override.date_end = request.date_end
    if "capacity_delta" in fields_to_update and request.capacity_delta is not None:
        capacity_override.capacity_delta = request.capacity_delta
    if "description" in fields_to_update:
        capacity_override.description = request.description

    await _ensure_no_capacity_override_conflict(
        service_id,
        capacity_override.date_start,
        capacity_override.date_end,
        Weekday(capacity_override.weekday) if capacity_override.weekday is not None else None,
        exclude_id=capacity_override.id,
    )

    session = get_sql_session()
    await session.flush()
    await session.refresh(capacity_override)
    _logger.info("Updated capacity override %s for service %s", capacity_override_id, service_id)
    return capacity_override


async def remove_service_capacity_override(service_id: UUID, capacity_override_id: UUID) -> None:
    """Delete a capacity override. Raises HTTP 404 if not found."""
    capacity_override = await find_service_capacity_override_or_throw(service_id, capacity_override_id)
    service = await find_service_or_throw(service_id)
    await ensure_venue_accepts_config_changes(service.venue_id)
    session = get_sql_session()
    await session.delete(capacity_override)
    _logger.info("Deleted capacity override %s for service %s", capacity_override_id, service_id)


async def search_service_capacity_overrides(
        service_id: UUID,
        query: CapacityOverrideSearchQuery,
) -> Page[CapacityOverrideResponse]:
    """Return a paginated, date-range-filtered page of capacity overrides for a service."""
    await find_service_or_throw(service_id, include_deleted=query.include_deleted)
    return await _capacity_override_search_executor.execute(query, service_id)



def _to_schedule_conflict(
        candidate_weekday: Weekday | None,
        source: ConflictSource,
        row: OpeningOverrideEntity | ServiceClosingEntity | CapacityOverrideEntity | VenueClosingEntity,
) -> ScheduleConflict:
    """Map a conflicting DB row to a `ScheduleConflict`, tagged with the candidate weekday it
    clashes with and the row's own kind."""
    return ScheduleConflict(
        weekday=candidate_weekday,
        source=source,
        conflicting_id=row.id,
        conflicting_date_start=row.date_start,
        conflicting_date_end=row.date_end,
        conflicting_weekday=Weekday(row.weekday) if row.weekday is not None else None,
    )


async def find_service_opening_override_conflicts_for(
        service_id: UUID,
        query: ConflictQuery,
) -> ConflictsResponse:
    """Read-only preview: which existing opening overrides (same service) a candidate
    period+weekdays would conflict with, plus any cross-service opening overlaps (SERVICE_OPENING)
    when the candidate carries hours. Lock-free — mirrors what `create_service_opening_overrides`
    would reject."""
    await find_service_or_throw(service_id)
    conflicts: list[ScheduleConflict] = []
    for weekday in normalize_weekdays(query.weekdays):
        rows = await _find_service_exception_conflicts(
            OpeningOverrideEntity, service_id, query.date_start, query.date_end, weekday,
            exclude_id=query.exclude_id,
        )
        conflicts.extend(
            _to_schedule_conflict(weekday, ConflictSource.OPENING_OVERRIDE, row) for row in rows
        )
    conflicts.extend(
        await find_service_opening_override_cross_service_conflicts_for(service_id, query)
    )
    return ConflictsResponse(conflicts=conflicts)


async def find_service_capacity_override_conflicts_for(
        service_id: UUID,
        query: ConflictQuery,
) -> ConflictsResponse:
    """Read-only preview: which existing capacity overrides a candidate period+weekdays would
    conflict with. Lock-free — mirrors what `create_service_capacity_overrides` would reject."""
    await find_service_or_throw(service_id)
    conflicts: list[ScheduleConflict] = []
    for weekday in normalize_weekdays(query.weekdays):
        rows = await _find_service_exception_conflicts(
            CapacityOverrideEntity, service_id, query.date_start, query.date_end, weekday,
            exclude_id=query.exclude_id,
        )
        conflicts.extend(
            _to_schedule_conflict(weekday, ConflictSource.CAPACITY_OVERRIDE, row) for row in rows
        )
    return ConflictsResponse(conflicts=conflicts)


async def find_service_closing_conflicts_for(
        service_id: UUID,
        query: ConflictQuery,
) -> ConflictsResponse:
    """Read-only preview: which existing service closings (this service) or venue closings (its
    venue) a candidate period+weekdays would conflict with. Lock-free — mirrors what
    `create_service_closings` would reject. ``exclude_id`` applies only to the service-closing
    side; venue closings are always checked in full."""
    service = await find_service_or_throw(service_id)
    conflicts: list[ScheduleConflict] = []
    for weekday in normalize_weekdays(query.weekdays):
        service_rows = await _find_service_exception_conflicts(
            ServiceClosingEntity, service_id, query.date_start, query.date_end, weekday,
            exclude_id=query.exclude_id,
        )
        conflicts.extend(
            _to_schedule_conflict(weekday, ConflictSource.SERVICE_CLOSING, row)
            for row in service_rows
        )
        venue_rows = await find_venue_closing_conflicts(
            service.venue_id, query.date_start, query.date_end, weekday
        )
        conflicts.extend(
            _to_schedule_conflict(weekday, ConflictSource.VENUE_CLOSING, row) for row in venue_rows
        )
    return ConflictsResponse(conflicts=conflicts)


#
# Infer which of a venue's services is open at a candidate reservation instant and resolve its
# effective opening window + seat capacity, applying the same precedence the config CRUD enforces.
# Used by the reservation domain to decide whether a slot is bookable. Reservations carry no
# service reference — the service is derived from venue + datetime here. The candidate is a naive
# venue-local datetime; the caller converts the reservation instant into the venue timezone first.
#
# Openings run overnight when their end_time is not after their start_time (e.g. 18:00–02:00):
# such an opening belongs to the calendar date it *opens* on (its weekday), and its window spills
# into the next calendar day. So a candidate's "business date" — the date whose weekday/closings/
# capacity apply — is not always its own calendar date: an early-morning booking attaches to the
# previous day's overnight opening. `resolve_opening_or_throw` returns the window as concrete
# datetimes (the close may land on the following day) so the caller needs no wrap-around math.

# Weekday enum in Python's Monday=0..Sunday=6 order, matching date.weekday().
_WEEKDAYS: tuple[Weekday, ...] = tuple(Weekday)


def _opening_window(on_date: date, start_time: time, end_time: time) -> tuple[datetime, datetime]:
    """Concrete open/close datetimes for an opening on ``on_date``. An opening whose ``end_time``
    is not after its ``start_time`` runs overnight, so its close lands on the following day."""
    opens_at = datetime.combine(on_date, start_time)
    close_date = on_date if end_time > start_time else on_date + timedelta(days=1)
    return opens_at, datetime.combine(close_date, end_time)


#
# Enforce that no two services of a venue are *effectively* open at the same instant, so a
# reservation's service is unambiguous (see `resolve_bookable_slot_or_throw`). A service
# occupies a window on a date when it has an effective opening (override-for-that-date else base
# weekday opening) AND no service/venue closing removes that date. Overlap splits in two:
#   * permanent (base vs base): same weekday + time overlap recurs forever — closings (bounded)
#     can never eliminate all occurrences, so they're irrelevant. Overnight openings are compared
#     as per-weekday minute segments (an 18:00–02:00 Friday opening also occupies Saturday 00:00–02:00).
#   * bounded (an override on either side): confined to concrete dates — iterate them, resolve each
#     side's effective window per date (subtracting closings), and compare. This honours "a closed
#     service frees the slot for another".
# Intervals are half-open, so touching boundaries (15:00 end vs 15:00 start) do not conflict.


@dataclass
class _OpeningCandidate:
    """A proposed base weekly opening (indefinite) being validated for overlap."""

    weekday: Weekday
    start_time: time
    end_time: time


@dataclass
class _OverrideCandidate:
    """A proposed opening override (bounded date range) being validated for overlap."""

    date_start: date
    date_end: date
    weekday: Weekday | None
    start_time: time
    end_time: time


@dataclass
class _ServiceSchedule:
    """A sibling service's schedule, preloaded for in-memory overlap checks."""

    service: ServiceEntity
    base_by_weekday: dict[Weekday, OpeningEntity]
    overrides: list[OpeningOverrideEntity]
    closings: list[ServiceClosingEntity]


@dataclass
class _OverlapContext:
    """Everything needed to check a candidate against a venue's other services."""

    siblings: list[_ServiceSchedule]
    venue_closings: list[VenueClosingEntity]
    candidate_closings: list[ServiceClosingEntity]


def _time_to_min(t: time) -> int:
    return t.hour * 60 + t.minute


def _opening_minute_segments(weekday: Weekday, start: time, end: time) -> list[tuple[Weekday, int, int]]:
    """Split an opening into half-open minute segments `(weekday, start_min, end_min)` within a
    day. A same-day opening is one segment; an overnight opening (``end <= start``) becomes an
    evening segment on its weekday plus an early-morning segment on the following weekday."""
    s, e = _time_to_min(start), _time_to_min(end)
    if e > s:
        return [(weekday, s, e)]
    segments = [(weekday, s, 24 * 60)]
    if e > 0:
        next_weekday = _WEEKDAYS[(_WEEKDAYS.index(weekday) + 1) % 7]
        segments.append((next_weekday, 0, e))
    return segments


def _minute_segments_overlap(
        a: list[tuple[Weekday, int, int]], b: list[tuple[Weekday, int, int]],
) -> bool:
    """Whether two sets of weekday minute segments overlap (same weekday, half-open time overlap)."""
    return any(
        aw == bw and a_start < b_end and b_start < a_end
        for (aw, a_start, a_end) in a
        for (bw, b_start, b_end) in b
    )


def _windows_overlap(a_open: datetime, a_close: datetime, b_open: datetime, b_close: datetime) -> bool:
    """Half-open overlap of two concrete datetime windows."""
    return a_open < b_close and b_open < a_close


def _covers_date(date_start: date, date_end: date, weekday_value: str | None, d: date) -> bool:
    """Whether a date-ranged, optionally weekday-scoped row applies on date ``d`` (null weekday =
    every day)."""
    if not (date_start <= d <= date_end):
        return False
    return weekday_value is None or weekday_value == _WEEKDAYS[d.weekday()]


def _service_closed_on(schedule: _ServiceSchedule, venue_closings: list[VenueClosingEntity], d: date) -> bool:
    """Whether a sibling service is closed on ``d`` by its own or a venue-wide closing."""
    if any(_covers_date(c.date_start, c.date_end, c.weekday, d) for c in schedule.closings):
        return True
    return any(_covers_date(c.date_start, c.date_end, c.weekday, d) for c in venue_closings)


def _candidate_closed_on(ctx: _OverlapContext, d: date) -> bool:
    """Whether the service being edited is closed on ``d`` (its own or a venue-wide closing)."""
    if any(_covers_date(c.date_start, c.date_end, c.weekday, d) for c in ctx.candidate_closings):
        return True
    return any(_covers_date(c.date_start, c.date_end, c.weekday, d) for c in ctx.venue_closings)


def _effective_row_on(
        schedule: _ServiceSchedule, d: date,
) -> tuple[OpeningEntity | OpeningOverrideEntity, time, time] | None:
    """A sibling's effective opening row + hours on ``d``: an override covering the date wins over
    the base weekday opening; ``None`` if the sibling has no opening that day."""
    for override in schedule.overrides:
        if _covers_date(override.date_start, override.date_end, override.weekday, d):
            return override, override.start_time, override.end_time
    base = schedule.base_by_weekday.get(_WEEKDAYS[d.weekday()])
    if base is not None:
        return base, base.start_time, base.end_time
    return None


def _service_opening_conflict(
        candidate_weekday: Weekday | None,
        schedule: _ServiceSchedule,
        conflicting_id: UUID,
        start_time: time,
        end_time: time,
        conflicting_weekday: Weekday | None,
        conflicting_date: date | None,
) -> ScheduleConflict:
    return ScheduleConflict(
        weekday=candidate_weekday,
        source=ConflictSource.SERVICE_OPENING,
        conflicting_id=conflicting_id,
        conflicting_date_start=conflicting_date,
        conflicting_date_end=conflicting_date,
        conflicting_weekday=conflicting_weekday,
        conflicting_service_id=schedule.service.id,
        conflicting_service_name=schedule.service.name,
        conflicting_start_time=start_time,
        conflicting_end_time=end_time,
    )


def _iter_dates(date_start: date, date_end: date):
    d = date_start
    while d <= date_end:
        yield d
        d += timedelta(days=1)


def _base_candidate_conflicts(candidate: _OpeningCandidate, ctx: _OverlapContext) -> list[ScheduleConflict]:
    """Conflicts of a proposed base opening against sibling services: permanent (base vs base,
    weekday + time) plus bounded (vs each sibling override over its date range, minus closings)."""
    conflicts: list[ScheduleConflict] = []
    candidate_segments = _opening_minute_segments(
        candidate.weekday, candidate.start_time, candidate.end_time
    )
    for sibling in ctx.siblings:
        for opening in sibling.base_by_weekday.values():
            sibling_segments = _opening_minute_segments(
                Weekday(opening.weekday), opening.start_time, opening.end_time
            )
            if _minute_segments_overlap(candidate_segments, sibling_segments):
                conflicts.append(_service_opening_conflict(
                    candidate.weekday, sibling, opening.id,
                    opening.start_time, opening.end_time, Weekday(opening.weekday), None,
                ))
                break
        for override in sibling.overrides:
            hit_date = _base_vs_override_hit(candidate, override, sibling, ctx)
            if hit_date is not None:
                conflicts.append(_service_opening_conflict(
                    candidate.weekday, sibling, override.id,
                    override.start_time, override.end_time,
                    Weekday(override.weekday) if override.weekday is not None else None, hit_date,
                ))
    return conflicts


def _base_vs_override_hit(
        candidate: _OpeningCandidate,
        override: OpeningOverrideEntity,
        sibling: _ServiceSchedule,
        ctx: _OverlapContext,
) -> date | None:
    """Earliest date in the sibling override's range where the candidate base opening overlaps it
    (candidate open that weekday and not closed, sibling not closed), or ``None``."""
    for d in _iter_dates(override.date_start, override.date_end):
        if not _covers_date(override.date_start, override.date_end, override.weekday, d):
            continue
        if _service_closed_on(sibling, ctx.venue_closings, d):
            continue
        sibling_open, sibling_close = _opening_window(d, override.start_time, override.end_time)
        for delta in (-1, 0, 1):
            x = d + timedelta(days=delta)
            if _WEEKDAYS[x.weekday()] != candidate.weekday or _candidate_closed_on(ctx, x):
                continue
            cand_open, cand_close = _opening_window(x, candidate.start_time, candidate.end_time)
            if _windows_overlap(cand_open, cand_close, sibling_open, sibling_close):
                return d
    return None


def _override_candidate_conflicts(candidate: _OverrideCandidate, ctx: _OverlapContext) -> list[ScheduleConflict]:
    """Conflicts of a proposed opening override against sibling services: iterate the candidate's
    dates, resolve each sibling's effective window (minus closings) around each date, and compare.
    At most one conflict per sibling (the earliest date)."""
    hits: dict[UUID, ScheduleConflict] = {}
    for d in _iter_dates(candidate.date_start, candidate.date_end):
        if not _covers_date(candidate.date_start, candidate.date_end, candidate.weekday, d):
            continue
        if _candidate_closed_on(ctx, d):
            continue
        cand_open, cand_close = _opening_window(d, candidate.start_time, candidate.end_time)
        for sibling in ctx.siblings:
            if sibling.service.id in hits:
                continue
            for delta in (-1, 0, 1):
                x = d + timedelta(days=delta)
                if _service_closed_on(sibling, ctx.venue_closings, x):
                    continue
                effective = _effective_row_on(sibling, x)
                if effective is None:
                    continue
                row, s_start, s_end = effective
                sibling_open, sibling_close = _opening_window(x, s_start, s_end)
                if _windows_overlap(cand_open, cand_close, sibling_open, sibling_close):
                    hits[sibling.service.id] = _service_opening_conflict(
                        candidate.weekday, sibling, row.id, s_start, s_end,
                        Weekday(row.weekday) if row.weekday is not None else None, d,
                    )
                    break
    return list(hits.values())


def _self_overnight_overlap_dates(
        candidate: _OverrideCandidate, own: _ServiceSchedule, venue_closings: list[VenueClosingEntity],
) -> list[date]:
    """Dates where the candidate override's overnight spillover would overlap the service's own
    opening (base or another override) on the adjacent day, or vice versa. Same-day is excluded —
    an override intentionally replaces the base for that day, that's not a conflict."""
    hits: list[date] = []
    for d in _iter_dates(candidate.date_start, candidate.date_end):
        if not _covers_date(candidate.date_start, candidate.date_end, candidate.weekday, d):
            continue
        if _service_closed_on(own, venue_closings, d):
            continue
        cand_open, cand_close = _opening_window(d, candidate.start_time, candidate.end_time)
        for delta in (-1, 1):
            x = d + timedelta(days=delta)
            if _service_closed_on(own, venue_closings, x):
                continue
            effective = _effective_row_on(own, x)
            if effective is None:
                continue
            _, s_start, s_end = effective
            x_open, x_close = _opening_window(x, s_start, s_end)
            if _windows_overlap(cand_open, cand_close, x_open, x_close):
                hits.append(d)
    return hits


async def ensure_no_self_overnight_overlap_for_override(
        service: ServiceEntity, candidate: _OverrideCandidate, exclude_override_id: UUID | None = None,
) -> None:
    """Raise HTTP 422 if a candidate override's overnight hours would overlap the service's own
    opening (base or another override) on the adjacent day. A 422, not 409, since this is the
    candidate being internally inconsistent with the rest of its own service's schedule, not a
    conflict with another service (which has its own preview UI — see SERVICE_OPENING)."""
    snapshot = await load_venue_schedule_snapshot(service.venue_id)
    own = next((s for s in snapshot.schedules if s.service.id == service.id), None)
    if own is None:
        return
    if exclude_override_id is not None:
        own = _ServiceSchedule(
            service=own.service,
            base_by_weekday=own.base_by_weekday,
            overrides=[o for o in own.overrides if o.id != exclude_override_id],
            closings=own.closings,
        )
    if _self_overnight_overlap_dates(candidate, own, snapshot.venue_closings):
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail="This override's overnight hours would overlap the service's own opening "
                   "on the following day",
        )


async def _load_overlap_context(service_id: UUID, venue_id: UUID) -> _OverlapContext:
    """Split the venue snapshot into the cross-service overlap context: sibling schedules (every
    service except the one being edited), venue closings, and the edited service's own closings."""
    snapshot = await load_venue_schedule_snapshot(venue_id)
    siblings = [s for s in snapshot.schedules if s.service.id != service_id]
    candidate_closings = next(
        (s.closings for s in snapshot.schedules if s.service.id == service_id), []
    )
    return _OverlapContext(siblings, snapshot.venue_closings, candidate_closings)


async def ensure_no_cross_service_opening_overlap_for_openings(
        service_id: UUID, venue_id: UUID, openings: list[OpeningUpsertRequest],
) -> None:
    """Raise HTTP 409 if any proposed base opening overlaps another service of the venue."""
    ctx = await _load_overlap_context(service_id, venue_id)
    for opening in openings:
        candidate = _OpeningCandidate(opening.weekday, opening.start_time, opening.end_time)
        conflicts = _base_candidate_conflicts(candidate, ctx)
        if conflicts:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail=f"These hours overlap another service ({conflicts[0].conflicting_service_name}) "
                       f"of the venue",
            )


async def ensure_no_cross_service_opening_overlap_for_override(
        service_id: UUID, venue_id: UUID, candidate: _OverrideCandidate,
) -> None:
    """Raise HTTP 409 if a proposed opening override overlaps another service of the venue."""
    ctx = await _load_overlap_context(service_id, venue_id)
    conflicts = _override_candidate_conflicts(candidate, ctx)
    if conflicts:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail=f"This override overlaps another service ({conflicts[0].conflicting_service_name}) "
                   f"of the venue",
        )


async def find_service_opening_conflicts_for(
        service_id: UUID, query: OpeningConflictQuery,
) -> ConflictsResponse:
    """Read-only preview: which of the venue's other services a candidate base opening would
    overlap. Lock-free mirror of the openings-upsert cross-service check."""
    service = await find_service_or_throw(service_id)
    ctx = await _load_overlap_context(service_id, service.venue_id)
    candidate = _OpeningCandidate(query.weekday, query.start_time, query.end_time)
    return ConflictsResponse(conflicts=_base_candidate_conflicts(candidate, ctx))


async def find_service_opening_override_cross_service_conflicts_for(
        service_id: UUID, query: ConflictQuery,
) -> list[ScheduleConflict]:
    """Cross-service overlaps a candidate opening override would introduce, one candidate per
    weekday in the query. Returns empty when the query carries no times to compare."""
    if query.start_time is None or query.end_time is None:
        return []
    service = await find_service_or_throw(service_id)
    ctx = await _load_overlap_context(service_id, service.venue_id)
    conflicts: list[ScheduleConflict] = []
    for weekday in normalize_weekdays(query.weekdays):
        candidate = _OverrideCandidate(
            query.date_start, query.date_end, weekday, query.start_time, query.end_time,
        )
        conflicts.extend(_override_candidate_conflicts(candidate, ctx))
    return conflicts


#
# A read-only, in-memory snapshot of a venue's whole schedule, so the reservation domain can
# re-validate existing bookings against the *current* schedule without a query per reservation
# (see the reservation-schedule-invalidation policy: schedule edits are non-destructive; the
# reservation section flags what no longer fits). Reasons are plain strings the caller maps to
# its own enum (keeps this layer free of a reservation-schema import).


@dataclass
class VenueScheduleSnapshot:
    """All services of a venue with their openings/overrides/closings, plus venue closings and
    per-service capacity overrides, preloaded once for repeated in-memory slot resolution."""

    schedules: list[_ServiceSchedule]
    venue_closings: list[VenueClosingEntity]
    capacity_overrides_by_service: dict[UUID, list[CapacityOverrideEntity]]


async def load_venue_schedule_snapshot(venue_id: UUID) -> VenueScheduleSnapshot:
    """Preload the full current schedule of a venue's non-deleted services for violation and
    over-capacity checks."""
    session = get_sql_session()
    services = list((await session.scalars(
        select(ServiceEntity).where(
            ServiceEntity.venue_id == venue_id,
            ServiceEntity.deleted_at.is_(None),
        )
    )).all())
    service_ids = [s.id for s in services]
    openings = list((await session.scalars(
        select(OpeningEntity).where(OpeningEntity.service_id.in_(service_ids))
    )).all()) if service_ids else []
    overrides = list((await session.scalars(
        select(OpeningOverrideEntity).where(OpeningOverrideEntity.service_id.in_(service_ids))
    )).all()) if service_ids else []
    closings = list((await session.scalars(
        select(ServiceClosingEntity).where(ServiceClosingEntity.service_id.in_(service_ids))
    )).all()) if service_ids else []
    capacity_overrides = list((await session.scalars(
        select(CapacityOverrideEntity).where(CapacityOverrideEntity.service_id.in_(service_ids))
    )).all()) if service_ids else []
    venue_closings = list((await session.scalars(
        select(VenueClosingEntity).where(VenueClosingEntity.venue_id == venue_id)
    )).all())
    schedules = [
        _ServiceSchedule(
            service=service,
            base_by_weekday={Weekday(o.weekday): o for o in openings if o.service_id == service.id},
            overrides=[o for o in overrides if o.service_id == service.id],
            closings=[c for c in closings if c.service_id == service.id],
        )
        for service in services
    ]
    capacity_overrides_by_service: dict[UUID, list[CapacityOverrideEntity]] = {
        service.id: [c for c in capacity_overrides if c.service_id == service.id]
        for service in services
    }
    return VenueScheduleSnapshot(
        schedules=schedules,
        venue_closings=venue_closings,
        capacity_overrides_by_service=capacity_overrides_by_service,
    )


class SlotInfo(NamedTuple):
    """The open slot a reservation instant falls in: the service, the business date, the effective
    seat capacity (opening capacity + capacity-override deltas), and the open/close window."""

    service: ServiceEntity
    business_date: date
    capacity: int
    opens_at: datetime
    closes_at: datetime


def resolve_slot(snapshot: VenueScheduleSnapshot, reservation_local: datetime) -> SlotInfo | str:
    """Resolve the venue slot a reservation at ``reservation_local`` (naive venue-local) falls in.

    Returns a `SlotInfo` when a service is open then, or a reason string when not: ``"closed"`` (a
    venue/service closing covers the date) or ``"no_service"`` (nothing opens then). The instant is
    matched against its own date's opening first, then the previous date's (which only reaches it
    if that opening runs overnight); the first covering service wins, and that opening's date is the
    business date whose closings and capacity overrides apply. Turn-fit is not checked here — that's
    a hard violation, separate from capacity.
    """
    for schedule in snapshot.schedules:
        for business_date in (reservation_local.date(), reservation_local.date() - timedelta(days=1)):
            effective = _effective_row_on(schedule, business_date)
            if effective is None:
                continue
            row, start_time, end_time = effective
            opens_at, closes_at = _opening_window(business_date, start_time, end_time)
            if not (opens_at <= reservation_local < closes_at):
                continue
            if _service_closed_on(schedule, snapshot.venue_closings, business_date):
                return "closed"
            delta = sum(
                c.capacity_delta
                for c in snapshot.capacity_overrides_by_service.get(schedule.service.id, [])
                if _covers_date(c.date_start, c.date_end, c.weekday, business_date)
            )
            return SlotInfo(
                service=schedule.service,
                business_date=business_date,
                capacity=row.capacity + delta,
                opens_at=opens_at,
                closes_at=closes_at,
            )
    return "no_service"


def resolve_bookable_slot_or_throw(
        snapshot: VenueScheduleSnapshot, reservation_local: datetime,
) -> SlotInfo:
    """The slot a reservation must be booked into, or HTTP 409 if no service is open then.
    Reservations are anchored to venue + datetime, not to a service — the service is derived here
    (so a reservation survives later service edits)."""
    slot = resolve_slot(snapshot, reservation_local)
    if slot == "closed":
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT, detail="The venue is closed at the requested time",
        )
    if isinstance(slot, str):
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT, detail="No service is open at the requested time",
        )
    return slot


def reservation_violation(snapshot: VenueScheduleSnapshot, reservation_local: datetime) -> str | None:
    """Why a reservation at ``reservation_local`` no longer fits the current schedule, or ``None``
    if it still does. ``"closed"``/``"no_service"`` come from `resolve_slot`; ``"outside_hours"``
    means the turn no longer fits the open window. Capacity is handled separately (over-capacity)."""
    slot = resolve_slot(snapshot, reservation_local)
    if isinstance(slot, str):
        return slot
    turn = timedelta(minutes=slot.service.turn_time_m)
    if reservation_local < slot.opens_at or reservation_local + turn > slot.closes_at:
        return "outside_hours"
    return None
