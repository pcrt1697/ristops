import logging
from datetime import date, datetime, time, timedelta, UTC
from http import HTTPStatus
from typing import NamedTuple
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import select, ScalarResult, ColumnElement, and_, false, or_

from ristops_be_reservation.domain.models import ReservationViolation
from ristops_be_reservation.domain.reservation.entities import ReservationEntity
from ristops_be_reservation.domain.reservation.schema import (
    ReservationCreationRequest, ReservationUpdateRequest, ReservationResponse, ReservationSearchQuery,
    ReservationActionRequest, ReservationActionType, ReservationStatus,
    CheckInReservationAction, CalendarQuery, CalendarResponse, CalendarDay, CalendarServiceSummary,
    ClosedServiceSummary, DeletedServiceSummary,
)
from ristops_be_reservation.domain.service.entities import ServiceEntity
from ristops_be_reservation.domain.service.service import (
    ServiceSchedule, SlotInfo, VenueScheduleSnapshot, business_day_bounds, find_service_or_throw,
    load_schedules,
    load_venue_schedule_snapshot, reservation_violation, resolve_day_slots, slot_covering,
)
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


async def _date_condition(
        query: ReservationSearchQuery, tz: ZoneInfo,
) -> ColumnElement[bool] | None:
    """Restrict a search to the business dates in ``[date_from, date_to]``, or ``None`` when no
    date is asked for.

    A booking's business date comes from its own service, since only an overnight service moves
    it off the calendar date. So each of the venue's services, deleted ones included, gets its own
    instant range, and the ranges are OR-ed together.
    """
    if query.date_from is None and query.date_to is None:
        return None
    conditions: list[ColumnElement[bool]] = [ServiceEntity.venue_id == query.venue_id]
    if query.service_id is not None:
        conditions.append(ServiceEntity.id == query.service_id)
    session = get_sql_session()
    services = list((await session.scalars(select(ServiceEntity).where(*conditions))).all())

    per_service: list[ColumnElement[bool]] = []
    for schedule in await load_schedules(services):
        in_range: list[ColumnElement[bool]] = [ReservationEntity.service_id == schedule.service.id]
        if query.date_from is not None:
            start = business_day_bounds(schedule, query.date_from)[0]
            in_range.append(ReservationEntity.reservation_date >= to_utc_instant(start, tz))
        if query.date_to is not None:
            end = business_day_bounds(schedule, query.date_to)[1]
            in_range.append(ReservationEntity.reservation_date < to_utc_instant(end, tz))
        per_service.append(and_(*in_range))
    return or_(*per_service) if per_service else false()


def _build_reservation_conditions(
        query: ReservationSearchQuery, date_condition: ColumnElement[bool] | None,
) -> list[ColumnElement[bool]]:
    """WHERE conditions from the filter: venue (mandatory), optional service, status set and
    business-date range."""
    conditions: list[ColumnElement[bool]] = [ReservationEntity.venue_id == query.venue_id]
    if query.service_id is not None:
        conditions.append(ReservationEntity.service_id == query.service_id)
    if query.status:
        conditions.append(ReservationEntity.status.in_([s.value for s in query.status]))
    if date_condition is not None:
        conditions.append(date_condition)
    return conditions


_reservation_list_executor: PaginatedSearchQueryExecutor[
    ReservationSearchQuery, ColumnElement[bool] | None, ReservationEntity, ReservationResponse
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
        service_id: UUID,
        status: str,
        snapshot: VenueScheduleSnapshot,
        tz: ZoneInfo,
        now: datetime,
) -> ReservationViolation | None:
    """The schedule violation of a stored reservation under the current schedule, or None. Only
    future bookings in a live status can be violated."""
    if status not in _VIOLATION_ELIGIBLE_STATUSES or instant <= now:
        return None
    return reservation_violation(snapshot.for_service(service_id), to_local_naive(instant, tz))


async def _load_service_schedule(service: ServiceEntity) -> ServiceSchedule:
    """Preload one service's openings and closings."""
    schedules = await load_schedules([service])
    return schedules[0]


