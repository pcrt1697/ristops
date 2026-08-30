from datetime import date, datetime, time, timedelta, tzinfo
from enum import StrEnum
from typing import Annotated, ClassVar, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from ristops_lib_core.pydantic.types import ObjectUUID, CreatedAt, UpdatedAt
from ristops_lib_core.schema.pagination import SearchQuery
from ristops_lib_core.utils import to_utc_instant


class ReservationStatus(StrEnum):
    PENDING = "pending"  # awaiting confirmation
    CONFIRMED = "confirmed"  # accepted by the venue
    REJECTED = "rejected"  # declined by the venue (of a still-pending request)
    CANCELED = "canceled"  # canceled by the customer
    CHECKED_IN = "checked_in"  # customer arrived
    NO_SHOW = "no_show"  # customer did not arrive
    WITHDRAWN = "withdrawn"  # venue withdrew an accepted booking it can no longer honor


class ReservationViolation(StrEnum):
    """Why a live (pending/confirmed) reservation no longer fits the current schedule. Computed on
    read — reservations are never mutated by a schedule change (see the invalidation policy)."""

    NO_SERVICE = "no_service"  # no service is open at that time anymore
    CLOSED = "closed"  # a venue or service closing now covers the date
    OUTSIDE_HOURS = "outside_hours"  # the turn no longer fits within the (shrunk) opening hours


def _validate_reservation_datetime(value: datetime | None) -> datetime | None:
    """Validate an incoming reservation datetime. It must be a *naive* value interpreted as
    venue-local wall-clock time (the server localizes it to the venue timezone on write), and it
    is booked to the minute — seconds/microseconds are rejected."""
    if value is None:
        return None
    if value.tzinfo is not None:
        raise ValueError(
            "reservation_date must be a naive venue-local datetime, without a timezone offset"
        )
    if value.second != 0 or value.microsecond != 0:
        raise ValueError("reservation_date must not include seconds or microseconds")
    return value


class ReservationCreationRequest(BaseModel):
    """Request body for creating a new reservation."""

    venue_id: UUID = Field(
        description="Identifier of the venue this reservation belongs to.",
    )
    contact_name: str = Field(
        description="Name of the customer.",
        max_length=120,
    )
    contact_phone_number: str | None = Field(
        default=None,
        description="Phone number of the customer.",
        max_length=20,
    )
    contact_email: str | None = Field(
        default=None,
        description="Email of the customer.",
        max_length=320,
    )
    party_size: int = Field(
        description="Number of people.",
        gt=0,
    )
    reservation_date: datetime = Field(
        description=(
            "Reservation date and time as venue-local wall-clock, naive (no timezone offset). "
            "Minute granularity only."
        ),
    )
    notes: str | None = Field(
        default=None,
        description="Free-form staff notes about the reservation.",
        max_length=1000,
    )

    _validate_reservation_date = field_validator("reservation_date")(_validate_reservation_datetime)


class ReservationUpdateRequest(BaseModel):
    """Request body for updating an existing reservation. Unset fields are not modified."""

    contact_name: str | None = Field(
        default=None,
        description="New name of the customer.",
        max_length=120,
    )
    contact_phone_number: str | None = Field(
        default=None,
        description="New phone number of the customer.",
        max_length=20,
    )
    party_size: int | None = Field(
        default=None,
        description="New number of people.",
        gt=0,
    )
    reservation_date: datetime | None = Field(
        default=None,
        description=(
            "New reservation date and time as venue-local wall-clock, naive (no timezone "
            "offset). Minute granularity only."
        ),
    )
    notes: str | None = Field(
        default=None,
        description="New staff notes about the reservation.",
        max_length=1000,
    )

    _validate_reservation_date = field_validator("reservation_date")(_validate_reservation_datetime)


class ReservationResponse(BaseModel):
    """Response body representing a reservation."""

    id: ObjectUUID
    venue_id: UUID = Field(description="Identifier of the venue this reservation belongs to.")
    status: ReservationStatus = Field(description="Status of the reservation.")
    reservation_date: datetime = Field(
        description="Reservation date and time as venue-local wall-clock, naive (no offset).",
    )
    party_size: int = Field(description="Number of people.")
    arrival_time: time | None = Field(default=None, description="Actual time of arrival, once checked in.")
    contact_name: str = Field(description="Name of the customer.")
    contact_phone_number: str | None = Field(default=None, description="Phone number of the customer.")
    contact_email: str | None = Field(default=None, description="Email of the customer.")
    notes: str | None = Field(default=None, description="Free-form staff notes about the reservation.")
    violation: ReservationViolation | None = Field(
        default=None,
        description="If set, why this reservation no longer fits the current schedule "
                    "(computed on read for live future bookings; null when it still fits).",
    )
    created_at: CreatedAt
    updated_at: UpdatedAt


class OverCapacitySlot(BaseModel):
    """A service+date whose booked seats now exceed the effective capacity (over-capacity is a
    slot-level overflow, not attributable to a single reservation)."""

    service_id: UUID = Field(description="Service the overbooked slot belongs to.")
    service_name: str = Field(description="Name of that service.")
    business_date: date = Field(description="Venue-local service date of the overbooked slot.")
    capacity: int = Field(description="Effective seat capacity for that date.")
    peak_booked: int = Field(description="Peak concurrent booked seats (the overflow amount).")
    reservation_ids: list[UUID] = Field(
        description="Live reservations contributing to this slot, for staff to review.",
    )


