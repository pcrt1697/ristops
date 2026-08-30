from datetime import date, datetime, time
from enum import Enum
from typing import Annotated, Any

import strawberry

from ristops_bff_web.domain.reservation.service import (
    find_reservation, search_reservations, create_reservation, update_reservation,
    perform_reservation_action, reservation_over_capacity, reservation_calendar,
    reservation_availability,
)
from ristops_bff_web.graphql.pagination import Page, PaginationInput, SearchQueryParams, SortInput
from ristops_bff_web.graphql.types import EntityId



async def resolve_get_reservation(reservation_id: EntityId) -> "Reservation":
    return Reservation.from_dict(await find_reservation(reservation_id))


async def resolve_search_reservations(
        _input: Annotated[
            "ReservationSearchInput",
            strawberry.argument(description="Reservation search query.", name="input"),
        ]
) -> Page["Reservation"]:
    params = ReservationQueryParams(_input).build()
    page = await search_reservations(params)
    return Page.from_dict(page, Reservation.from_dict)


async def resolve_reservation_over_capacity(
        venue_id: Annotated[strawberry.ID, strawberry.argument(description="Venue ID.")],
) -> list["OverCapacitySlot"]:
    slots = await reservation_over_capacity(venue_id)
    return [OverCapacitySlot.from_dict(slot) for slot in slots]


async def resolve_reservation_calendar(
        venue_id: Annotated[strawberry.ID, strawberry.argument(description="Venue ID.")],
        date_from: Annotated[date, strawberry.argument(description="First business date (inclusive).")],
        date_to: Annotated[date, strawberry.argument(description="Last business date (inclusive).")],
) -> list["CalendarDay"]:
    days = await reservation_calendar({
        "venue_id": str(venue_id),
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
    })
    return [CalendarDay.from_dict(day) for day in days]


async def resolve_reservation_availability(
        venue_id: Annotated[strawberry.ID, strawberry.argument(description="Venue ID.")],
        business_date: Annotated[date, strawberry.argument(description="Business date to check.")],
        party_size: Annotated[int, strawberry.argument(description="Number of people to seat.")],
        exclude_reservation_id: Annotated[
            strawberry.ID | None,
            strawberry.argument(description="Reservation to leave out of the seat count (when editing)."),
        ] = None,
) -> "DayAvailability":
    params: dict[str, Any] = {
        "venue_id": str(venue_id),
        "business_date": business_date.isoformat(),
        "party_size": party_size,
    }
    if exclude_reservation_id is not None:
        params["exclude_reservation_id"] = str(exclude_reservation_id)
    return DayAvailability.from_dict(await reservation_availability(params))


async def resolve_create_reservation(
        _input: Annotated[
            "CreateReservationInput",
            strawberry.argument(description="Reservation information.", name="input"),
        ]
) -> "Reservation":
    return Reservation.from_dict(await create_reservation(_create_payload(_input)))


async def resolve_update_reservation(
        reservation_id: EntityId,
        _input: Annotated[
            "UpdateReservationInput",
            strawberry.argument(description="Reservation fields to update.", name="input"),
        ]
) -> "Reservation":
    return Reservation.from_dict(await update_reservation(reservation_id, _update_payload(_input)))


async def _apply_action(reservation_id: str, payload: dict[str, Any]) -> "Reservation":
    return Reservation.from_dict(await perform_reservation_action(reservation_id, payload))


async def resolve_confirm_reservation(reservation_id: EntityId, notes: str | None = None) -> "Reservation":
    return await _apply_action(reservation_id, _action_payload("confirm", notes))


async def resolve_reject_reservation(reservation_id: EntityId, notes: str | None = None) -> "Reservation":
    return await _apply_action(reservation_id, _action_payload("reject", notes))


async def resolve_cancel_reservation(reservation_id: EntityId, notes: str | None = None) -> "Reservation":
    return await _apply_action(reservation_id, _action_payload("cancel", notes))


