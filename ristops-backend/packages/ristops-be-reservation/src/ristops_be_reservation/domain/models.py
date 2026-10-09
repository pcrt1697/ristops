from datetime import date
from enum import StrEnum


class Weekday(StrEnum):
    """Days of the week, in Python's Monday=0..Sunday=6 order (matching `date.weekday()`)."""

    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class ReservationViolation(StrEnum):
    """Why a live (pending/confirmed) reservation no longer fits its service's current schedule.
    Computed on read — reservations are never mutated by a schedule change."""

    NO_SERVICE = "no_service"  # the service was deleted, or no longer runs that date
    CLOSED = "closed"  # a closing now covers the date
    OUTSIDE_HOURS = "outside_hours"  # the service still runs that day, but not at that time


WEEKDAYS: tuple[Weekday, ...] = tuple(Weekday)


def weekday_of(on_date: date) -> Weekday:
    """The weekday a calendar date falls on."""
    return WEEKDAYS[on_date.weekday()]


def next_weekday(weekday: Weekday) -> Weekday:
    """The weekday following the given one, wrapping Sunday back to Monday."""
    return WEEKDAYS[(WEEKDAYS.index(weekday) + 1) % 7]
