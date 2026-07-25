from datetime import time, date
from enum import StrEnum
from typing import ClassVar
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from ristops_be_reservation.domain.models import Weekday
from ristops_lib_core.pydantic.types import ObjectUUID, CreatedAt, UpdatedAt
from ristops_lib_core.schema.pagination import SearchQuery


class DateRangeFilter(BaseModel):
    """Filter a date-ranged resource by overlap with a `[date_from, date_to]` window.

    An item with period `[date_start, date_end]` matches when it covers at least one day of
    the window: `date_end >= date_from AND date_start <= date_to`. Either bound may be omitted
    to leave that side open. The intended use case is a month view, where the window is the
    first and last day of the selected month.
    """

    date_from: date | None = Field(
        default=None,
        description="Include items whose period ends on or after this date (window start).",
    )
    date_to: date | None = Field(
        default=None,
        description="Include items whose period starts on or before this date (window end).",
    )


class ServiceScheduleQuery(SearchQuery, DateRangeFilter):
    """Shared base for the paginated schedule list queries (opening overrides, closings):
    pagination + sort + date-range overlap, plus the deleted-service gate. Concrete
    subclasses only set ``sort_field_enum``. Exposed as `filter.*` / `page` / `sort` params.
    """

    include_deleted: bool = Field(
        default=False,
        description="Return results even if the parent service has been deleted.",
    )


class ConflictSource(StrEnum):
    """Which kind of exception a conflicting row belongs to."""

    VENUE_CLOSING = "venue_closing"
    SERVICE_CLOSING = "service_closing"
    OPENING_OVERRIDE = "opening_override"
    CAPACITY_OVERRIDE = "capacity_override"


class ScheduleConflict(BaseModel):
    """A single existing row that conflicts with a candidate period+weekday being checked."""

    weekday: Weekday | None = Field(
        default=None,
        description="Weekday from the candidate request this conflict applies to; null = every day.",
    )
    source: ConflictSource = Field(description="Which kind of exception the conflicting row is.")
    conflicting_id: UUID = Field(description="Identifier of the existing conflicting row.")
    conflicting_date_start: date = Field(description="First date of the conflicting row (inclusive).")
    conflicting_date_end: date = Field(description="Last date of the conflicting row (inclusive).")
    conflicting_weekday: Weekday | None = Field(
        default=None,
        description="Weekday scope of the conflicting row; null means every day.",
    )


class ConflictQuery(BaseModel):
    """Query for a read-only conflict preview: the candidate period a client is about to write.
    Mirrors the create-request shape (bulk `weekdays`), plus an optional `exclude_id` to preview
    an in-place edit without the row conflicting with itself."""

    date_start: date = Field(description="First date of the candidate period (inclusive).")
    date_end: date = Field(description="Last date of the candidate period (inclusive).")
    weekdays: list[Weekday] | None = Field(
        default=None,
        description="Weekdays to check; provide multiple for a bulk candidate. "
                    "Omit, or include all 7, for every day.",
    )
    exclude_id: UUID | None = Field(
        default=None,
        description="Exclude this row from the check (use when previewing an edit of it).",
    )


class ConflictsResponse(BaseModel):
    """Result of a conflict preview: the conflicting rows, empty when the candidate is free."""

    conflicts: list[ScheduleConflict] = Field(
        default_factory=list,
        description="Existing rows that conflict with the candidate; empty means no conflict.",
    )


class OpeningUpsertRequest(BaseModel):
    """A single opening within a bulk upsert request."""

    weekday: Weekday = Field(description="Day of the week this opening applies to.")
    capacity: int = Field(description="Maximum number of reservable seats.", gt=0)
    start_time: time = Field(description="Time the service opens.")
    end_time: time = Field(description="Time the service closes.")
    description: str | None = Field(
        default=None,
        description="Description of this opening.",
        max_length=1000,
    )


class OpeningResponse(BaseModel):
    """Response body representing a service opening."""

    id: ObjectUUID
    service_id: UUID = Field(description="Identifier of the service this opening belongs to.")
    weekday: Weekday = Field(description="Day of the week this opening applies to.")
    capacity: int = Field(description="Maximum number of reservable seats.")
    start_time: time = Field(description="Time the service opens.")
    end_time: time = Field(description="Time the service closes.")
    description: str | None = Field(default=None, description="Description of this opening.")
    created_at: CreatedAt
    updated_at: UpdatedAt


