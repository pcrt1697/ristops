from datetime import date, time
from enum import StrEnum
from typing import ClassVar
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from ristops_be_reservation.domain.models import Weekday
from ristops_lib_core.pydantic.types import ObjectUUID, CreatedAt, UpdatedAt, DeletedAt
from ristops_lib_core.schema.pagination import SearchQuery, SortableQuery


def _validate_validity(date_from: date | None, date_to: date | None) -> None:
    """Reject a validity period that ends before it starts. An open-ended period (null
    ``date_to``) is always valid."""
    if date_from is not None and date_to is not None and date_to < date_from:
        raise ValueError("date_to must not be earlier than date_from")


class ServiceCreationRequest(BaseModel):
    """Request body for creating a new service."""

    venue_id: UUID = Field(
        description="Identifier of the venue this service belongs to."
    )
    name: str = Field(
        description="Name of the service.",
        max_length=120,
    )
    description: str | None = Field(
        default=None,
        description="Optional description of the service.",
        max_length=1000,
    )
    date_from: date = Field(
        description="First date the service runs on (inclusive).",
    )
    date_to: date | None = Field(
        default=None,
        description="Last date the service runs on (inclusive). Omit to run it indefinitely; "
                    "set it equal to `date_from` for a one-shot service.",
    )
    capacity: int = Field(
        description="Maximum number of seats bookable on any date the service runs.",
        gt=0,
    )

    @model_validator(mode="after")
    def _validate_period(self) -> "ServiceCreationRequest":
        _validate_validity(self.date_from, self.date_to)
        return self


class ServiceUpdateRequest(BaseModel):
    """Request body for updating an existing service. Unset fields are not modified."""

    name: str | None = Field(
        default=None,
        description="New name of the service.",
        max_length=120,
    )
    description: str | None = Field(
        default=None,
        description="New description of the service.",
        max_length=1000,
    )
    date_from: date | None = Field(
        default=None,
        description="New first date the service runs on (inclusive).",
    )
    date_to: date | None = Field(
        default=None,
        description="New last date the service runs on (inclusive); null runs it indefinitely.",
    )
    capacity: int | None = Field(
        default=None,
        description="New maximum number of seats bookable on any date the service runs.",
        gt=0,
    )

    @model_validator(mode="after")
    def _validate_period(self) -> "ServiceUpdateRequest":
        _validate_validity(self.date_from, self.date_to)
        return self


class ServiceResponse(BaseModel):
    """Response body representing a service."""

    id: ObjectUUID
    venue_id: UUID = Field(description="Identifier of the venue this service belongs to.")
    name: str = Field(description="Name of the service.")
    description: str | None = Field(default=None, description="Description of the service.")
    date_from: date = Field(description="First date the service runs on (inclusive).")
    date_to: date | None = Field(
        default=None,
        description="Last date the service runs on (inclusive); null runs it indefinitely.",
    )
    capacity: int = Field(description="Maximum number of seats bookable on any date the service runs.")
    deleted_at: DeletedAt
    created_at: CreatedAt
    updated_at: UpdatedAt


class ServicesResponse(BaseModel):
    """Response body listing services."""

    services: list[ServiceResponse]


class ServiceSortField(StrEnum):
    """Fields a service search may be sorted by."""

    ID = "id"
    NAME = "name"
    DATE_FROM = "date_from"
    DATE_TO = "date_to"
    CREATED_AT = "created_at"


class ServiceListFilter(BaseModel):
    """Filter parameters for listing services, exposed as `filter.<field>` query params."""

    venue_id: UUID = Field(
        description="Filter by venue ID.",
    )
    name: str | None = Field(
        default=None,
        description="Filter by name of the service using a like operator.",
    )
    date_from: date | None = Field(
        default=None,
        description="Include services still running on or after this date (window start).",
    )
    date_to: date | None = Field(
        default=None,
        description="Include services already running on or before this date (window end).",
    )
    include_deleted: bool = Field(
        default=False,
        description="Include deleted services. Excluded by default.",
    )


class ServiceListQuery(SortableQuery, ServiceListFilter):
    """Full service list query: sort and filter combined. Not paginated."""

    sort_field_enum: ClassVar[type[StrEnum]] = ServiceSortField


class DateRangeFilter(BaseModel):
    """Filter a date-ranged resource by overlap with a `[date_from, date_to]` window.

    An item with period `[date_from, date_to]` matches when it covers at least one day of
    the window. Either bound may be omitted to leave that side open. The intended use case is a
    month view, where the window is the first and last day of the selected month.
    """

    date_from: date | None = Field(
        default=None,
        description="Include items whose period ends on or after this date (window start).",
    )
    date_to: date | None = Field(
        default=None,
        description="Include items whose period starts on or before this date (window end).",
    )


