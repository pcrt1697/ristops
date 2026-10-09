import logging
from datetime import date, datetime, time, timedelta, UTC
from http import HTTPStatus
from typing import NamedTuple
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select, delete, exists, ScalarResult, ColumnElement

from ristops_be_reservation.domain.models import (
    ReservationViolation, WEEKDAYS, Weekday, weekday_of,
)
from ristops_be_reservation.domain.service.entities import (
    ClosingEntity, ClosingServiceEntity, OpeningEntity, ServiceEntity,
)
from ristops_be_reservation.domain.service.schema import (
    ClosingCreateRequest, ClosingResponse, ClosingSearchQuery, ClosingUpdateRequest,
    OpeningsUpsertRequest, ServiceCreationRequest, ServiceListQuery, ServiceResponse,
    ServiceUpdateRequest,
)
from ristops_be_reservation.domain.venue.service import ensure_venue_accepts_config_changes
from ristops_be_reservation.services.resource import publish_resource_created_event, publish_resource_deleted_event
from ristops_lib_core.schema.authz import ResourceType
from ristops_lib_core.schema.pagination import Page
from ristops_lib_sql.engine import get_sql_session
from ristops_lib_sql.search import PaginatedSearchQueryExecutor, SearchQueryExecutor

_logger = logging.getLogger(__name__)


async def create_service(request: ServiceCreationRequest) -> ServiceEntity:
    """Create a new service under a venue.

    A service with no openings yet cannot overlap anything. So the overlap check here only
    matters once hours are added — it runs anyway, since a validity period alone is enough to
    make the state checkable and keeps the write paths symmetric.
    """
    await ensure_venue_accepts_config_changes(request.venue_id, for_update=True)
    session = get_sql_session()
    service = ServiceEntity(
        venue_id=request.venue_id,
        name=request.name,
        description=request.description,
        date_from=request.date_from,
        date_to=request.date_to,
        capacity=request.capacity,
    )
    session.add(service)
    await session.flush()
    await session.refresh(service)
    await ensure_no_service_overlap(service.id, service.venue_id)
    await publish_resource_created_event(
        str(service.id),
        ResourceType.SERVICE,
        str(request.venue_id),
        ResourceType.VENUE,
    )
    _logger.info("Created service: %s", service.id)
    return service


async def find_service_or_throw(
        service_id: UUID,
        include_deleted: bool = False,
        for_update: bool = False,
) -> ServiceEntity:
    """Return the service with the given ID, or raise HTTP 404.

    Deleted services are excluded by default; set ``include_deleted=True`` to fetch them anyway
    (e.g. to resolve a service still referenced by an existing reservation).

    Set ``for_update=True`` from a mutating path that needs to serialize against concurrent
    bookings on the same service: it takes a ``SELECT ... FOR UPDATE`` row lock, held until the
    transaction commits. Leave it false on read paths so plain GETs never block.
    """
    session = get_sql_session()
    conditions = [ServiceEntity.id == service_id]
    if not include_deleted:
        conditions.append(ServiceEntity.deleted_at.is_(None))
    stmt = select(ServiceEntity).where(*conditions).limit(1)
    if for_update:
        stmt = stmt.with_for_update()
    result: ScalarResult[ServiceEntity] = await session.scalars(stmt)
    service = result.one_or_none()
    if service is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Service not found")
    return service


async def update_service(service_id: UUID, request: ServiceUpdateRequest) -> ServiceEntity:
    """Update a service. Only fields present in the request body are modified. Raises HTTP 404
    if the service is not found, HTTP 409 if its venue is not accepting config changes or if the
    new validity period makes it overlap another service of the venue.

    Shrinking the validity period or the capacity under existing bookings is allowed: schedule
    edits are non-destructive, and the bookings left behind are flagged on read instead.
    """
    service = await find_service_or_throw(service_id)
    # Lock the venue row to serialize concurrent schedule writes across its services while the
    # overlap check reads their openings.
    await ensure_venue_accepts_config_changes(service.venue_id, for_update=True)
    fields_to_update = request.model_fields_set

    if "name" in fields_to_update and request.name is not None:
        service.name = request.name
    if "description" in fields_to_update:
        service.description = request.description
    if "date_from" in fields_to_update and request.date_from is not None:
        service.date_from = request.date_from
    if "date_to" in fields_to_update:
        service.date_to = request.date_to
    if "capacity" in fields_to_update and request.capacity is not None:
        service.capacity = request.capacity

    session = get_sql_session()
    await session.flush()
    await session.refresh(service)
    if service.date_to is not None and service.date_to < service.date_from:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail="date_to must not be earlier than date_from",
        )
    await ensure_no_service_overlap(service_id, service.venue_id)
    _logger.info("Updated service: %s", service_id)
    return service