async def resolve_check_in_reservation(
        reservation_id: EntityId,
        arrival_time: Annotated[
            time | None,
            strawberry.argument(description="Venue-local arrival time; defaults to now if omitted."),
        ] = None,
        notes: str | None = None,
) -> "Reservation":
    return await _apply_action(
        reservation_id, _action_payload("check_in", notes, arrival_time),
    )


async def resolve_no_show_reservation(reservation_id: EntityId, notes: str | None = None) -> "Reservation":
    return await _apply_action(reservation_id, _action_payload("no_show", notes))


async def resolve_withdraw_reservation(reservation_id: EntityId, notes: str | None = None) -> "Reservation":
    return await _apply_action(reservation_id, _action_payload("withdraw", notes))



def _create_payload(inp: "CreateReservationInput") -> dict[str, Any]:
    payload: dict[str, Any] = {
        "venue_id": inp.venue_id,
        "contact_name": inp.contact_name,
        "party_size": inp.party_size,
        "reservation_date": inp.reservation_date.isoformat(),
    }
    if inp.contact_phone_number is not None:
        payload["contact_phone_number"] = inp.contact_phone_number
    if inp.contact_email is not None:
        payload["contact_email"] = inp.contact_email
    if inp.notes is not None:
        payload["notes"] = inp.notes
    return payload


def _update_payload(inp: "UpdateReservationInput") -> dict[str, Any]:
    """Send only provided fields, so unset ones aren't touched. contact_phone_number and notes
    default to UNSET, so an explicit null is forwarded and clears the field (an omitted one is
    left unchanged); the other fields can't be cleared, so a null there is simply ignored."""
    payload: dict[str, Any] = {}
    if inp.contact_name is not None:
        payload["contact_name"] = inp.contact_name
    if inp.party_size is not None:
        payload["party_size"] = inp.party_size
    if inp.reservation_date is not None:
        payload["reservation_date"] = inp.reservation_date.isoformat()
    if inp.contact_phone_number is not strawberry.UNSET:
        payload["contact_phone_number"] = inp.contact_phone_number
    if inp.notes is not strawberry.UNSET:
        payload["notes"] = inp.notes
    return payload


def _action_payload(action: str, notes: str | None, arrival_time: time | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"action": action}
    if notes is not None:
        payload["notes"] = notes
    if arrival_time is not None:
        payload["arrival_time"] = arrival_time.isoformat()
    return payload



@strawberry.enum(description="Lifecycle status of a reservation.")
class ReservationStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    CANCELED = "canceled"
    CHECKED_IN = "checked_in"
    NO_SHOW = "no_show"
    WITHDRAWN = "withdrawn"


@strawberry.enum(description="Why a reservation no longer fits the current schedule.")
class ReservationViolation(Enum):
    NO_SERVICE = "no_service"
    CLOSED = "closed"
    OUTSIDE_HOURS = "outside_hours"


@strawberry.enum(description="Fields a reservation search may be sorted by.")
class ReservationSortField(Enum):
    ID = "id"
    RESERVATION_DATE = "reservation_date"
    CREATED_AT = "created_at"



@strawberry.type(description="A reservation.")
class Reservation:
    id: str = strawberry.field(description="Reservation identifier.")
    venue_id: str = strawberry.field(description="Venue this reservation belongs to.")
    status: ReservationStatus = strawberry.field(description="Current status.")
    reservation_date: datetime = strawberry.field(
        description="Reservation date and time as venue-local wall-clock (naive, no offset).",
    )
    party_size: int = strawberry.field(description="Number of people.")
    arrival_time: time | None = strawberry.field(description="Actual arrival time, once checked in.")
    contact_name: str = strawberry.field(description="Customer name.")
    contact_phone_number: str | None = strawberry.field(description="Customer phone number.")
    contact_email: str | None = strawberry.field(description="Customer email.")
    notes: str | None = strawberry.field(description="Free-form staff notes.")
    violation: ReservationViolation | None = strawberry.field(
        description="Set when the reservation no longer fits the current schedule (needs attention).",
    )
    created_at: datetime = strawberry.field(description="Creation date.")
    updated_at: datetime = strawberry.field(description="Last update date.")

    @classmethod
    def from_dict(cls, obj: dict[str, Any]) -> "Reservation":
        return Reservation(
            id=obj["id"],
            venue_id=obj["venue_id"],
            status=ReservationStatus(obj["status"]),
            reservation_date=obj["reservation_date"],
            party_size=obj["party_size"],
            arrival_time=obj.get("arrival_time"),
            contact_name=obj["contact_name"],
            contact_phone_number=obj.get("contact_phone_number"),
            contact_email=obj.get("contact_email"),
            notes=obj.get("notes"),
            violation=ReservationViolation(obj["violation"]) if obj.get("violation") else None,
            created_at=obj["created_at"],
            updated_at=obj["updated_at"],
        )


