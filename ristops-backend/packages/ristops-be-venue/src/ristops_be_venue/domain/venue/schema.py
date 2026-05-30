from pydantic import BaseModel, Field

from ristops_lib_core.schema.types import ObjectUUID, CreatedAt, UpdatedAt


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


class VenueResponse(BaseModel):
    """Response body representing a venue."""

    id: ObjectUUID
    name: str = Field(description="Name of the venue.")
    address: str = Field(description="Address of the venue.")
    description: str | None = Field(default=None, description="Description of the venue.")
    created_at: CreatedAt
    updated_at: UpdatedAt