def _build_service_conditions(query: ServiceListQuery, scope: None) -> list[ColumnElement[bool]]:
    """Build the WHERE conditions from the user filter. The date filter selects services whose
    validity period overlaps the window, treating a null ``date_to`` as open-ended."""
    conditions = [ServiceEntity.venue_id == query.venue_id]
    if query.name is not None:
        conditions.append(ServiceEntity.name.ilike(f"%{query.name}%"))
    if query.date_from is not None:
        conditions.append(
            (ServiceEntity.date_to.is_(None)) | (ServiceEntity.date_to >= query.date_from)
        )
    if query.date_to is not None:
        conditions.append(ServiceEntity.date_from <= query.date_to)
    if not query.include_deleted:
        conditions.append(ServiceEntity.deleted_at.is_(None))
    return conditions


_service_list_executor: SearchQueryExecutor[ServiceListQuery, None, ServiceEntity, ServiceResponse] = (
    SearchQueryExecutor(
        entity_class=ServiceEntity,
        response_class=ServiceResponse,
        condition_builder=_build_service_conditions,
    )
)


async def list_services(query: ServiceListQuery) -> list[ServiceResponse]:
    """Return services matching the given filters, sorted per the query. Not paginated."""
    return await _service_list_executor.execute(query, None)


async def remove_service(service_id: UUID) -> None:
    """Soft-delete the service with the given ID. Raises HTTP 404 if not found.

    Bookings keep their reference to it — `find_service_or_throw(include_deleted=True)` still
    resolves them — and are reported as violated from then on.
    """
    service = await find_service_or_throw(service_id)
    await ensure_venue_accepts_config_changes(service.venue_id)
    service.deleted_at = datetime.now(UTC)
    session = get_sql_session()
    await session.flush()
    await publish_resource_deleted_event(str(service_id), ResourceType.SERVICE)
    _logger.info("Deleted service: %s", service_id)


async def upsert_service_openings(
        service_id: UUID,
        request: OpeningsUpsertRequest,
) -> list[OpeningEntity]:
    """Replace the full set of openings for a service: existing openings are dropped and the
    submitted list is inserted fresh.

    No diff/reconcile-in-place — an opening's `id` carries no identity anything else references,
    so there is nothing to preserve across a replace. Duplicate weekdays and overnight spillover
    are rejected at the schema layer (`OpeningsUpsertRequest`); an overlap with another service
    of the venue is rejected here.
    """
    service = await find_service_or_throw(service_id)
    # Lock the venue row to serialize concurrent schedule writes across the venue's services
    # while the overlap check reads their openings.
    await ensure_venue_accepts_config_changes(service.venue_id, for_update=True)

    session = get_sql_session()
    await session.execute(
        delete(OpeningEntity).where(OpeningEntity.service_id == service_id)
    )

    openings = [
        OpeningEntity(
            service_id=service_id,
            weekday=item.weekday,
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
    await ensure_no_service_overlap(service_id, service.venue_id)
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


async def _resolve_venue_services_or_throw(venue_id: UUID, service_ids: list[UUID]) -> list[UUID]:
    """Validate that every ID names a live service of the venue, returning them de-duplicated.
    Raises HTTP 404 for an unknown service and HTTP 422 for one belonging to another venue."""
    unique = list(dict.fromkeys(service_ids))
    session = get_sql_session()
    found = list((await session.scalars(
        select(ServiceEntity).where(
            ServiceEntity.id.in_(unique),
            ServiceEntity.deleted_at.is_(None),
        )
    )).all())
    by_id = {service.id: service for service in found}
    missing = [service_id for service_id in unique if service_id not in by_id]
    if missing:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f"Service not found: {', '.join(str(service_id) for service_id in missing)}",
        )
    foreign = [service_id for service_id, service in by_id.items() if service.venue_id != venue_id]
    if foreign:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail=f"Service does not belong to this venue: "
                   f"{', '.join(str(service_id) for service_id in foreign)}",
        )
    return unique