@strawberry.type(description="A service+date whose booked seats exceed the effective capacity.")
class OverCapacitySlot:
    service_id: str = strawberry.field(description="Service the overbooked slot belongs to.")
    service_name: str = strawberry.field(description="Name of that service.")
    business_date: date = strawberry.field(description="Venue-local service date of the slot.")
    capacity: int = strawberry.field(description="Effective seat capacity for that date.")
    peak_booked: int = strawberry.field(description="Peak concurrent booked seats.")
    reservation_ids: list[str] = strawberry.field(description="Live reservations in this slot.")

    @classmethod
    def from_dict(cls, obj: dict[str, Any]) -> "OverCapacitySlot":
        return OverCapacitySlot(
            service_id=obj["service_id"],
            service_name=obj["service_name"],
            business_date=obj["business_date"],
            capacity=obj["capacity"],
            peak_booked=obj["peak_booked"],
            reservation_ids=obj["reservation_ids"],
        )



@strawberry.type(description="How full one service is on one business date.")
class CalendarServiceSummary:
    service_id: str = strawberry.field(description="Service the summary belongs to.")
    service_name: str = strawberry.field(description="Name of that service.")
    opens_at: datetime = strawberry.field(description="Venue-local opening datetime (naive).")
    closes_at: datetime = strawberry.field(
        description="Venue-local closing datetime (naive); the next day for an overnight opening.",
    )
    capacity: int = strawberry.field(description="Effective seat capacity for the date.")
    peak_booked: int = strawberry.field(description="Peak concurrent booked seats.")
    reservation_count: int = strawberry.field(description="Number of live bookings.")
    over_capacity: bool = strawberry.field(description="Whether peak booked seats exceed capacity.")

    @classmethod
    def from_dict(cls, obj: dict[str, Any]) -> "CalendarServiceSummary":
        return CalendarServiceSummary(
            service_id=obj["service_id"],
            service_name=obj["service_name"],
            opens_at=obj["opens_at"],
            closes_at=obj["closes_at"],
            capacity=obj["capacity"],
            peak_booked=obj["peak_booked"],
            reservation_count=obj["reservation_count"],
            over_capacity=obj["over_capacity"],
        )


@strawberry.type(description="One business date of the calendar window.")
class CalendarDay:
    business_date: date = strawberry.field(description="Venue-local business date.")
    closed: bool = strawberry.field(
        description="Whether a closing removes every service that would otherwise open.",
    )
    services: list[CalendarServiceSummary] = strawberry.field(description="Services open that date.")

    @classmethod
    def from_dict(cls, obj: dict[str, Any]) -> "CalendarDay":
        return CalendarDay(
            business_date=obj["business_date"],
            closed=obj["closed"],
            services=[CalendarServiceSummary.from_dict(s) for s in obj["services"]],
        )


@strawberry.enum(description="Why an otherwise-open slot cannot take the requested party.")
class AvailabilityBlocker(Enum):
    INSUFFICIENT_SEATS = "insufficient_seats"


