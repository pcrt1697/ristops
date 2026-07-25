from enum import StrEnum

from sqlalchemy import ColumnElement, or_, true


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


def weekday_scope_overlap_condition(
        weekday_column: ColumnElement[str | None],
        weekday: Weekday | None,
) -> ColumnElement[bool]:
    """Whether an existing row's weekday scope overlaps a candidate ``weekday``.

    ``None`` means "every day in the range": a ``None`` candidate overlaps any existing row, and
    an existing ``None``-scoped row overlaps any candidate. Two explicit weekdays overlap only
    when equal.
    """
    if weekday is None:
        return true()
    return or_(weekday_column.is_(None), weekday_column == weekday)
