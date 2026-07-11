from enum import StrEnum


class ReservationStatus(StrEnum):
    PENDING = "pending"  # awaiting confirmation
    CONFIRMED = "confirmed"  # accepted by the venue
    REJECTED = "rejected"  # declined by the venue
    CANCELED = "canceled"  # canceled by the customer
    CHECKED_IN = "checked_in"  # customer arrived
    NO_SHOW = "no_show"  # customer did not arrive