async def _booked_seats(
        service_id: UUID,
        slot: SlotInfo,
        tz: ZoneInfo,
        exclude_reservation_id: UUID | None = None,
) -> int:
    """Seats already taken inside a service's window on one business date.

    The window itself is the bucket: a service holds exactly one window per business date, so any
    live booking whose instant falls in it belongs to that date. Bookings left outside by a later
    hours change are not counted — they are violations, reported per-reservation, not capacity.
    """
    session = get_sql_session()
    conditions: list[ColumnElement[bool]] = [
        ReservationEntity.service_id == service_id,
        ReservationEntity.status.in_([s.value for s in _OCCUPYING_STATUSES]),
        ReservationEntity.reservation_date >= to_utc_instant(slot.opens_at, tz),
        ReservationEntity.reservation_date < to_utc_instant(slot.closes_at, tz),
    ]
    if exclude_reservation_id is not None:
        conditions.append(ReservationEntity.id != exclude_reservation_id)
    result: ScalarResult[ReservationEntity] = await session.scalars(
        select(ReservationEntity).where(*conditions)
    )
    return sum(row.party_size for row in result.all())


async def _ensure_bookable(
        venue: VenueEntity,
        service_id: UUID,
        reservation_local: datetime,
        party_size: int,
        exclude_reservation_id: UUID | None = None,
) -> datetime:
    """Validate that ``party_size`` can be booked into ``service_id`` at ``reservation_local``
    (naive venue-local), raising HTTP 409 otherwise, and return the UTC instant to store.

    Checks, in order: the service belongs to the venue; it runs that date and the instant falls
    inside its opening window (an overnight window is matched against the previous business date
    too); no closing covers that date; and the seats already booked into the same window leave
    room for the party. The service row is locked first, so concurrent bookings into it serialize
    on the seat count.
    """
    service = await find_service_or_throw(service_id, for_update=True)
    if service.venue_id != venue.id:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail="The service does not belong to this venue",
        )

    schedule = await _load_service_schedule(service)
    covering = slot_covering(schedule, reservation_local)
    if covering is None:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail=f"'{service.name}' is not open at the requested time",
        )
    slot, closed = covering
    if closed:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail=f"'{service.name}' is closed on {slot.business_date.isoformat()}",
        )

    tz = ZoneInfo(venue.timezone)
    booked = await _booked_seats(service_id, slot, tz, exclude_reservation_id)
    if booked + party_size > slot.capacity:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail=f"Not enough seats left in '{service.name}' on "
                   f"{slot.business_date.isoformat()}: {slot.capacity - booked} of "
                   f"{slot.capacity} remaining",
        )
    return to_utc_instant(reservation_local, tz)


async def create_reservation(request: ReservationCreationRequest) -> ReservationResponse:
    """Create a new reservation at a venue, booked into one of its services.

    Requires the venue to be ACTIVE, then validates the requested time and party against that
    service's opening window, closings and capacity under a lock on the service.
    ``reservation_date`` is accepted as naive venue-local wall-clock and stored as the
    corresponding UTC instant.
    """
    venue = await find_venue_or_throw(request.venue_id)
    check_venue_accepts_reservations(venue)

    instant = await _ensure_bookable(
        venue, request.service_id, request.reservation_date, request.party_size,
    )

    session = get_sql_session()
    reservation = ReservationEntity(
        venue_id=request.venue_id,
        service_id=request.service_id,
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
        reservation.reservation_date, reservation.service_id, reservation.status,
        snapshot, tz, datetime.now(UTC),
    )
    return response