async def _set_closing_services(closing_id: UUID, service_ids: list[UUID]) -> None:
    """Replace the set of services a closing applies to."""
    session = get_sql_session()
    await session.execute(
        delete(ClosingServiceEntity).where(ClosingServiceEntity.closing_id == closing_id)
    )
    session.add_all([
        ClosingServiceEntity(closing_id=closing_id, service_id=service_id)
        for service_id in service_ids
    ])
    await session.flush()


async def _closing_service_ids(closing_ids: list[UUID]) -> dict[UUID, list[UUID]]:
    """The service IDs each of the given closings applies to, keyed by closing ID."""
    by_closing: dict[UUID, list[UUID]] = {closing_id: [] for closing_id in closing_ids}
    if not closing_ids:
        return by_closing
    session = get_sql_session()
    rows = (await session.execute(
        select(ClosingServiceEntity.closing_id, ClosingServiceEntity.service_id)
        .where(ClosingServiceEntity.closing_id.in_(closing_ids))
    )).all()
    for closing_id, service_id in rows:
        by_closing[closing_id].append(service_id)
    return by_closing


async def _to_closing_response(closing: ClosingEntity) -> ClosingResponse:
    """Map a closing entity to its response, filling in the services it applies to."""
    response = ClosingResponse.model_validate(closing, from_attributes=True)
    response.service_ids = (await _closing_service_ids([closing.id]))[closing.id]
    return response


async def create_closing(venue_id: UUID, request: ClosingCreateRequest) -> ClosingResponse:
    """Create a closing over a date range for one or more of the venue's services.

    Creating a closing can only ever remove openings from the calendar, so it cannot introduce an
    overlap between two services — no overlap check is needed here, unlike on update and delete.
    """
    await ensure_venue_accepts_config_changes(venue_id, for_update=True)
    service_ids = await _resolve_venue_services_or_throw(venue_id, request.service_ids)

    session = get_sql_session()
    closing = ClosingEntity(
        venue_id=venue_id,
        date_from=request.date_from,
        date_to=request.date_to,
        description=request.description,
    )
    session.add(closing)
    await session.flush()
    await session.refresh(closing)
    await _set_closing_services(closing.id, service_ids)
    _logger.info(
        "Created closing %s on venue %s for %d service(s)", closing.id, venue_id, len(service_ids),
    )
    return await _to_closing_response(closing)


async def find_closing_or_throw(venue_id: UUID, closing_id: UUID) -> ClosingEntity:
    """Return the closing with the given ID under the given venue, or raise HTTP 404."""
    session = get_sql_session()
    result: ScalarResult[ClosingEntity] = await session.scalars(
        select(ClosingEntity)
        .where(ClosingEntity.id == closing_id, ClosingEntity.venue_id == venue_id)
        .limit(1)
    )
    closing = result.one_or_none()
    if closing is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Closing not found")
    return closing


async def update_closing(
        venue_id: UUID, closing_id: UUID, request: ClosingUpdateRequest,
) -> ClosingResponse:
    """Update a closing. Only fields present in the request body are modified; ``service_ids``
    replaces the full set of targeted services.

    Shrinking a closing, or dropping a service from it, can re-expose an overlap it was keeping
    apart — so the venue's services are re-checked afterwards and the change is rejected with
    HTTP 409 if one surfaces.
    """
    await ensure_venue_accepts_config_changes(venue_id, for_update=True)
    closing = await find_closing_or_throw(venue_id, closing_id)
    fields_to_update = request.model_fields_set

    if "date_from" in fields_to_update and request.date_from is not None:
        closing.date_from = request.date_from
    if "date_to" in fields_to_update and request.date_to is not None:
        closing.date_to = request.date_to
    if "description" in fields_to_update:
        closing.description = request.description
    if "service_ids" in fields_to_update and request.service_ids is not None:
        service_ids = await _resolve_venue_services_or_throw(venue_id, request.service_ids)
        await _set_closing_services(closing_id, service_ids)

    session = get_sql_session()
    await session.flush()
    await session.refresh(closing)
    if closing.date_to < closing.date_from:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail="date_to must not be earlier than date_from",
        )
    await ensure_venue_services_do_not_overlap(venue_id)
    _logger.info("Updated closing: %s", closing_id)
    return await _to_closing_response(closing)


