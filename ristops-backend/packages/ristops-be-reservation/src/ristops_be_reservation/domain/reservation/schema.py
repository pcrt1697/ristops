from datetime import date, datetime, time
from enum import StrEnum
from typing import Annotated, ClassVar, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from ristops_be_reservation.domain.models import ReservationViolation
from ristops_lib_core.pydantic.types import ObjectUUID, CreatedAt, UpdatedAt
from ristops_lib_core.schema.pagination import SearchQuery


class ReservationStatus(StrEnum):
    PENDING = "pending"  # awaiting confirmation
    CONFIRMED = "confirmed"  # accepted by the venue
    REJECTED = "rejected"  # declined by the venue (of a still-pending request)
    CANCELED = "canceled"  # canceled by the customer
    CHECKED_IN = "checked_in"  # customer arrived
    NO_SHOW = "no_show"  # customer did not arrive
    WITHDRAWN = "withdrawn"  # venue withdrew an accepted booking it can no longer honor


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
    service_id: UUID = Field(
        description="Identifier of the service to book into. The requested time must fall within "
                    "that service's opening window on the date.",
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

    service_id: UUID | None = Field(
        default=None,
        description="Move the booking to this service. The booking is checked against it like a "
                    "new one, so this is how a booking left on a closed or deleted service is "
                    "given a new one.",
    )
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
            "offset). Minute granularity only. Must still fall within the booked service's "
            "opening window."
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
    service_id: UUID = Field(description="Identifier of the service this reservation is booked into.")
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
    capacity: int = Field(description="Seats the service can take on the date.")
    booked: int = Field(description="Seats taken by live bookings on the date.")
    remaining: int = Field(description="Seats still free on the date; negative when over capacity.")
    reservation_count: int = Field(description="Number of live bookings on the date.")
    over_capacity: bool = Field(description="Whether the booked seats exceed the capacity.")


class ClosedServiceSummary(BaseModel):
    """A service a closing removes from one business date while it still holds bookings."""

    service_id: UUID = Field(description="Service the closing removes.")
    service_name: str = Field(description="Name of that service.")
    reservation_count: int = Field(
        description="Pending or confirmed bookings still held on the service that day, which "
                    "staff need to resolve.",
    )


class DeletedServiceSummary(BaseModel):
    """A deleted service that still holds bookings on one business date."""

    service_id: UUID = Field(description="The deleted service.")
    service_name: str = Field(description="Name of that service.")
    reservation_count: int = Field(
        description="Pending or confirmed bookings still held on the service that day, which "
                    "staff need to resolve.",
    )


class CalendarDay(BaseModel):
    """One business date of the calendar window."""

    business_date: date = Field(description="Venue-local business date.")
    closed: bool = Field(
        description="Whether a closing removes every service that would otherwise run on this "
                    "date. False when nothing was scheduled at all.",
    )
    services: list[CalendarServiceSummary] = Field(default_factory=list)
    closed_services: list[ClosedServiceSummary] = Field(
        default_factory=list,
        description="Services a closing removes that day which still hold bookings. They are not "
                    "in `services`, since they no longer run.",
    )
    deleted_services: list[DeletedServiceSummary] = Field(
        default_factory=list,
        description="Deleted services that still hold bookings on that day. They are not in "
                    "`services`, since they no longer run.",
    )


class CalendarResponse(BaseModel):
    """Per-day occupancy of a venue over the requested window — the day's shape and what is left
    to book. Days with no service running and no closing are omitted, so a caller can render
    "nothing scheduled" by absence."""

    days: list[CalendarDay] = Field(default_factory=list)


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
    service_id: UUID | None = Field(
        default=None,
        description="Filter to reservations booked into this service.",
    )
    status: list[ReservationStatus] | None = Field(
        default=None,
        description="Filter to reservations in any of these statuses.",
    )
    date_from: date | None = Field(
        default=None,
        description="Include reservations on or after this business date.",
    )
    date_to: date | None = Field(
        default=None,
        description="Include reservations on or before this business date.",
    )
    violations_only: bool = Field(
        default=False,
        description="Return only reservations that violate the current schedule (the "
                    "'needs attention' view).",
    )


class ReservationSearchQuery(SearchQuery, ReservationListFilter):
    """Full reservation search query: pagination, sort, and filter combined."""

    sort_field_enum: ClassVar[type[StrEnum]] = ReservationSortField


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
