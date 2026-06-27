from enum import StrEnum
from typing import ClassVar

from pydantic import BaseModel, Field

from ristops_lib_core.schema.pagination import SearchQuery


class ResourceUserSortField(StrEnum):
    """Fields a resource user search may be sorted by."""

    ID = "id"
    USERNAME = "username"
    DISPLAY_NAME = "display_name"


class ResourceUserSearchFilter(BaseModel):
    """Filter parameters for resource user search, exposed as `filter.<field>` query params."""

    username: str | None = Field(
        default=None,
        description="Filter by username using `contains` operator.",
    )
    display_name: str | None = Field(
        default=None,
        description="Filter by display name using `contains` operator.",
    )
    permission: str | None = Field(
        default=None,
        description="Filter by permission using `contains` operator.",
    )
    role_id: str | None = Field(
        default=None,
        description="Filter by role using `contains` operator.",
    )
    role_name: str | None = Field(
        default=None,
        description="Filter by role name using `contains` operator.",
    )


class ResourceUserSearchQuery(SearchQuery, ResourceUserSearchFilter):
    """Full resource user search query: pagination, sort, and filter combined."""

    sort_field_enum: ClassVar[type[StrEnum]] = ResourceUserSortField