class OverCapacityResponse(BaseModel):
    """The venue's currently overbooked slots (empty when none)."""

    slots: list[OverCapacitySlot] = Field(default_factory=list)


# Maximum span of a calendar query, in days. A month view needs 31; the cap keeps a single
# request from scanning an unbounded stretch of reservations.
MAX_CALENDAR_SPAN_DAYS = 62


class CalendarQuery(BaseModel):
    """Query parameters of the calendar summary: a venue and an inclusive date window."""

    venue_id: UUID = Field(
        description="Identifier of the venue to summarize.",
    )
    date_from: date = Field(
        description="First venue-local business date of the window (inclusive).",
    )
    date_to: date = Field(
        description="Last venue-local business date of the window (inclusive).",
    )

    @model_validator(mode="after")
    def _validate_span(self) -> "CalendarQuery":
        if self.date_to < self.date_from:
            raise ValueError("date_to must not be earlier than date_from")
        span = (self.date_to - self.date_from).days + 1
        if span > MAX_CALENDAR_SPAN_DAYS:
            raise ValueError(f"The window must not exceed {MAX_CALENDAR_SPAN_DAYS} days")
        return self


class CalendarServiceSummary(BaseModel):
    """How full one service is on one business date."""

    service_id: UUID = Field(description="Service the summary belongs to.")
    service_name: str = Field(description="Name of that service.")
    opens_at: datetime = Field(
        description="Venue-local opening datetime, naive. May cross midnight for an overnight "
                    "opening, in which case it closes on the following calendar day.",
    )
    closes_at: datetime = Field(description="Venue-local closing datetime, naive.")
    capacity: int = Field(
        description="Effective seat capacity (opening capacity plus capacity-override deltas).",
    )
    peak_booked: int = Field(description="Peak concurrent booked seats across the service window.")
    reservation_count: int = Field(description="Number of live bookings in the window.")
    over_capacity: bool = Field(description="Whether the peak booked seats exceed the capacity.")


class CalendarDay(BaseModel):
    """One business date of the calendar window."""

    business_date: date = Field(description="Venue-local business date.")
    closed: bool = Field(
        description="Whether a venue or service closing removes every service that would "
                    "otherwise open on this date. False when nothing was scheduled at all.",
    )
    services: list[CalendarServiceSummary] = Field(default_factory=list)


class CalendarResponse(BaseModel):
    """Per-day occupancy of a venue over the requested window. Days with no service open and no
    closing are omitted."""

    days: list[CalendarDay] = Field(default_factory=list)


class AvailabilityQuery(BaseModel):
    """Query parameters of the availability preview: which venue, date and party to check."""

    venue_id: UUID = Field(
        description="Identifier of the venue to check.",
    )
    business_date: date = Field(
        description="Venue-local business date to check. An overnight opening is reported on the "
                    "date it opens on.",
    )
    party_size: int = Field(
        description="Number of people to seat; a slot is bookable when this many seats remain.",
        gt=0,
    )
    exclude_reservation_id: UUID | None = Field(
        default=None,
        description="Reservation to leave out of the seat count, so an edit does not count its "
                    "own seats against itself.",
    )


class AvailabilityBlocker(StrEnum):
    """Why an otherwise-open slot cannot take the requested party."""

    INSUFFICIENT_SEATS = "insufficient_seats"  # fewer seats remain than the party needs


class AvailabilitySlot(BaseModel):
    """One start time on a service's slot grid, with its current seat occupancy."""

    slot_at: datetime = Field(
        description="Venue-local start time, naive — usable as a reservation's date as-is.",
    )
    booked: int = Field(description="Seats already taken by bookings overlapping this slot.")
    remaining: int = Field(description="Seats still free at this slot.")
    bookable: bool = Field(description="Whether the requested party fits.")
    blocker: AvailabilityBlocker | None = Field(
        default=None,
        description="Why the party does not fit; null when the slot is bookable.",
    )


class ServiceAvailability(BaseModel):
    """A service open on the requested date, with its slot grid."""

    service_id: UUID = Field(description="Service the slots belong to.")
    service_name: str = Field(description="Name of that service.")
    business_date: date = Field(description="Venue-local business date of the opening.")
    opens_at: datetime = Field(description="Venue-local opening datetime, naive.")
    closes_at: datetime = Field(description="Venue-local closing datetime, naive.")
    capacity: int = Field(description="Effective seat capacity for the date.")
    turn_time_m: int = Field(description="Reservation duration, in minutes.")
    slot_interval_m: int = Field(description="Interval between slot start times, in minutes.")
    slots: list[AvailabilitySlot] = Field(
        default_factory=list,
        description="Bookable-in-principle start times. Slots that have passed, or that fall "
                    "inside the advance-notice window, are omitted entirely — so this is empty "
                    "for a past date even though the service opened.",
    )