class OpeningsUpsertRequest(BaseModel):
    """Request body for replacing the full set of openings for a service. Openings are
    configured as a whole set at setup time, so this stays a bulk, list-replace operation
    (unlike overrides/closings, which are one-off special cases created individually)."""

    openings: list[OpeningUpsertRequest] = Field(
        description="The complete set of openings to apply. Openings for weekdays not "
                    "included here are removed.",
    )

    @model_validator(mode="after")
    def _validate_no_duplicate_weekdays(self) -> "OpeningsUpsertRequest":
        weekdays = {opening.weekday for opening in self.openings}
        if len(self.openings) != len(weekdays):
            raise ValueError("Duplicate weekday in openings list")
        return self


class OpeningsResponse(BaseModel):
    """Response body listing a service's openings."""

    openings: list[OpeningResponse]


class OpeningOverrideCreateRequest(BaseModel):
    """Request body for creating a new opening override. Bulk: one row is created per weekday
    given in ``weekdays`` (in a single transaction); omitted/empty, or all seven weekdays,
    collapses to a single every-day row (``weekday`` null) — the same normalization applied
    for a single-weekday request too."""

    date_start: date = Field(description="First date of the override period (inclusive).")
    date_end: date = Field(description="Last date of the override period (inclusive).")
    weekdays: list[Weekday] | None = Field(
        default=None,
        description="Weekdays to scope to; provide multiple to create one row per weekday. "
                    "Omit, or include all 7, for every day.",
    )
    capacity: int = Field(description="Overridden maximum number of reservable seats.", gt=0)
    start_time: time = Field(description="Overridden opening time.")
    end_time: time = Field(description="Overridden closing time.")
    description: str | None = Field(
        default=None,
        description="Description of this override.",
        max_length=1000,
    )


class OpeningOverrideUpdateRequest(BaseModel):
    """Request body for updating an opening override. Unset fields are not modified. The
    ``weekday`` scope is immutable — delete and recreate to re-scope it."""

    date_start: date | None = Field(
        default=None,
        description="New first date of the override period (inclusive).",
    )
    date_end: date | None = Field(
        default=None,
        description="New last date of the override period (inclusive).",
    )
    capacity: int | None = Field(
        default=None,
        description="New overridden maximum number of reservable seats.",
        gt=0,
    )
    start_time: time | None = Field(default=None, description="New overridden opening time.")
    end_time: time | None = Field(default=None, description="New overridden closing time.")
    description: str | None = Field(
        default=None,
        description="New description of this override.",
        max_length=1000,
    )


class OpeningOverrideResponse(BaseModel):
    """Response body representing a service opening override."""

    id: ObjectUUID
    service_id: UUID = Field(description="Identifier of the service this override belongs to.")
    date_start: date = Field(description="First date of the override period (inclusive).")
    date_end: date = Field(description="Last date of the override period (inclusive).")
    weekday: Weekday | None = Field(
        default=None,
        description="Weekday the override applies to within the range; null means every day.",
    )
    capacity: int = Field(description="Overridden maximum number of reservable seats.")
    start_time: time = Field(description="Overridden opening time.")
    end_time: time = Field(description="Overridden closing time.")
    description: str | None = Field(default=None, description="Description of this override.")
    created_at: CreatedAt
    updated_at: UpdatedAt


class OpeningOverrideSortField(StrEnum):
    """Fields an opening-override search may be sorted by."""

    DATE_START = "date_start"
    DATE_END = "date_end"
    CREATED_AT = "created_at"
    ID = "id"


class OpeningOverrideSearchQuery(ServiceScheduleQuery):
    """Paginated, sorted, date-range-filtered opening-override search query."""

    sort_field_enum: ClassVar[type[StrEnum]] = OpeningOverrideSortField


class ServiceClosingCreateRequest(BaseModel):
    """Request body for creating a new closing. Bulk: one row is created per weekday given in
    ``weekdays`` (in a single transaction); omitted/empty, or all seven weekdays, collapses to
    a single every-day row (``weekday`` null)."""

    date_start: date = Field(description="First date of the closing period (inclusive).")
    date_end: date = Field(description="Last date of the closing period (inclusive).")
    weekdays: list[Weekday] | None = Field(
        default=None,
        description="Weekdays to scope to; provide multiple to create one row per weekday. "
                    "Omit, or include all 7, for every day.",
    )
    description: str | None = Field(
        default=None,
        description="Description of this closing.",
        max_length=1000,
    )


