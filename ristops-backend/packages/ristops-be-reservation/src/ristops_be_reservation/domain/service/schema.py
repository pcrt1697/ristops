from datetime import time, date
from enum import StrEnum
from typing import ClassVar
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from ristops_be_reservation.domain.models import Weekday
from ristops_lib_core.pydantic.types import ObjectUUID, CreatedAt, UpdatedAt, DeletedAt
from ristops_lib_core.schema.pagination import SortableQuery


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
    turn_time_m: int = Field(
        description="Reservation duration, in minutes.",
        gt=0,
    )
    advance_notice_m: int = Field(
        description="Minimum notice required before a reservation slot, in minutes.",
        ge=0,
    )
    slot_interval_m: int = Field(
        description="Interval between reservation slots, in minutes.",
        gt=0,
    )
    grace_period_m: int = Field(
        description="Minutes past a reservation's start time before it may be marked as a no-show.",
        ge=0,
    )


class ServiceResponse(BaseModel):
    """Response body representing a service."""

    id: ObjectUUID
    venue_id: UUID = Field(description="Identifier of the venue this service belongs to.")
    name: str = Field(description="Name of the service.")
    description: str | None = Field(default=None, description="Description of the service.")
    turn_time_m: int = Field(description="Reservation duration, in minutes.")
    advance_notice_m: int = Field(description="Minimum notice required before a reservation slot, in minutes.")
    slot_interval_m: int = Field(description="Interval between reservation slots, in minutes.")
    grace_period_m: int = Field(
        description="Minutes past a reservation's start time before it may be marked as a no-show.",
    )
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
    include_deleted: bool = Field(
        default=False,
        description="Include deleted services. Excluded by default.",
    )


class ServiceListQuery(SortableQuery, ServiceListFilter):
    """Full service list query: sort and filter combined. Not paginated."""

    sort_field_enum: ClassVar[type[StrEnum]] = ServiceSortField


class ServiceOpeningUpsertRequest(BaseModel):
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


class ServiceOpeningResponse(BaseModel):
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


class ServiceOpeningsUpsertRequest(BaseModel):
    """Request body for replacing the full set of openings for a service. Openings are
    configured as a whole set at setup time, so this stays a bulk, list-replace operation
    (unlike overrides/closings, which are one-off special cases created individually)."""

    openings: list[ServiceOpeningUpsertRequest] = Field(
        description="The complete set of openings to apply. Openings for weekdays not "
                    "included here are removed.",
    )

    @model_validator(mode="after")
    def _validate_no_duplicate_weekdays(self) -> "ServiceOpeningsUpsertRequest":
        weekdays = {opening.weekday for opening in self.openings}
        if len(self.openings) != len(weekdays):
            raise ValueError("Duplicate weekday in openings list")
        return self


class ServiceOpeningsResponse(BaseModel):
    """Response body listing a service's openings."""

    openings: list[ServiceOpeningResponse]


class ServiceOpeningOverrideCreateRequest(BaseModel):
    """Request body for creating a new opening override."""

    date_start: date = Field(description="First date of the override period (inclusive).")
    date_end: date = Field(description="Last date of the override period (inclusive).")
    capacity: int = Field(description="Overridden maximum number of reservable seats.", gt=0)
    start_time: time = Field(description="Overridden opening time.")
    end_time: time = Field(description="Overridden closing time.")
    description: str | None = Field(
        default=None,
        description="Description of this override.",
        max_length=1000,
    )


class ServiceOpeningOverrideUpdateRequest(BaseModel):
    """Request body for updating an opening override. Unset fields are not modified."""

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


class ServiceOpeningOverrideResponse(BaseModel):
    """Response body representing a service opening override."""

    id: ObjectUUID
    service_id: UUID = Field(description="Identifier of the service this override belongs to.")
    date_start: date = Field(description="First date of the override period (inclusive).")
    date_end: date = Field(description="Last date of the override period (inclusive).")
    capacity: int = Field(description="Overridden maximum number of reservable seats.")
    start_time: time = Field(description="Overridden opening time.")
    end_time: time = Field(description="Overridden closing time.")
    description: str | None = Field(default=None, description="Description of this override.")
    created_at: CreatedAt
    updated_at: UpdatedAt


class ServiceOpeningOverridesResponse(BaseModel):
    """Response body listing a service's opening overrides."""

    opening_overrides: list[ServiceOpeningOverrideResponse]


class ServiceClosingCreateRequest(BaseModel):
    """Request body for creating a new closing."""

    date_start: date = Field(description="First date of the closing period (inclusive).")
    date_end: date = Field(description="Last date of the closing period (inclusive).")
    description: str | None = Field(
        default=None,
        description="Description of this closing.",
        max_length=1000,
    )


class ServiceClosingUpdateRequest(BaseModel):
    """Request body for updating a closing. Unset fields are not modified."""

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
    description: str | None = Field(default=None, description="Description of this closing.")
    created_at: CreatedAt
    updated_at: UpdatedAt


class ServiceClosingsResponse(BaseModel):
    """Response body listing a service's closings."""

    closings: list[ServiceClosingResponse]
