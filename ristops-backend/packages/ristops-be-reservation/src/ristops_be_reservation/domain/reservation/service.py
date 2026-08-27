import logging
from collections import defaultdict
from datetime import date, datetime, timedelta, UTC
from http import HTTPStatus
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import select, ScalarResult, ColumnElement

from ristops_be_reservation.domain.reservation.entities import ReservationEntity
from ristops_be_reservation.domain.reservation.schema import (
    ReservationCreationRequest, ReservationUpdateRequest, ReservationResponse, ReservationSearchQuery,
    ReservationActionRequest, ReservationActionType, ReservationStatus, ReservationViolation,
    CheckInReservationAction, OverCapacitySlot,
)
from ristops_be_reservation.domain.schedule.service import (
    resolve_bookable_slot_or_throw, load_venue_schedule_snapshot, reservation_violation,
    resolve_slot, SlotInfo, VenueScheduleSnapshot,
)
from ristops_be_reservation.domain.service.service import find_service_or_throw
from ristops_be_reservation.domain.venue.entities import VenueEntity
from ristops_be_reservation.domain.venue.service import (
    find_venue_or_throw, check_venue_accepts_reservations,
)
from ristops_be_reservation.services.resource import publish_resource_created_event
from ristops_lib_core.schema.authz import ResourceType
from ristops_lib_core.schema.pagination import Page
from ristops_lib_core.utils import to_local_naive, to_utc_instant
from ristops_lib_sql.engine import get_sql_session
from ristops_lib_sql.search import PaginatedSearchQueryExecutor

_logger = logging.getLogger(__name__)

# Reservation statuses that hold a seat and therefore count against capacity.
_OCCUPYING_STATUSES: tuple[ReservationStatus, ...] = (
    ReservationStatus.PENDING,
    ReservationStatus.CONFIRMED,
    ReservationStatus.CHECKED_IN,
)

# Statuses whose future bookings can be "violated" by a later schedule change (still to be
# honored, not yet arrived/resolved). checked_in already happened; terminal ones are resolved.
_VIOLATION_ELIGIBLE_STATUSES: tuple[ReservationStatus, ...] = (
    ReservationStatus.PENDING,
    ReservationStatus.CONFIRMED,
)

# Target status each action transitions the reservation to.
_ACTION_TARGET_STATUS: dict[ReservationActionType, ReservationStatus] = {
    ReservationActionType.CONFIRM: ReservationStatus.CONFIRMED,
    ReservationActionType.REJECT: ReservationStatus.REJECTED,
    ReservationActionType.CANCEL: ReservationStatus.CANCELED,
    ReservationActionType.CHECK_IN: ReservationStatus.CHECKED_IN,
    ReservationActionType.NO_SHOW: ReservationStatus.NO_SHOW,
    ReservationActionType.WITHDRAW: ReservationStatus.WITHDRAWN,
}


def _build_reservation_conditions(query: ReservationSearchQuery, tz: ZoneInfo) -> list[ColumnElement[bool]]:
    """WHERE conditions from the filter: venue (mandatory), optional status set and venue-local
    date range (converted to UTC instant bounds)."""
    conditions: list[ColumnElement[bool]] = [ReservationEntity.venue_id == query.venue_id]
    if query.status:
        conditions.append(ReservationEntity.status.in_([s.value for s in query.status]))
    start, end = query.date_bounds(tz)
    if start is not None:
        conditions.append(ReservationEntity.reservation_date >= start)
    if end is not None:
        conditions.append(ReservationEntity.reservation_date < end)
    return conditions


_reservation_list_executor: PaginatedSearchQueryExecutor[
    ReservationSearchQuery, ZoneInfo, ReservationEntity, ReservationResponse
] = PaginatedSearchQueryExecutor(
    entity_class=ReservationEntity,
    response_class=ReservationResponse,
    condition_builder=_build_reservation_conditions,
)


def _to_response(reservation: ReservationEntity, tz: ZoneInfo) -> ReservationResponse:
    """Map a reservation entity to its response, presenting ``reservation_date`` as venue-local
    wall-clock. ``violation`` is left null here — read paths set it via `_violation_for`."""
    response = ReservationResponse.model_validate(reservation, from_attributes=True)
    response.reservation_date = to_local_naive(reservation.reservation_date, tz)
    return response


def _violation_for(
        instant: datetime,
        status: str,
        snapshot: VenueScheduleSnapshot,
        tz: ZoneInfo,
        now: datetime,
) -> ReservationViolation | None:
    """The schedule violation of a stored reservation (UTC ``instant``, string ``status``) under
    the current schedule, or None. Only future bookings in a live status can be violated."""
    if status not in _VIOLATION_ELIGIBLE_STATUSES or instant <= now:
        return None
    reason = reservation_violation(snapshot, to_local_naive(instant, tz))
    return ReservationViolation(reason) if reason is not None else None