class ServiceClosingUpdateRequest(BaseModel):
    """Request body for updating a closing. Unset fields are not modified. The ``weekday`` scope
    is immutable — delete and recreate to re-scope it."""

    date_start: date | None = Field(
        default=None,
        description="New first date of the closing period (inclusive).",
    )
    date_end: date | None = Field(
        default=None,
        description="New last date of the closing period (inclusive).",
    )
    description: str | None = Field(
        default=None,
        description="New description of this closing.",
        max_length=1000,
    )


class ServiceClosingResponse(BaseModel):
    """Response body representing a service closing."""

    id: ObjectUUID
    service_id: UUID = Field(description="Identifier of the service this closing belongs to.")
    date_start: date = Field(description="First date of the closing period (inclusive).")
    date_end: date = Field(description="Last date of the closing period (inclusive).")
    weekday: Weekday | None = Field(
        default=None,
        description="Weekday the closing applies to within the range; null means every day.",
    )
    description: str | None = Field(default=None, description="Description of this closing.")
    created_at: CreatedAt
    updated_at: UpdatedAt


class ServiceClosingSortField(StrEnum):
    """Fields a service-closing search may be sorted by."""

    DATE_START = "date_start"
    DATE_END = "date_end"
    CREATED_AT = "created_at"
    ID = "id"


class ServiceClosingSearchQuery(ServiceScheduleQuery):
    """Paginated, sorted, date-range-filtered service-closing search query."""

    sort_field_enum: ClassVar[type[StrEnum]] = ServiceClosingSortField


class CapacityOverrideCreateRequest(BaseModel):
    """Request body for creating a new capacity override. Bulk: one row is created per weekday
    given in ``weekdays`` (in a single transaction); omitted/empty, or all seven weekdays,
    collapses to a single every-day row (``weekday`` null)."""

    date_start: date = Field(description="First date of the override period (inclusive).")
    date_end: date = Field(description="Last date of the override period (inclusive).")
    weekdays: list[Weekday] | None = Field(
        default=None,
        description="Weekdays to scope to; provide multiple to create one row per weekday. "
                    "Omit, or include all 7, for every day.",
    )
    capacity_delta: int = Field(
        description="Signed change to the resolved seat count (e.g. +30 for a garden).",
    )
    description: str | None = Field(
        default=None,
        description="Description of this capacity override.",
        max_length=1000,
    )


class CapacityOverrideUpdateRequest(BaseModel):
    """Request body for updating a capacity override. Unset fields are not modified. The
    ``weekday`` scope is immutable — delete and recreate to re-scope it."""

    date_start: date | None = Field(
        default=None,
        description="New first date of the override period (inclusive).",
    )
    date_end: date | None = Field(
        default=None,
        description="New last date of the override period (inclusive).",
    )
    capacity_delta: int | None = Field(
        default=None,
        description="New signed change to the resolved seat count.",
    )
    description: str | None = Field(
        default=None,
        description="New description of this capacity override.",
        max_length=1000,
    )


class CapacityOverrideResponse(BaseModel):
    """Response body representing a service capacity override."""

    id: ObjectUUID
    service_id: UUID = Field(description="Identifier of the service this override belongs to.")
    date_start: date = Field(description="First date of the override period (inclusive).")
    date_end: date = Field(description="Last date of the override period (inclusive).")
    weekday: Weekday | None = Field(
        default=None,
        description="Weekday the override applies to within the range; null means every day.",
    )
    capacity_delta: int = Field(description="Signed change to the resolved seat count.")
    description: str | None = Field(default=None, description="Description of this capacity override.")
    created_at: CreatedAt
    updated_at: UpdatedAt


class CapacityOverrideSortField(StrEnum):
    """Fields a capacity-override search may be sorted by."""

    DATE_START = "date_start"
    DATE_END = "date_end"
    CREATED_AT = "created_at"
    ID = "id"


class CapacityOverrideSearchQuery(ServiceScheduleQuery):
    """Paginated, sorted, date-range-filtered capacity-override search query."""

    sort_field_enum: ClassVar[type[StrEnum]] = CapacityOverrideSortField