class AvailabilityResponse(BaseModel):
    """Read-only preview of what could be booked at a venue on one date (what a create would
    409 on). Services are always listed when they open that date, even when no slot remains, so
    a caller can still show the day's shape."""

    business_date: date = Field(description="The venue-local date the preview is for.")
    closed: bool = Field(
        description="Whether a venue or service closing removes every service that would "
                    "otherwise open on this date.",
    )
    services: list[ServiceAvailability] = Field(default_factory=list)


class ReservationSortField(StrEnum):
    """Fields a reservation search may be sorted by."""

    ID = "id"
    RESERVATION_DATE = "reservation_date"
    CREATED_AT = "created_at"


class ReservationListFilter(BaseModel):
    """Filter parameters for listing reservations, exposed as `filter.<field>` query params."""

    venue_id: UUID = Field(
        description="Filter by venue ID. Mandatory.",
    )
    status: list[ReservationStatus] | None = Field(
        default=None,
        description="Filter to reservations in any of these statuses.",
    )
    date_from: date | None = Field(
        default=None,
        description="Include reservations on or after this venue-local calendar date.",
    )
    date_to: date | None = Field(
        default=None,
        description="Include reservations on or before this venue-local calendar date.",
    )
    violations_only: bool = Field(
        default=False,
        description="Return only reservations that violate the current schedule (the "
                    "'needs attention' view).",
    )


class ReservationSearchQuery(SearchQuery, ReservationListFilter):
    """Full reservation search query: pagination, sort, and filter combined."""

    sort_field_enum: ClassVar[type[StrEnum]] = ReservationSortField

    def date_bounds(self, tz: tzinfo) -> tuple[datetime | None, datetime | None]:
        """
        Convert the venue-local `[date_from, date_to]` filter into a half-open UTC instant range
        `[start, end)`. `date_to` is inclusive, so `end` is the start of the following day.

        :param tz: Timezone the filter dates are expressed in.
        """
        start = (
            to_utc_instant(datetime.combine(self.date_from, time.min), tz)
            if self.date_from is not None else None
        )
        end = (
            to_utc_instant(datetime.combine(self.date_to + timedelta(days=1), time.min), tz)
            if self.date_to is not None else None
        )
        return start, end


class ReservationActionType(StrEnum):
    """The action performed by the status-change endpoint. Distinct from the resulting
    `ReservationStatus`: an action is a verb (what the caller does), and each maps to a target
    status. `pending` has no action — it is only the status a reservation is created with."""

    CONFIRM = "confirm"
    REJECT = "reject"
    CANCEL = "cancel"
    CHECK_IN = "check_in"
    NO_SHOW = "no_show"
    WITHDRAW = "withdraw"


class _ReservationActionBase(BaseModel):
    """Fields common to every reservation status-change action."""

    notes: str | None = Field(
        default=None,
        description="Staff notes to record with this action (replaces the existing notes).",
        max_length=1000,
    )


class ConfirmReservationAction(_ReservationActionBase):
    """Confirm a reservation (accept it) → confirmed. Requires ``reservation:confirm``."""

    action: Literal[ReservationActionType.CONFIRM] = Field(description="Action: confirm.")


class RejectReservationAction(_ReservationActionBase):
    """Reject a reservation (decline it) → rejected. Requires ``reservation:reject``."""

    action: Literal[ReservationActionType.REJECT] = Field(description="Action: reject.")


class CancelReservationAction(_ReservationActionBase):
    """Cancel a reservation → canceled. Requires ``reservation:cancel``."""

    action: Literal[ReservationActionType.CANCEL] = Field(description="Action: cancel.")


class CheckInReservationAction(_ReservationActionBase):
    """Check a reservation in (the party arrived) → checked_in. Requires ``reservation:check-in``."""

    action: Literal[ReservationActionType.CHECK_IN] = Field(description="Action: check_in.")
    arrival_time: time | None = Field(
        default=None,
        description="Venue-local time of arrival; defaults to the current venue-local time if omitted.",
    )


class NoShowReservationAction(_ReservationActionBase):
    """Mark a reservation as a no-show (the party did not arrive) → no_show. Requires
    ``reservation:no-show``."""

    action: Literal[ReservationActionType.NO_SHOW] = Field(description="Action: no_show.")


class WithdrawReservationAction(_ReservationActionBase):
    """Withdraw a booking the venue can no longer honor → withdrawn — a venue-initiated
    cancellation, distinct from a customer ``cancel`` or a pre-acceptance ``reject`` (e.g. after a
    closure or schedule change makes the booking impossible). Requires ``reservation:withdraw``."""

    action: Literal[ReservationActionType.WITHDRAW] = Field(description="Action: withdraw.")


# Discriminated on `action` (the verb), not the resulting status. Each variant maps to a target
# status in the service; the required permission is resolved per-action in the router (see
# `_reservation_action_permission_resolver`).
ReservationActionRequest = Annotated[
    ConfirmReservationAction
    | RejectReservationAction
    | CancelReservationAction
    | CheckInReservationAction
    | NoShowReservationAction
    | WithdrawReservationAction,
    Field(discriminator="action"),
]
