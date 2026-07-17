from enum import StrEnum
from typing import ClassVar
from zoneinfo import available_timezones

from pydantic import BaseModel, Field, field_validator

from ristops_be_venue.domain.models import VenueStatus, VenueActionType
from ristops_lib_core.pydantic.types import ObjectUUID, CreatedAt, UpdatedAt
from ristops_lib_core.schema.pagination import SearchQuery


def _validate_timezone(value: str | None) -> str | None:
    """Validate that the given value is a known IANA timezone name, if set."""
    if value is not None and value not in available_timezones():
        raise ValueError(f"Unknown IANA timezone: {value}")
    return value


class VenueCreationRequest(BaseModel):
    """Request body for creating a new venue."""

    name: str = Field(
        description="Name of the venue.",
        max_length=120,
    )
    address: str = Field(
        description="Address of the venue.",
        max_length=255,
    )
    description: str | None = Field(
        default=None,
        description="Optional description of the venue.",
        max_length=1000,
    )
    timezone: str = Field(
        description="IANA timezone name of the venue (e.g. 'Europe/Rome').",
    )

    _validate_timezone = field_validator("timezone")(_validate_timezone)


class VenueUpdateRequest(BaseModel):
    """Request body for updating an existing venue. Unset fields are not modified."""

    name: str | None = Field(
        default=None,
        description="New name of the venue.",
        max_length=120,
    )
    address: str | None = Field(
        default=None,
        description="New address of the venue.",
        max_length=255,
    )
    description: str | None = Field(
        default=None,
        description="New description of the venue.",
        max_length=1000,
    )
    timezone: str | None = Field(
        default=None,
        description="New IANA timezone name of the venue.",
    )

    _validate_timezone = field_validator("timezone")(_validate_timezone)


class VenueActionRequest(BaseModel):
    """Request body for performing a lifecycle action on a venue."""

    action_type: VenueActionType = Field(description="The action to perform.")


class VenueResponse(BaseModel):
    """Response body representing a venue."""

    id: ObjectUUID
    name: str = Field(description="Name of the venue.")
    address: str = Field(description="Address of the venue.")
    description: str | None = Field(default=None, description="Description of the venue.")
    timezone: str = Field(description="IANA timezone name of the venue.")
    status: VenueStatus = Field(description="Current lifecycle status of the venue.")
    created_at: CreatedAt
    updated_at: UpdatedAt


class VenueSortField(StrEnum):
    """Fields a venue search may be sorted by."""

    ID = "id"
    NAME = "name"
    CREATED_AT = "created_at"


class VenueSearchFilter(BaseModel):
    """Filter parameters for venue search, exposed as `filter.<field>` query params."""

    name: str | None = Field(
        default=None,
        description="Filter by name of the venue using a like operator.",
    )


class VenueSearchQuery(SearchQuery, VenueSearchFilter):
    """Full venue search query: pagination, sort, and filter combined."""

    sort_field_enum: ClassVar[type[StrEnum]] = VenueSortField
