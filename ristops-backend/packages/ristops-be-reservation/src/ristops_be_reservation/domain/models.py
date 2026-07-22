from enum import StrEnum


class Weekday(StrEnum):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


def normalize_weekdays(weekdays: list[Weekday] | None) -> list[Weekday | None]:
    """Normalize a bulk-create ``weekdays`` list into the set of per-row weekday values to
    persist: one row per distinct weekday (in canonical order), or a single ``[None]``
    (every day) when the list is empty/omitted or covers all seven weekdays."""
    if not weekdays:
        return [None]
    unique = set(weekdays)
    if unique == set(Weekday):
        return [None]
    return [weekday for weekday in Weekday if weekday in unique]
