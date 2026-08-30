import logging
from typing import NamedTuple
from datetime import date, datetime, time, timedelta, UTC
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
    CalendarQuery, CalendarResponse, CalendarDay, CalendarServiceSummary,
    AvailabilityQuery, AvailabilityResponse, ServiceAvailability, AvailabilitySlot,
    AvailabilityBlocker,
)
from ristops_be_reservation.domain.schedule.service import (
    resolve_bookable_slot_or_throw, load_venue_schedule_snapshot, reservation_violation,
    resolve_slot, resolve_day_slots, slot_times, SlotInfo, VenueScheduleSnapshot,
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
from ristops_lib_otel.tracing import traced
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


@traced("reservation.ensure_slot_available")
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
    if reservation_local not in slot_times(slot):
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


class _SlotBookings(NamedTuple):
    """The live bookings that currently resolve onto one (service, business date) slot.

    The lists are filled after construction as reservations are bucketed, so they are passed in
    explicitly rather than defaulted — a shared default would be the same list for every slot.
    """

    slot: SlotInfo
    entries: list[tuple[datetime, int, int]]
    reservation_ids: list[UUID]

    @property
    def peak_booked(self) -> int:
        """Peak concurrent booked seats over the slot's window."""
        return _peak_concurrent_seats(self.entries)


async def _load_occupying_reservations(
        venue_id: UUID, instant_from: datetime | None = None, instant_to: datetime | None = None,
) -> list[ReservationEntity]:
    """Reservations of a venue that hold a seat, optionally bounded to a half-open UTC instant
    range."""
    conditions: list[ColumnElement[bool]] = [
        ReservationEntity.venue_id == venue_id,
        ReservationEntity.status.in_([s.value for s in _OCCUPYING_STATUSES]),
    ]
    if instant_from is not None:
        conditions.append(ReservationEntity.reservation_date >= instant_from)
    if instant_to is not None:
        conditions.append(ReservationEntity.reservation_date < instant_to)
    session = get_sql_session()
    result: ScalarResult[ReservationEntity] = await session.scalars(
        select(ReservationEntity).where(*conditions)
    )
    return list(result.all())


def _bookings_by_slot(
        rows: list[ReservationEntity], snapshot: VenueScheduleSnapshot, tz: ZoneInfo,
) -> dict[tuple[UUID, date], _SlotBookings]:
    """Bucket reservations onto the slot each one currently resolves to.

    Bookings that no longer resolve to any open slot are dropped: that is a hard violation
    (surfaced per-reservation as ``violation``), not a capacity figure.
    """
    by_slot: dict[tuple[UUID, date], _SlotBookings] = {}
    for row in rows:
        local = to_local_naive(row.reservation_date, tz)
        slot = resolve_slot(snapshot, local)
        if not isinstance(slot, SlotInfo):
            continue
        bookings = by_slot.setdefault(
            (slot.service.id, slot.business_date), _SlotBookings(slot, [], []),
        )
        bookings.entries.append((local, row.party_size, slot.service.turn_time_m))
        bookings.reservation_ids.append(row.id)
    return by_slot


async def list_over_capacity_slots(venue_id: UUID) -> list[OverCapacitySlot]:
    """Slots (service + venue-local date) where live future bookings now exceed the effective
    capacity. Computed on read against the current schedule — a capacity/hours cut can push a slot
    over without touching the reservations (see the invalidation policy)."""
    venue = await find_venue_or_throw(venue_id)
    tz = ZoneInfo(venue.timezone)
    snapshot = await load_venue_schedule_snapshot(venue_id)
    rows = await _load_occupying_reservations(venue_id, instant_from=datetime.now(UTC))

    over = [
        OverCapacitySlot(
            service_id=bookings.slot.service.id,
            service_name=bookings.slot.service.name,
            business_date=bookings.slot.business_date,
            capacity=bookings.slot.capacity,
            peak_booked=bookings.peak_booked,
            reservation_ids=bookings.reservation_ids,
        )
        for bookings in _bookings_by_slot(rows, snapshot, tz).values()
        if bookings.peak_booked > bookings.slot.capacity
    ]
    over.sort(key=lambda slot: (slot.business_date, slot.service_name))
    return over


@traced("reservation.calendar")
async def list_calendar_days(query: CalendarQuery) -> CalendarResponse:
    """Per-day, per-service occupancy of a venue over a date window — the month-grid summary.

    For each business date in the window, resolves which services open (`resolve_day_slots`) and
    how full each is, reusing the same seat arithmetic as the over-capacity view. Dates with
    neither an open service nor a closing are omitted, so a caller can render "nothing scheduled"
    by absence. Read-only: no lock, no validation.
    """
    venue = await find_venue_or_throw(query.venue_id)
    tz = ZoneInfo(venue.timezone)
    snapshot = await load_venue_schedule_snapshot(venue.id)

    # Widen the scan by a day on each side: an overnight opening on the day before the window
    # can hold bookings that land inside it, and vice versa.
    instant_from = to_utc_instant(datetime.combine(query.date_from - timedelta(days=1), time.min), tz)
    instant_to = to_utc_instant(datetime.combine(query.date_to + timedelta(days=2), time.min), tz)
    rows = await _load_occupying_reservations(query.venue_id, instant_from, instant_to)
    by_slot = _bookings_by_slot(rows, snapshot, tz)

    days: list[CalendarDay] = []
    business_date = query.date_from
    while business_date <= query.date_to:
        slots, closed = resolve_day_slots(snapshot, business_date)
        if slots or closed:
            days.append(CalendarDay(
                business_date=business_date,
                closed=closed,
                services=[_calendar_summary(slot, by_slot) for slot in slots],
            ))
        business_date += timedelta(days=1)
    return CalendarResponse(days=days)


def _calendar_summary(
        slot: SlotInfo, by_slot: dict[tuple[UUID, date], _SlotBookings],
) -> CalendarServiceSummary:
    """Summarize one open service on one date against the bookings resolved onto it."""
    bookings = by_slot.get((slot.service.id, slot.business_date))
    peak = bookings.peak_booked if bookings is not None else 0
    return CalendarServiceSummary(
        service_id=slot.service.id,
        service_name=slot.service.name,
        opens_at=slot.opens_at,
        closes_at=slot.closes_at,
        capacity=slot.capacity,
        peak_booked=peak,
        reservation_count=len(bookings.reservation_ids) if bookings is not None else 0,
        over_capacity=peak > slot.capacity,
    )


@traced("reservation.availability")
async def list_availability(query: AvailabilityQuery) -> AvailabilityResponse:
    """Read-only preview of the slots a party could be booked into on one date (what a create
    would 409 on).

    Every service open that date is listed with its window, so a caller can render the day's shape
    even when nothing is bookable. Within a service, the slot grid comes from `slot_times` — the
    same helper the write path validates against — and each slot is scored against the seats
    already taken by overlapping bookings. Slots at or before ``now + advance_notice_m`` are
    omitted, so a past date yields services with no slots. Authorization and the definitive
    capacity check still happen on write, under a lock.
    """
    venue = await find_venue_or_throw(query.venue_id)
    tz = ZoneInfo(venue.timezone)
    snapshot = await load_venue_schedule_snapshot(venue.id)
    slots, closed = resolve_day_slots(snapshot, query.business_date)

    now_local = to_local_naive(datetime.now(UTC), tz)
    # A day's slots can only overlap bookings on the day before or after (an overnight opening
    # runs past midnight, and a turn started late still occupies the next morning).
    instant_from = to_utc_instant(datetime.combine(query.business_date - timedelta(days=1), time.min), tz)
    instant_to = to_utc_instant(datetime.combine(query.business_date + timedelta(days=2), time.min), tz)
    rows = [
        row for row in await _load_occupying_reservations(query.venue_id, instant_from, instant_to)
        if row.id != query.exclude_reservation_id
    ]
    booked_entries = [
        (to_local_naive(row.reservation_date, tz), row.party_size) for row in rows
    ]

    return AvailabilityResponse(
        business_date=query.business_date,
        closed=closed,
        services=[
            _service_availability(slot, booked_entries, now_local, query.party_size)
            for slot in slots
        ],
    )


def _service_availability(
        slot: SlotInfo,
        booked_entries: list[tuple[datetime, int]],
        now_local: datetime,
        party_size: int,
) -> ServiceAvailability:
    """Score one service's slot grid against the seats already booked around each slot."""
    turn = timedelta(minutes=slot.service.turn_time_m)
    earliest = now_local + timedelta(minutes=slot.service.advance_notice_m)

    slots: list[AvailabilitySlot] = []
    for slot_at in slot_times(slot):
        if slot_at <= earliest:
            continue
        booked = sum(
            party for start, party in booked_entries
            if slot_at - turn < start < slot_at + turn
        )
        remaining = slot.capacity - booked
        bookable = remaining >= party_size
        slots.append(AvailabilitySlot(
            slot_at=slot_at,
            booked=booked,
            remaining=remaining,
            bookable=bookable,
            blocker=None if bookable else AvailabilityBlocker.INSUFFICIENT_SEATS,
        ))

    return ServiceAvailability(
        service_id=slot.service.id,
        service_name=slot.service.name,
        business_date=slot.business_date,
        opens_at=slot.opens_at,
        closes_at=slot.closes_at,
        capacity=slot.capacity,
        turn_time_m=slot.service.turn_time_m,
        slot_interval_m=slot.service.slot_interval_m,
        slots=slots,
    )


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