async def update_reservation(reservation_id: UUID, request: ReservationUpdateRequest) -> ReservationResponse:
    """Update a reservation. Only fields present in the request body are modified.

    When an availability-affecting field (``reservation_date``, ``party_size`` or ``service_id``)
    is given, the venue must be ACTIVE and the booking is re-validated against its service the
    same way a create is, excluding this reservation from the seat count. Giving a ``service_id``
    moves the booking onto that service, which is how one left on a closed or deleted service is
    rehomed.
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

    changes_booking = bool({"reservation_date", "party_size", "service_id"} & fields_to_update)
    if changes_booking:
        check_venue_accepts_reservations(venue)
        reservation_local = (
            request.reservation_date if request.reservation_date is not None
            else to_local_naive(reservation.reservation_date, tz)
        )
        party_size = request.party_size if request.party_size is not None else reservation.party_size
        service_id = request.service_id if request.service_id is not None else reservation.service_id

        instant = await _ensure_bookable(
            venue, service_id, reservation_local, party_size,
            exclude_reservation_id=reservation.id,
        )
        reservation.service_id = service_id
        reservation.party_size = party_size
        reservation.reservation_date = instant

    session = get_sql_session()
    await session.flush()
    await session.refresh(reservation)
    _logger.info("Updated reservation: %s", reservation_id)
    return _to_response(reservation, tz)


async def _list_violated_reservations(
        query: ReservationSearchQuery,
        date_condition: ColumnElement[bool] | None,
        tz: ZoneInfo,
        snapshot: VenueScheduleSnapshot,
        now: datetime,
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
    if query.service_id is not None:
        conditions.append(ReservationEntity.service_id == query.service_id)
    if date_condition is not None:
        conditions.append(date_condition)
    rows = list((await session.scalars(
        select(ReservationEntity).where(*conditions).order_by(ReservationEntity.reservation_date)
    )).all())

    violated: list[ReservationResponse] = []
    for row in rows:
        violation = reservation_violation(
            snapshot.for_service(row.service_id), to_local_naive(row.reservation_date, tz),
        )
        if violation is None:
            continue
        response = _to_response(row, tz)
        response.violation = violation
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
    date_condition = await _date_condition(query, tz)

    if query.violations_only:
        return await _list_violated_reservations(query, date_condition, tz, snapshot, now)

    page = await _reservation_list_executor.execute(query, date_condition)
    for item in page.items:
        item.violation = _violation_for(
            item.reservation_date, item.service_id, item.status, snapshot, tz, now,
        )
        item.reservation_date = to_local_naive(item.reservation_date, tz)
    return page


class _DayBookings(NamedTuple):
    """Live bookings resolved onto one (service, business date)."""

    seats: int
    count: int


async def _load_occupying_reservations(
        venue_id: UUID, instant_from: datetime, instant_to: datetime,
) -> list[ReservationEntity]:
    """Reservations of a venue that hold a seat within a half-open UTC instant range."""
    session = get_sql_session()
    result: ScalarResult[ReservationEntity] = await session.scalars(
        select(ReservationEntity).where(
            ReservationEntity.venue_id == venue_id,
            ReservationEntity.status.in_([s.value for s in _OCCUPYING_STATUSES]),
            ReservationEntity.reservation_date >= instant_from,
            ReservationEntity.reservation_date < instant_to,
        )
    )
    return list(result.all())


def _bookings_by_slot(
        rows: list[ReservationEntity], snapshot: VenueScheduleSnapshot, tz: ZoneInfo,
) -> dict[tuple[UUID, date], _DayBookings]:
    """Bucket reservations onto the (service, business date) each one currently falls in.

    Bookings that no longer land in their service's window are dropped: that is a violation,
    surfaced per-reservation, not a capacity figure.
    """
    by_slot: dict[tuple[UUID, date], _DayBookings] = {}
    for row in rows:
        schedule = snapshot.for_service(row.service_id)
        if schedule is None:
            continue
        covering = slot_covering(schedule, to_local_naive(row.reservation_date, tz))
        if covering is None:
            continue
        key = (row.service_id, covering[0].business_date)
        current = by_slot.get(key, _DayBookings(0, 0))
        by_slot[key] = _DayBookings(current.seats + row.party_size, current.count + 1)
    return by_slot


def _closed_services_by_date(
        rows: list[ReservationEntity], snapshot: VenueScheduleSnapshot, tz: ZoneInfo, now: datetime,
) -> dict[date, list[ClosedServiceSummary]]:
    """The services a closing removes from each business date while they still hold bookings that
    need staff attention, grouped by date.

    These are the bookings `reservation_violation` reports as closed. The services running that
    day do not list them, so the calendar would otherwise have no way to show them.
    """
    counts: dict[tuple[date, UUID], int] = {}
    for row in rows:
        if row.status not in _VIOLATION_ELIGIBLE_STATUSES or row.reservation_date <= now:
            continue
        schedule = snapshot.for_service(row.service_id)
        if schedule is None:
            continue
        covering = slot_covering(schedule, to_local_naive(row.reservation_date, tz))
        if covering is None or not covering[1]:
            continue
        key = (covering[0].business_date, row.service_id)
        counts[key] = counts.get(key, 0) + 1

    by_date: dict[date, list[ClosedServiceSummary]] = {}
    for (business_date, service_id), count in counts.items():
        schedule = snapshot.for_service(service_id)
        by_date.setdefault(business_date, []).append(ClosedServiceSummary(
            service_id=service_id,
            service_name=schedule.service.name,
            reservation_count=count,
        ))
    for closed_services in by_date.values():
        closed_services.sort(key=lambda summary: summary.service_name)
    return by_date


async def _deleted_services_by_date(
        rows: list[ReservationEntity], snapshot: VenueScheduleSnapshot, tz: ZoneInfo, now: datetime,
) -> dict[date, list[DeletedServiceSummary]]:
    """The deleted services that still hold bookings needing staff attention, grouped by the
    business date each booking falls on.

    A deleted service is not in the snapshot, so its schedule is loaded here to place each
    booking on the date of the window containing it. One outside every window is placed on its
    own calendar date.
    """
    live_ids = {schedule.service.id for schedule in snapshot.schedules}
    eligible = [
        row for row in rows
        if row.service_id not in live_ids
        and row.status in _VIOLATION_ELIGIBLE_STATUSES
        and row.reservation_date > now
    ]
    if not eligible:
        return {}

    session = get_sql_session()
    services = list((await session.scalars(
        select(ServiceEntity).where(ServiceEntity.id.in_({row.service_id for row in eligible}))
    )).all())
    schedules = {schedule.service.id: schedule for schedule in await load_schedules(services)}

    counts: dict[tuple[date, UUID], int] = {}
    for row in eligible:
        local = to_local_naive(row.reservation_date, tz)
        covering = slot_covering(schedules[row.service_id], local)
        key = (covering[0].business_date if covering else local.date(), row.service_id)
        counts[key] = counts.get(key, 0) + 1

    by_date: dict[date, list[DeletedServiceSummary]] = {}
    for (business_date, service_id), count in counts.items():
        by_date.setdefault(business_date, []).append(DeletedServiceSummary(
            service_id=service_id,
            service_name=schedules[service_id].service.name,
            reservation_count=count,
        ))
    for deleted_services in by_date.values():
        deleted_services.sort(key=lambda summary: summary.service_name)
    return by_date


def _calendar_summary(
        slot: SlotInfo, by_slot: dict[tuple[UUID, date], _DayBookings],
) -> CalendarServiceSummary:
    """Summarize one service running on one date against the bookings resolved onto it."""
    bookings = by_slot.get((slot.service.id, slot.business_date), _DayBookings(0, 0))
    return CalendarServiceSummary(
        service_id=slot.service.id,
        service_name=slot.service.name,
        opens_at=slot.opens_at,
        closes_at=slot.closes_at,
        capacity=slot.capacity,
        booked=bookings.seats,
        remaining=slot.capacity - bookings.seats,
        reservation_count=bookings.count,
        over_capacity=bookings.seats > slot.capacity,
    )


async def list_calendar_days(query: CalendarQuery) -> CalendarResponse:
    """Per-day, per-service occupancy of a venue over a date window — the month-grid summary and
    the source of what is still bookable on a day.

    For each business date in the window, resolves which services run (`resolve_day_slots`) and
    how full each is. Dates with neither a running service nor a closing are omitted, so a caller
    can render "nothing scheduled" by absence. Read-only: no lock, no validation.
    """
    venue = await find_venue_or_throw(query.venue_id)
    tz = ZoneInfo(venue.timezone)
    snapshot = await load_venue_schedule_snapshot(venue.id)

    # Widen the scan by a day on each side: an overnight opening on the day before the window can
    # hold bookings that land inside it, and vice versa.
    instant_from = to_utc_instant(datetime.combine(query.date_from - timedelta(days=1), time.min), tz)
    instant_to = to_utc_instant(datetime.combine(query.date_to + timedelta(days=2), time.min), tz)
    rows = await _load_occupying_reservations(query.venue_id, instant_from, instant_to)
    by_slot = _bookings_by_slot(rows, snapshot, tz)
    now = datetime.now(UTC)
    closed_by_date = _closed_services_by_date(rows, snapshot, tz, now)
    deleted_by_date = await _deleted_services_by_date(rows, snapshot, tz, now)

    days: list[CalendarDay] = []
    business_date = query.date_from
    while business_date <= query.date_to:
        slots, closed = resolve_day_slots(snapshot, business_date)
        if slots or closed or business_date in deleted_by_date:
            days.append(CalendarDay(
                business_date=business_date,
                closed=closed,
                services=[_calendar_summary(slot, by_slot) for slot in slots],
                closed_services=closed_by_date.get(business_date, []),
                deleted_services=deleted_by_date.get(business_date, []),
            ))
        business_date += timedelta(days=1)
    return CalendarResponse(days=days)


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