@strawberry.type(description="One start time on a service's slot grid.")
class AvailabilitySlot:
    slot_at: datetime = strawberry.field(
        description="Venue-local start time (naive); usable as a reservation date as-is.",
    )
    booked: int = strawberry.field(description="Seats taken by bookings overlapping this slot.")
    remaining: int = strawberry.field(description="Seats still free at this slot.")
    bookable: bool = strawberry.field(description="Whether the requested party fits.")
    blocker: AvailabilityBlocker | None = strawberry.field(
        default=None, description="Why the party does not fit; null when bookable.",
    )

    @classmethod
    def from_dict(cls, obj: dict[str, Any]) -> "AvailabilitySlot":
        return AvailabilitySlot(
            slot_at=obj["slot_at"],
            booked=obj["booked"],
            remaining=obj["remaining"],
            bookable=obj["bookable"],
            blocker=AvailabilityBlocker(obj["blocker"]) if obj.get("blocker") else None,
        )


@strawberry.type(description="A service open on the requested date, with its slot grid.")
class ServiceAvailability:
    service_id: str = strawberry.field(description="Service the slots belong to.")
    service_name: str = strawberry.field(description="Name of that service.")
    business_date: date = strawberry.field(description="Venue-local business date of the opening.")
    opens_at: datetime = strawberry.field(description="Venue-local opening datetime (naive).")
    closes_at: datetime = strawberry.field(description="Venue-local closing datetime (naive).")
    capacity: int = strawberry.field(description="Effective seat capacity for the date.")
    turn_time_m: int = strawberry.field(description="Reservation duration, in minutes.")
    slot_interval_m: int = strawberry.field(description="Interval between slot start times.")
    slots: list[AvailabilitySlot] = strawberry.field(
        description="Start times still open to booking; empty for a past date.",
    )

    @classmethod
    def from_dict(cls, obj: dict[str, Any]) -> "ServiceAvailability":
        return ServiceAvailability(
            service_id=obj["service_id"],
            service_name=obj["service_name"],
            business_date=obj["business_date"],
            opens_at=obj["opens_at"],
            closes_at=obj["closes_at"],
            capacity=obj["capacity"],
            turn_time_m=obj["turn_time_m"],
            slot_interval_m=obj["slot_interval_m"],
            slots=[AvailabilitySlot.from_dict(s) for s in obj["slots"]],
        )


@strawberry.type(description="Preview of what could be booked at a venue on one date.")
class DayAvailability:
    business_date: date = strawberry.field(description="The venue-local date the preview is for.")
    closed: bool = strawberry.field(description="Whether a closing removes every service.")
    services: list[ServiceAvailability] = strawberry.field(description="Services open that date.")

    @classmethod
    def from_dict(cls, obj: dict[str, Any]) -> "DayAvailability":
        return DayAvailability(
            business_date=obj["business_date"],
            closed=obj["closed"],
            services=[ServiceAvailability.from_dict(s) for s in obj["services"]],
        )


@strawberry.input(description="Information to create a reservation.")
class CreateReservationInput:
    venue_id: strawberry.ID = strawberry.field(description="Venue to book at.")
    contact_name: str = strawberry.field(description="Customer name.")
    party_size: int = strawberry.field(description="Number of people.")
    reservation_date: datetime = strawberry.field(
        description="Reservation date and time as venue-local wall-clock (naive, no offset).",
    )
    contact_phone_number: str | None = strawberry.field(default=None, description="Customer phone number.")
    contact_email: str | None = strawberry.field(default=None, description="Customer email.")
    notes: str | None = strawberry.field(default=None, description="Staff notes.")


@strawberry.input(description="Reservation fields to update (only provided fields change).")
class UpdateReservationInput:
    contact_name: str | None = strawberry.field(default=None, description="New customer name.")
    party_size: int | None = strawberry.field(default=None, description="New party size.")
    reservation_date: datetime | None = strawberry.field(
        default=None,
        description="New reservation date and time as venue-local wall-clock (naive, no offset).",
    )
    # UNSET default so an omitted field is left unchanged while an explicit null clears it — the
    # two fields the backend actually allows clearing. (contact_name/party_size/reservation_date
    # can't be cleared, so a plain None default is fine there.)
    contact_phone_number: str | None = strawberry.field(
        default=strawberry.UNSET, description="New phone number (null clears it).",
    )
    notes: str | None = strawberry.field(
        default=strawberry.UNSET, description="New staff notes (null clears them).",
    )


