from datetime import time, date
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from ristops_be_reservation.domain.models import Weekday
from ristops_lib_core.pydantic.types import ObjectUUID, CreatedAt, UpdatedAt


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


class OpeningOverrideUpdateRequest(BaseModel):
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


class OpeningOverrideResponse(BaseModel):
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


class OpeningOverridesResponse(BaseModel):
    """Response body listing a service's opening overrides."""

    opening_overrides: list[OpeningOverrideResponse]


class ClosingCreateRequest(BaseModel):
    """Request body for creating a new closing."""

    date_start: date = Field(description="First date of the closing period (inclusive).")
    date_end: date = Field(description="Last date of the closing period (inclusive).")
    description: str | None = Field(
        default=None,
        description="Description of this closing.",
        max_length=1000,
    )


class ClosingUpdateRequest(BaseModel):
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


class ClosingResponse(BaseModel):
    """Response body representing a service closing."""

    id: ObjectUUID
    service_id: UUID = Field(description="Identifier of the service this closing belongs to.")
    date_start: date = Field(description="First date of the closing period (inclusive).")
    date_end: date = Field(description="Last date of the closing period (inclusive).")
    description: str | None = Field(default=None, description="Description of this closing.")
    created_at: CreatedAt
    updated_at: UpdatedAt


class ClosingsResponse(BaseModel):
    """Response body listing a service's closings."""

    closings: list[ClosingResponse]
