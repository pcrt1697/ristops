from enum import StrEnum
from typing import ClassVar
from uuid import UUID

from pydantic import BaseModel, Field

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