@strawberry.input(description="Reservation search filter.")
class ReservationFilterInput:
    venue_id: strawberry.ID = strawberry.field(description="Venue to list reservations for. Mandatory.")
    status: list[ReservationStatus] | None = strawberry.field(
        default=None, description="Filter to reservations in any of these statuses.",
    )
    date_from: date | None = strawberry.field(
        default=None, description="Include reservations on or after this venue-local date.",
    )
    date_to: date | None = strawberry.field(
        default=None, description="Include reservations on or before this venue-local date.",
    )
    violations_only: bool = strawberry.field(
        default=False, description="Return only reservations that violate the current schedule.",
    )


@strawberry.input(description="Reservation search query.")
class ReservationSearchInput:
    filter: ReservationFilterInput = strawberry.field(description="Filter parameters (venue mandatory).")
    pagination: PaginationInput = strawberry.field(
        default_factory=PaginationInput, description="Pagination parameters.",
    )
    sort: list[SortInput[ReservationSortField]] = strawberry.field(
        default_factory=list, description="Sort instructions.",
    )


class ReservationQueryParams(SearchQueryParams):
    """Builds the backend reservation-search query params from a ReservationSearchInput."""

    def __init__(self, search: ReservationSearchInput) -> None:
        super().__init__(search.pagination, search.sort)
        self._filter = search.filter

    def _finalize(self) -> None:
        self._set_filter("venue_id", str(self._filter.venue_id))
        if self._filter.status:
            self._set_filter("status", [s.value for s in self._filter.status])
        if self._filter.date_from is not None:
            self._set_filter("date_from", self._filter.date_from.isoformat())
        if self._filter.date_to is not None:
            self._set_filter("date_to", self._filter.date_to.isoformat())
        if self._filter.violations_only:
            self._set_filter("violations_only", self._filter.violations_only)



@strawberry.type
class ReservationQuery:
    reservation: Reservation = strawberry.field(
        resolver=resolve_get_reservation, description="Fetch a reservation by ID.",
    )
    reservations: Page[Reservation] = strawberry.field(
        resolver=resolve_search_reservations, description="Search a venue's reservations.",
    )
    reservation_over_capacity: list[OverCapacitySlot] = strawberry.field(
        resolver=resolve_reservation_over_capacity,
        description="Slots of a venue whose bookings now exceed the effective capacity.",
    )
    reservation_calendar: list[CalendarDay] = strawberry.field(
        resolver=resolve_reservation_calendar,
        description="Per-day, per-service occupancy of a venue over a date window.",
    )
    reservation_availability: DayAvailability = strawberry.field(
        resolver=resolve_reservation_availability,
        description="Slots a party could be booked into at a venue on one date.",
    )


@strawberry.type
class ReservationMutation:
    create_reservation = strawberry.mutation(
        resolver=resolve_create_reservation, description="Create a reservation.",
    )
    update_reservation = strawberry.mutation(
        resolver=resolve_update_reservation, description="Update a reservation's editable fields.",
    )
    confirm_reservation = strawberry.mutation(
        resolver=resolve_confirm_reservation, description="Confirm (accept) a reservation.",
    )
    reject_reservation = strawberry.mutation(
        resolver=resolve_reject_reservation, description="Reject (decline) a pending reservation.",
    )
    cancel_reservation = strawberry.mutation(
        resolver=resolve_cancel_reservation, description="Cancel a reservation (customer-initiated).",
    )
    check_in_reservation = strawberry.mutation(
        resolver=resolve_check_in_reservation, description="Check a reservation in (records arrival).",
    )
    no_show_reservation = strawberry.mutation(
        resolver=resolve_no_show_reservation, description="Mark a reservation as a no-show.",
    )
    withdraw_reservation = strawberry.mutation(
        resolver=resolve_withdraw_reservation,
        description="Withdraw a booking the venue can no longer honor (venue-initiated).",
    )