async def _ensure_slot_available(
        venue: VenueEntity,
        reservation_local: datetime,
        party_size: int,
        exclude_reservation_id: UUID | None = None,
) -> datetime:
    """Validate that ``party_size`` can be booked at ``reservation_local`` (naive venue-local) at
    ``venue``, raising HTTP 409 otherwise, and return the UTC instant to store.

    The service is inferred from venue + datetime (reservations carry no service reference). Checks,
    in order: the venue has a service open then (venue/service closings, opening + overrides,
    including overnight openings — via ``resolve_bookable_slot_or_throw``); advance-notice lead
    time; the requested time sits on a slot boundary and the whole turn fits before closing; and
    enough seats remain once existing overlapping reservations are counted against the resolved
    capacity. Seats are counted by venue + time overlap rather than by service — equivalent while a
    venue's services don't overlap in time (service-conflict handling is a later task).
    """
    tz = ZoneInfo(venue.timezone)
    instant = to_utc_instant(reservation_local, tz)

    snapshot = await load_venue_schedule_snapshot(venue.id)
    slot = resolve_bookable_slot_or_throw(snapshot, reservation_local)
    service = slot.service
    # Lock the inferred service so concurrent bookings under it serialize on the capacity check.
    await find_service_or_throw(service.id, for_update=True)

    now = datetime.now(UTC)
    if instant < now + timedelta(minutes=service.advance_notice_m):
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail=f"Reservations require at least {service.advance_notice_m} minutes advance notice",
        )

    turn = timedelta(minutes=service.turn_time_m)
    if reservation_local < slot.opens_at or reservation_local + turn > slot.closes_at:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail="The requested time is outside the service opening hours",
        )
    offset_minutes = int((reservation_local - slot.opens_at).total_seconds() // 60)
    if offset_minutes % service.slot_interval_m != 0:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail=f"The requested time is not a valid reservation slot "
                   f"(every {service.slot_interval_m} minutes from opening)",
        )

    session = get_sql_session()
    conditions: list[ColumnElement[bool]] = [
        ReservationEntity.venue_id == venue.id,
        ReservationEntity.status.in_(_OCCUPYING_STATUSES),
        ReservationEntity.reservation_date > instant - turn,
        ReservationEntity.reservation_date < instant + turn,
    ]
    if exclude_reservation_id is not None:
        conditions.append(ReservationEntity.id != exclude_reservation_id)
    result: ScalarResult[ReservationEntity] = await session.scalars(
        select(ReservationEntity).where(*conditions)
    )
    booked = sum(row.party_size for row in result.all())
    if booked + party_size > slot.capacity:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail="Not enough seats available for the requested time",
        )
    return instant


async def create_reservation(request: ReservationCreationRequest) -> ReservationResponse:
    """Create a new reservation at a venue.

    Requires the venue to be ACTIVE, then infers the service open at the requested time and
    validates slot availability (opening hours, slot alignment, turn fit and seat capacity) under
    a lock on that service before inserting. The reservation is anchored to venue + datetime only.
    ``reservation_date`` is accepted as naive venue-local wall-clock and stored as the
    corresponding UTC instant.
    """
    venue = await find_venue_or_throw(request.venue_id)
    check_venue_accepts_reservations(venue)

    instant = await _ensure_slot_available(
        venue, request.reservation_date, request.party_size
    )

    session = get_sql_session()
    reservation = ReservationEntity(
        venue_id=request.venue_id,
        status=ReservationStatus.PENDING,
        reservation_date=instant,
        party_size=request.party_size,
        contact_name=request.contact_name,
        contact_phone_number=request.contact_phone_number,
        contact_email=request.contact_email,
        notes=request.notes,
    )
    session.add(reservation)
    await session.flush()
    await session.refresh(reservation)
    await publish_resource_created_event(
        str(reservation.id),
        ResourceType.RESERVATION,
        str(request.venue_id),
        ResourceType.VENUE,
    )
    _logger.info("Created reservation: %s", reservation.id)
    return _to_response(reservation, ZoneInfo(venue.timezone))


async def find_reservation_or_throw(reservation_id: UUID, for_update: bool = False) -> ReservationEntity:
    """Return the reservation with the given ID, or raise HTTP 404.

    Set ``for_update=True`` from a mutating path that needs to serialize against concurrent
    writes on the same reservation: it takes a ``SELECT ... FOR UPDATE`` row lock, held until
    the transaction commits. Leave it false on read paths so plain GETs never block.
    """
    session = get_sql_session()
    stmt = select(ReservationEntity).where(ReservationEntity.id == reservation_id).limit(1)
    if for_update:
        stmt = stmt.with_for_update()
    result: ScalarResult[ReservationEntity] = await session.scalars(stmt)
    reservation = result.one_or_none()
    if reservation is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Reservation not found")
    return reservation