class OpeningUpsertRequest(BaseModel):
    """One weekday's opening hours within an openings upsert."""

    weekday: Weekday = Field(description="Day of the week this opening applies to.")
    start_time: time = Field(description="Time the service opens.")
    end_time: time = Field(
        description="Time the service closes. An end at or before the start runs the opening "
                    "overnight, closing on the following day.",
    )
    description: str | None = Field(
        default=None,
        description="Description of this opening.",
        max_length=1000,
    )


class OpeningsUpsertRequest(BaseModel):
    """Request body replacing a service's full set of weekly openings."""

    openings: list[OpeningUpsertRequest] = Field(
        default_factory=list,
        description="The service's complete weekly hours. Submitting an empty list clears them.",
    )

    @model_validator(mode="after")
    def _validate_unique_weekdays(self) -> "OpeningsUpsertRequest":
        weekdays = [opening.weekday for opening in self.openings]
        if len(weekdays) != len(set(weekdays)):
            raise ValueError("Each weekday may appear at most once")
        return self

    @model_validator(mode="after")
    def _validate_no_overnight_spillover(self) -> "OpeningsUpsertRequest":
        """An overnight opening must not run into the next day's own opening — the service would
        be open twice at once, which no closing can separate."""
        by_weekday = {opening.weekday: opening for opening in self.openings}
        weekdays = list(Weekday)
        for opening in self.openings:
            if opening.end_time > opening.start_time:
                continue
            following = by_weekday.get(
                weekdays[(weekdays.index(opening.weekday) + 1) % 7]
            )
            if following is not None and opening.end_time > following.start_time:
                raise ValueError(
                    f"The {opening.weekday} opening runs past the start of the "
                    f"{following.weekday} one"
                )
        return self


class OpeningResponse(BaseModel):
    """Response body representing a service opening."""

    id: ObjectUUID
    service_id: UUID = Field(description="Identifier of the service this opening belongs to.")
    weekday: Weekday = Field(description="Day of the week this opening applies to.")
    start_time: time = Field(description="Time the service opens.")
    end_time: time = Field(description="Time the service closes.")
    description: str | None = Field(default=None, description="Description of this opening.")
    created_at: CreatedAt
    updated_at: UpdatedAt


class OpeningsResponse(BaseModel):
    """Response body listing a service's weekly openings."""

    openings: list[OpeningResponse] = Field(default_factory=list)


class ClosingCreateRequest(BaseModel):
    """Request body for creating a closing: a date range and the services it closes."""

    date_from: date = Field(description="First date of the closing period (inclusive).")
    date_to: date = Field(description="Last date of the closing period (inclusive).")
    service_ids: list[UUID] = Field(
        description="Services this closing applies to. Pass every service of the venue for a "
                    "venue-wide shutdown.",
        min_length=1,
    )
    description: str | None = Field(
        default=None,
        description="Description of this closing.",
        max_length=1000,
    )

    @model_validator(mode="after")
    def _validate_period(self) -> "ClosingCreateRequest":
        if self.date_to < self.date_from:
            raise ValueError("date_to must not be earlier than date_from")
        return self


class ClosingUpdateRequest(BaseModel):
    """Request body for updating a closing. Unset fields are not modified; ``service_ids``, when
    given, replaces the full set of targeted services."""

    date_from: date | None = Field(
        default=None,
        description="New first date of the closing period (inclusive).",
    )
    date_to: date | None = Field(
        default=None,
        description="New last date of the closing period (inclusive).",
    )
    service_ids: list[UUID] | None = Field(
        default=None,
        description="New complete set of services this closing applies to.",
        min_length=1,
    )
    description: str | None = Field(
        default=None,
        description="New description of this closing.",
        max_length=1000,
    )

    @model_validator(mode="after")
    def _validate_period(self) -> "ClosingUpdateRequest":
        if self.date_from is not None and self.date_to is not None and self.date_to < self.date_from:
            raise ValueError("date_to must not be earlier than date_from")
        return self


class ClosingResponse(BaseModel):
    """Response body representing a closing."""

    id: ObjectUUID
    venue_id: UUID = Field(description="Identifier of the venue this closing belongs to.")
    date_from: date = Field(description="First date of the closing period (inclusive).")
    date_to: date = Field(description="Last date of the closing period (inclusive).")
    service_ids: list[UUID] = Field(
        default_factory=list,
        description="Services this closing applies to.",
    )
    description: str | None = Field(default=None, description="Description of this closing.")
    created_at: CreatedAt
    updated_at: UpdatedAt


class ClosingSortField(StrEnum):
    """Fields a closing search may be sorted by."""

    DATE_FROM = "date_from"
    DATE_TO = "date_to"
    CREATED_AT = "created_at"
    ID = "id"


class ClosingSearchQuery(SearchQuery, DateRangeFilter):
    """Paginated, sorted, date-range-filtered closing search query, optionally narrowed to one
    service."""

    sort_field_enum: ClassVar[type[StrEnum]] = ClosingSortField

    service_id: UUID | None = Field(
        default=None,
        description="Return only closings applying to this service.",
    )