async def remove_closing(venue_id: UUID, closing_id: UUID) -> None:
    """Delete a closing. Rejected with HTTP 409 when removing it would leave two of the venue's
    services open at the same time — the closing is what keeps them apart."""
    await ensure_venue_accepts_config_changes(venue_id, for_update=True)
    closing = await find_closing_or_throw(venue_id, closing_id)
    session = get_sql_session()
    await session.delete(closing)
    await session.flush()
    await ensure_venue_services_do_not_overlap(venue_id)
    _logger.info("Deleted closing: %s", closing_id)


def _build_closing_conditions(query: ClosingSearchQuery, venue_id: UUID) -> list[ColumnElement[bool]]:
    """Scope to the venue, overlap the `[date_from, date_to]` window (either bound optional), and
    optionally narrow to the closings applying to one service."""
    conditions: list[ColumnElement[bool]] = [ClosingEntity.venue_id == venue_id]
    if query.date_from is not None:
        conditions.append(ClosingEntity.date_to >= query.date_from)
    if query.date_to is not None:
        conditions.append(ClosingEntity.date_from <= query.date_to)
    if query.service_id is not None:
        conditions.append(exists().where(
            ClosingServiceEntity.closing_id == ClosingEntity.id,
            ClosingServiceEntity.service_id == query.service_id,
        ))
    return conditions


_closing_search_executor = PaginatedSearchQueryExecutor[
    ClosingSearchQuery, UUID, ClosingEntity, ClosingResponse
](
    entity_class=ClosingEntity,
    response_class=ClosingResponse,
    condition_builder=_build_closing_conditions,
)


async def search_closings(venue_id: UUID, query: ClosingSearchQuery) -> Page[ClosingResponse]:
    """Return the venue's closings matching the query, paginated and sorted, each carrying the
    services it applies to (resolved in one query for the whole page)."""
    page = await _closing_search_executor.execute(query, venue_id)
    by_closing = await _closing_service_ids([item.id for item in page.items])
    for item in page.items:
        item.service_ids = by_closing.get(item.id, [])
    return page


# No two services of a venue may be open at the same instant: a booking names its service, but
# staff picking from two services offered at the same hour is a configuration mistake, not a
# choice. Two services conflict on a date only when *both* actually run it — validity covers it,
# a weekday opening covers it, and no closing removes it. That last clause is what makes a
# one-shot service possible: close the regular service for the date, and the special one fits.
#
# A window spans at most two calendar days (an overnight opening closes the next morning), so a
# candidate opening on weekday W can only meet a sibling opening on W-1, W or W+1. Whether two
# such openings overlap depends on the times and that day offset alone, not on which concrete
# dates they land on — so the times are compared once against a reference week, and only the
# pairs that do overlap go looking for a date where both services are actually running.

# A Monday, used to place a weekday's window on a concrete date for time-only comparisons.
_REFERENCE_MONDAY = date(2024, 1, 1)


def _reference_date(weekday: Weekday) -> date:
    """The date in the reference week falling on ``weekday``."""
    return _REFERENCE_MONDAY + timedelta(days=WEEKDAYS.index(weekday))


def _openings_overlap(
        candidate: ServiceSchedule,
        candidate_weekday: Weekday,
        sibling: ServiceSchedule,
        sibling_weekday: Weekday,
        day_offset: int,
) -> bool:
    """Whether the candidate's opening on ``candidate_weekday`` overlaps the sibling's opening on
    ``sibling_weekday``, when the sibling's date sits ``day_offset`` days after the candidate's.
    Windows are half-open, so touching boundaries do not overlap."""
    candidate_opening = candidate.openings_by_weekday[candidate_weekday]
    sibling_opening = sibling.openings_by_weekday[sibling_weekday]
    candidate_date = _reference_date(candidate_weekday)
    a_open, a_close = opening_window(
        candidate_date, candidate_opening.start_time, candidate_opening.end_time,
    )
    b_open, b_close = opening_window(
        candidate_date + timedelta(days=day_offset),
        sibling_opening.start_time,
        sibling_opening.end_time,
    )
    return a_open < b_close and b_open < a_close


