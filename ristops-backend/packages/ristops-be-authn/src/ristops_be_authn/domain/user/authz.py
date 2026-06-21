from uuid import UUID

from pydantic import BaseModel, Field


class VenueSearchScope(BaseModel):
    """Full venue search scope."""
    id_venues: list[UUID] | None = Field(
        description="List of venue IDs the user has access to. ``None`` means all venues."
    )