async def get_reservation(reservation_id: UUID) -> ReservationResponse:
    """Return a single reservation, with ``reservation_date`` as venue-local wall-clock and a
    computed ``violation`` if it no longer fits the current schedule."""
    reservation = await find_reservation_or_throw(reservation_id)
    venue = await find_venue_or_throw(reservation.venue_id)
    tz = ZoneInfo(venue.timezone)
    snapshot = await load_venue_schedule_snapshot(venue.id)
    response = _to_response(reservation, tz)
    response.violation = _violation_for(
        reservation.reservation_date, reservation.status, snapshot, tz, datetime.now(UTC),
    )
    return response


async def update_reservation(reservation_id: UUID, request: ReservationUpdateRequest) -> ReservationResponse:
    """Update a reservation. Only fields present in the request body are modified.

    When an availability-affecting field (``reservation_date`` or ``party_size``) changes, the
    venue must be ACTIVE and the resulting slot is re-validated the same way a create is — the
    service is re-inferred from venue + datetime and hours, slot alignment, turn fit and seat
    capacity are checked (excluding this reservation from the seat count). ``reservation_date`` is
    accepted as naive venue-local wall-clock and stored as a UTC instant.
    """
    reservation = await find_reservation_or_throw(reservation_id, for_update=True)
    venue = await find_venue_or_throw(reservation.venue_id)
    tz = ZoneInfo(venue.timezone)
    fields_to_update = request.model_fields_set

    if "contact_name" in fields_to_update and request.contact_name is not None:
        reservation.contact_name = request.contact_name
    if "contact_phone_number" in fields_to_update:
        reservation.contact_phone_number = request.contact_phone_number
    if "notes" in fields_to_update:
        reservation.notes = request.notes

    changes_slot = bool({"reservation_date", "party_size"} & fields_to_update)
    if changes_slot:
        check_venue_accepts_reservations(venue)
        reservation_local = (
            request.reservation_date if request.reservation_date is not None
            else to_local_naive(reservation.reservation_date, tz)
        )
        party_size = request.party_size if request.party_size is not None else reservation.party_size

        instant = await _ensure_slot_available(
            venue, reservation_local, party_size, exclude_reservation_id=reservation.id
        )
        reservation.party_size = party_size
        reservation.reservation_date = instant

    session = get_sql_session()
    await session.flush()
    await session.refresh(reservation)
    _logger.info("Updated reservation: %s", reservation_id)
    return _to_response(reservation, tz)


async def _list_violated_reservations(
        query: ReservationSearchQuery, tz: ZoneInfo, snapshot: VenueScheduleSnapshot, now: datetime,
) -> Page[ReservationResponse]:
    """The 'needs attention' view: every future live (pending/confirmed) reservation of the venue
    that no longer fits the current schedule. Violations are computed, not stored, so this can't
    be a SQL predicate — fetch the (bounded) candidate set, filter in memory, paginate the result.
    The status filter is implied (pending/confirmed) and ignored here."""
    session = get_sql_session()
    conditions: list[ColumnElement[bool]] = [
        ReservationEntity.venue_id == query.venue_id,
        ReservationEntity.status.in_([s.value for s in _VIOLATION_ELIGIBLE_STATUSES]),
        ReservationEntity.reservation_date > now,
    ]
    start, end = query.date_bounds(tz)
    if start is not None:
        conditions.append(ReservationEntity.reservation_date >= start)
    if end is not None:
        conditions.append(ReservationEntity.reservation_date < end)
    rows = list((await session.scalars(
        select(ReservationEntity).where(*conditions).order_by(ReservationEntity.reservation_date)
    )).all())

    violated: list[ReservationResponse] = []
    for row in rows:
        reason = reservation_violation(snapshot, to_local_naive(row.reservation_date, tz))
        if reason is None:
            continue
        response = _to_response(row, tz)
        response.violation = ReservationViolation(reason)
        violated.append(response)

    offset = query.page * query.page_size
    return Page.create(violated[offset:offset + query.page_size], len(violated), query)