def _conflict_date(
        candidate: ServiceSchedule,
        sibling: ServiceSchedule,
        weekday: Weekday,
        day_offset: int,
) -> date | None:
    """A concrete date on which both services run their overlapping openings, or ``None`` if a
    closing on one side or the other removes every occurrence.

    ``weekday`` is the candidate's; the sibling's date is ``day_offset`` days later. Only dates
    inside both validity periods count. When neither period is bounded the answer is always yes:
    closings are finite date ranges, so they can never remove every occurrence of a weekly
    opening — the scan is simply extended past the last of them to name one.
    """
    lower = max(candidate.service.date_from, sibling.service.date_from - timedelta(days=day_offset))
    uppers = [
        bound for bound in (
            candidate.service.date_to,
            sibling.service.date_to - timedelta(days=day_offset)
            if sibling.service.date_to is not None else None,
        ) if bound is not None
    ]
    upper = min(uppers) if uppers else None

    first = lower + timedelta(days=(WEEKDAYS.index(weekday) - lower.weekday()) % 7)
    if upper is None:
        closings = candidate.closings + sibling.closings
        last_closing = max((c.date_to for c in closings), default=first)
        limit = max(first, last_closing) + timedelta(days=7)
    else:
        limit = upper

    on_date = first
    while on_date <= limit:
        if (
                not closing_covers(candidate.closings, on_date)
                and not closing_covers(sibling.closings, on_date + timedelta(days=day_offset))
        ):
            return on_date
        on_date += timedelta(days=7)
    return None


def find_overlap(
        candidate: ServiceSchedule, siblings: list[ServiceSchedule],
) -> tuple[ServiceSchedule, date] | None:
    """The first sibling service that is open at the same time as the candidate, with the date it
    happens on, or ``None`` when the candidate is free of overlaps."""
    for sibling in siblings:
        for candidate_weekday in candidate.openings_by_weekday:
            for day_offset in (-1, 0, 1):
                sibling_weekday = WEEKDAYS[(WEEKDAYS.index(candidate_weekday) + day_offset) % 7]
                if sibling_weekday not in sibling.openings_by_weekday:
                    continue
                if not _openings_overlap(
                        candidate, candidate_weekday, sibling, sibling_weekday, day_offset,
                ):
                    continue
                on_date = _conflict_date(candidate, sibling, candidate_weekday, day_offset)
                if on_date is not None:
                    return sibling, on_date
    return None


async def ensure_no_service_overlap(service_id: UUID, venue_id: UUID) -> None:
    """Raise HTTP 409 if the given service is open at the same time as another service of the
    venue on any date both of them run.

    Called from every write that can create an overlap: a service's validity or openings
    changing, and a closing being shrunk or deleted (which can re-expose one it was hiding).
    Creating a closing never can. The caller is expected to hold the venue row lock, so
    concurrent writes across the venue's services serialize behind this check.
    """
    snapshot = await load_venue_schedule_snapshot(venue_id)
    candidate = snapshot.for_service(service_id)
    if candidate is None:
        return
    siblings = [s for s in snapshot.schedules if s.service.id != service_id]
    overlap = find_overlap(candidate, siblings)
    if overlap is None:
        return
    sibling, on_date = overlap
    raise HTTPException(
        status_code=HTTPStatus.CONFLICT,
        detail=f"Service '{candidate.service.name}' is open at the same time as "
               f"'{sibling.service.name}' on {on_date.isoformat()}. Close one of them for that "
               f"date, or change its hours.",
    )


async def ensure_venue_services_do_not_overlap(venue_id: UUID) -> None:
    """Raise HTTP 409 if any two services of the venue are open at the same time. Used by the
    closing writes, where the change can re-expose an overlap between any pair, not just one
    service's."""
    snapshot = await load_venue_schedule_snapshot(venue_id)
    for index, candidate in enumerate(snapshot.schedules):
        overlap = find_overlap(candidate, snapshot.schedules[index + 1:])
        if overlap is None:
            continue
        sibling, on_date = overlap
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail=f"Service '{candidate.service.name}' would be open at the same time as "
                   f"'{sibling.service.name}' on {on_date.isoformat()}. That closing is what "
                   f"keeps them apart.",
        )


