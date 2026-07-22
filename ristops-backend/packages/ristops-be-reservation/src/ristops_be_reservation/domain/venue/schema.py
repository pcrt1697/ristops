from datetime import date
from enum import StrEnum
from typing import ClassVar
from uuid import UUID

from pydantic import BaseModel, Field

from ristops_be_reservation.domain.models import Weekday
from ristops_be_reservation.domain.schedule.schema import DateRangeFilter
from ristops_lib_core.pydantic.types import ObjectUUID, UpdatedAt, CreatedAt
from ristops_lib_core.schema.pagination import SearchQuery


class VenueClosingCreateRequest(BaseModel):
    """Request body for creating a new venue-wide closing. Bulk: one row is created per weekday
    given in ``weekdays`` (in a single transaction); omitted/empty, or all seven weekdays,
    collapses to a single every-day row (``weekday`` null)."""

    date_start: date = Field(description="First date of the closing period (inclusive).")
    date_end: date = Field(description="Last date of the closing period (inclusive).")
    weekdays: list[Weekday] | None = Field(
        default=None,
        description="Weekdays to scope to; provide multiple to create one row per weekday. "
                    "Omit, or include all 7, for every day.",
    )
    description: str | None = Field(
        default=None,
        description="Description of this venue closing.",
        max_length=1000,
    )


class VenueClosingUpdateRequest(BaseModel):
    """Request body for updating a venue closing. Unset fields are not modified."""

    date_start: date | None = Field(
        default=None,
        description="New first date of the closing period (inclusive).",
    )
    date_end: date | None = Field(
        default=None,
        description="New last date of the closing period (inclusive).",
    )
    weekday: Weekday | None = Field(
        default=None,
        description="New weekday the closing applies to; null means every day in the range.",
    )
    description: str | None = Field(
        default=None,
        description="New description of this venue closing.",
        max_length=1000,
    )


class VenueClosingResponse(BaseModel):
    """Response body representing a venue-wide closing."""

    id: ObjectUUID
    venue_id: UUID = Field(description="Identifier of the venue this closing belongs to.")
    date_start: date = Field(description="First date of the closing period (inclusive).")
    date_end: date = Field(description="Last date of the closing period (inclusive).")
    weekday: Weekday | None = Field(
        default=None,
        description="Weekday the closing applies to within the range; null means every day.",
    )
    description: str | None = Field(default=None, description="Description of this venue closing.")
    created_at: CreatedAt
    updated_at: UpdatedAt


class VenueClosingSortField(StrEnum):
    """Fields a venue-closing search may be sorted by."""

    DATE_START = "date_start"
    DATE_END = "date_end"
    CREATED_AT = "created_at"
    ID = "id"


class VenueClosingSearchQuery(SearchQuery, DateRangeFilter):
    """Paginated, sorted, date-range-filtered venue-closing search query."""

    sort_field_enum: ClassVar[type[StrEnum]] = VenueClosingSortField