async def list_reservations(query: ReservationSearchQuery) -> Page[ReservationResponse]:
    """Return reservations for a venue matching the given filters, sorted per the query,
    paginated. ``reservation_date`` is presented as venue-local wall-clock, and each item carries
    a computed ``violation`` (null when it still fits) — the venue schedule is preloaded once so
    this costs no per-row query. ``violations_only`` switches to the 'needs attention' view."""
    venue = await find_venue_or_throw(query.venue_id)
    tz = ZoneInfo(venue.timezone)
    snapshot = await load_venue_schedule_snapshot(venue.id)
    now = datetime.now(UTC)

    if query.violations_only:
        return await _list_violated_reservations(query, tz, snapshot, now)

    page = await _reservation_list_executor.execute(query, tz)
    for item in page.items:
        item.violation = _violation_for(item.reservation_date, item.status, snapshot, tz, now)
        item.reservation_date = to_local_naive(item.reservation_date, tz)
    return page


def _peak_concurrent_seats(entries: list[tuple[datetime, int, int]]) -> int:
    """Max concurrent booked seats across half-open ``[start, start+turn)`` windows. Each entry is
    ``(start_local, party_size, turn_minutes)``. Touching windows don't overlap: at a shared
    instant, seat releases are applied before takes."""
    events: list[tuple[datetime, int]] = []
    for start, party, turn_m in entries:
        events.append((start, party))
        events.append((start + timedelta(minutes=turn_m), -party))
    events.sort(key=lambda event: (event[0], event[1]))
    peak = current = 0
    for _instant, delta in events:
        current += delta
        peak = max(peak, current)
    return peak


async def list_over_capacity_slots(venue_id: UUID) -> list[OverCapacitySlot]:
    """Slots (service + venue-local date) where live future bookings now exceed the effective
    capacity. Computed on read against the current schedule — a capacity/hours cut can push a slot
    over without touching the reservations (see the invalidation policy). Bookings that no longer
    resolve to any open slot are a hard violation (surfaced via the list's ``violation``), not an
    overflow, so they're skipped here."""
    venue = await find_venue_or_throw(venue_id)
    tz = ZoneInfo(venue.timezone)
    snapshot = await load_venue_schedule_snapshot(venue_id)
    now = datetime.now(UTC)
    session = get_sql_session()
    rows = list((await session.scalars(
        select(ReservationEntity).where(
            ReservationEntity.venue_id == venue_id,
            ReservationEntity.status.in_([s.value for s in _OCCUPYING_STATUSES]),
            ReservationEntity.reservation_date > now,
        )
    )).all())

    entries_by_slot: dict[tuple[UUID, date], list[tuple[datetime, int, int]]] = defaultdict(list)
    ids_by_slot: dict[tuple[UUID, date], list[UUID]] = defaultdict(list)
    slot_by_key: dict[tuple[UUID, date], SlotInfo] = {}
    for row in rows:
        local = to_local_naive(row.reservation_date, tz)
        slot = resolve_slot(snapshot, local)
        if not isinstance(slot, SlotInfo):
            continue  # closed / no service — a hard violation, not a capacity overflow
        key = (slot.service.id, slot.business_date)
        entries_by_slot[key].append((local, row.party_size, slot.service.turn_time_m))
        ids_by_slot[key].append(row.id)
        slot_by_key[key] = slot

    over: list[OverCapacitySlot] = []
    for key, entries in entries_by_slot.items():
        slot = slot_by_key[key]
        peak = _peak_concurrent_seats(entries)
        if peak > slot.capacity:
            over.append(OverCapacitySlot(
                service_id=slot.service.id,
                service_name=slot.service.name,
                business_date=slot.business_date,
                capacity=slot.capacity,
                peak_booked=peak,
                reservation_ids=ids_by_slot[key],
            ))
    over.sort(key=lambda slot: (slot.business_date, slot.service_name))
    return over


async def update_reservation_status(
        reservation_id: UUID, request: ReservationActionRequest,
) -> ReservationResponse:
    """Apply a status-change action to a reservation: set the target status, and for a check-in
    also set the arrival time (from the request, or the current venue-local time if omitted).
    Optional ``notes`` on the action replace the reservation's notes.

    The required permission is enforced per-action by the router. There is no from-state
    transition validation yet — the action sets the status directly (the state machine is a
    later task); ``pending`` is not an action (it is only the creation status)."""
    reservation = await find_reservation_or_throw(reservation_id, for_update=True)
    venue = await find_venue_or_throw(reservation.venue_id)
    tz = ZoneInfo(venue.timezone)

    reservation.status = _ACTION_TARGET_STATUS[request.action]
    if "notes" in request.model_fields_set:
        reservation.notes = request.notes
    if isinstance(request, CheckInReservationAction):
        reservation.arrival_time = (
            request.arrival_time
            or datetime.now(tz).time().replace(second=0, microsecond=0)
        )

    session = get_sql_session()
    await session.flush()
    await session.refresh(reservation)
    _logger.info("Applied '%s' action to reservation %s", request.action.value, reservation_id)
    return _to_response(reservation, tz)