# Resolving "is this service open at this instant?" from the stored rules. A service occupies a
# window on a business date when its validity covers the date, it has an opening on that
# weekday, and no closing linked to it covers the date. Windows are half-open — a 15:00 close and
# a 15:00 open do not overlap — and are returned as concrete datetimes, so an overnight opening
# needs no wrap-around math from the caller.


class ServiceSchedule(NamedTuple):
    """One service with everything needed to resolve its windows in memory."""

    service: ServiceEntity
    openings_by_weekday: dict[Weekday, OpeningEntity]
    closings: list[ClosingEntity]


class VenueScheduleSnapshot(NamedTuple):
    """Every non-deleted service of a venue with its openings and closings, preloaded once for
    repeated in-memory resolution."""

    schedules: list[ServiceSchedule]

    def for_service(self, service_id: UUID) -> ServiceSchedule | None:
        """The schedule of one of the venue's services, or None when it is not in the snapshot
        (deleted, or belonging to another venue)."""
        return next(
            (s for s in self.schedules if s.service.id == service_id), None,
        )


class SlotInfo(NamedTuple):
    """The window a service occupies on one business date."""

    service: ServiceEntity
    business_date: date
    capacity: int
    opens_at: datetime
    closes_at: datetime


def opening_window(on_date: date, start_time: time, end_time: time) -> tuple[datetime, datetime]:
    """Concrete open/close datetimes for an opening on ``on_date``. An opening whose ``end_time``
    is not after its ``start_time`` runs overnight, so its close lands on the following day."""
    opens_at = datetime.combine(on_date, start_time)
    close_date = on_date if end_time > start_time else on_date + timedelta(days=1)
    return opens_at, datetime.combine(close_date, end_time)


def service_runs_on(service: ServiceEntity, on_date: date) -> bool:
    """Whether ``on_date`` falls inside the service's validity period."""
    if on_date < service.date_from:
        return False
    return service.date_to is None or on_date <= service.date_to


def closing_covers(closings: list[ClosingEntity], on_date: date) -> bool:
    """Whether any of the given closings covers ``on_date``."""
    return any(c.date_from <= on_date <= c.date_to for c in closings)


def service_slot_on(
        schedule: ServiceSchedule, business_date: date,
) -> tuple[SlotInfo, bool] | None:
    """The window a service occupies on ``business_date`` and whether a closing removes it, or
    ``None`` when the service does not run that day at all (outside its validity, or no opening
    on that weekday).

    The window is returned even when closed, so a caller matching an instant can tell "closed
    then" from "closed, but the instant wasn't in this window anyway".
    """
    service = schedule.service
    if not service_runs_on(service, business_date):
        return None
    opening = schedule.openings_by_weekday.get(weekday_of(business_date))
    if opening is None:
        return None
    opens_at, closes_at = opening_window(business_date, opening.start_time, opening.end_time)
    slot = SlotInfo(
        service=service,
        business_date=business_date,
        capacity=service.capacity,
        opens_at=opens_at,
        closes_at=closes_at,
    )
    return slot, closing_covers(schedule.closings, business_date)


def resolve_day_slots(
        snapshot: VenueScheduleSnapshot, business_date: date,
) -> tuple[list[SlotInfo], bool]:
    """Every service of the venue open on ``business_date``, and whether the date is *closed out*.

    The flag distinguishes "closed" from "never scheduled": it is True only when at least one
    service runs that date but a closing removes every one of them. An overnight opening is
    reported on the date it opens on.
    """
    slots: list[SlotInfo] = []
    closed_any = False
    for schedule in snapshot.schedules:
        resolved = service_slot_on(schedule, business_date)
        if resolved is None:
            continue
        slot, closed = resolved
        if closed:
            closed_any = True
            continue
        slots.append(slot)
    return slots, closed_any and not slots


def slot_covering(schedule: ServiceSchedule, local: datetime) -> tuple[SlotInfo, bool] | None:
    """The slot of ``schedule`` containing the naive venue-local instant ``local``, with its
    closed flag, or ``None`` when the service holds no window over that instant.

    The instant is matched against its own date's opening first, then the previous date's — which
    only reaches it when that opening runs overnight.
    """
    for business_date in (local.date(), local.date() - timedelta(days=1)):
        resolved = service_slot_on(schedule, business_date)
        if resolved is None:
            continue
        slot, closed = resolved
        if slot.opens_at <= local < slot.closes_at:
            return slot, closed
    return None


def business_day_bounds(schedule: ServiceSchedule, business_date: date) -> tuple[datetime, datetime]:
    """The naive venue-local ``[start, end)`` holding every booking of the service that belongs to
    ``business_date``: the calendar day, shifted past the previous night's overnight tail and
    stretched to this date's own close when that runs past midnight. It spans the whole day, not
    just the opening window, so bookings the hours no longer cover stay in it."""
    start = datetime.combine(business_date, time.min)
    end = start + timedelta(days=1)
    previous = service_slot_on(schedule, business_date - timedelta(days=1))
    current = service_slot_on(schedule, business_date)
    if previous is not None:
        start = max(start, previous[0].closes_at)
    if current is not None:
        end = max(end, current[0].closes_at)
    return start, end


def reservation_violation(
        schedule: ServiceSchedule | None, local: datetime,
) -> ReservationViolation | None:
    """Why a booking at ``local`` (naive venue-local) no longer fits its service's current
    schedule, or ``None`` if it still does.

    ``NO_SERVICE`` when the service is gone from the snapshot (deleted) or no longer runs that
    date at all, ``CLOSED`` when a closing covers the date, and ``OUTSIDE_HOURS`` when the service
    still runs that day but the booking now falls outside the window. Capacity is handled
    separately: overflow belongs to a service-date, not to one booking.
    """
    if schedule is None:
        return ReservationViolation.NO_SERVICE
    covering = slot_covering(schedule, local)
    if covering is not None:
        return ReservationViolation.CLOSED if covering[1] else None
    # Nothing covers the instant: distinguish "the service still runs that day, just not then"
    # from "the service no longer runs that day at all".
    resolved = service_slot_on(schedule, local.date())
    if resolved is None:
        return ReservationViolation.NO_SERVICE
    return ReservationViolation.CLOSED if resolved[1] else ReservationViolation.OUTSIDE_HOURS


async def load_service_closings(service_ids: list[UUID]) -> dict[UUID, list[ClosingEntity]]:
    """The closings covering each of the given services, keyed by service ID."""
    by_service: dict[UUID, list[ClosingEntity]] = {service_id: [] for service_id in service_ids}
    if not service_ids:
        return by_service
    session = get_sql_session()
    rows = (await session.execute(
        select(ClosingServiceEntity.service_id, ClosingEntity)
        .join(ClosingEntity, ClosingEntity.id == ClosingServiceEntity.closing_id)
        .where(ClosingServiceEntity.service_id.in_(service_ids))
    )).all()
    for service_id, closing in rows:
        by_service[service_id].append(closing)
    return by_service


async def load_schedules(services: list[ServiceEntity]) -> list[ServiceSchedule]:
    """Preload openings and closings for the given services, in two queries."""
    service_ids = [service.id for service in services]
    session = get_sql_session()
    openings = list((await session.scalars(
        select(OpeningEntity).where(OpeningEntity.service_id.in_(service_ids))
    )).all()) if service_ids else []
    closings_by_service = await load_service_closings(service_ids)
    return [
        ServiceSchedule(
            service=service,
            openings_by_weekday={
                Weekday(o.weekday): o for o in openings if o.service_id == service.id
            },
            closings=closings_by_service[service.id],
        )
        for service in services
    ]


async def load_venue_schedule_snapshot(venue_id: UUID) -> VenueScheduleSnapshot:
    """Preload the full current schedule of a venue's non-deleted services, for the calendar and
    for violation checks."""
    session = get_sql_session()
    services = list((await session.scalars(
        select(ServiceEntity).where(
            ServiceEntity.venue_id == venue_id,
            ServiceEntity.deleted_at.is_(None),
        )
    )).all())
    return VenueScheduleSnapshot(schedules=await load_schedules(services))
