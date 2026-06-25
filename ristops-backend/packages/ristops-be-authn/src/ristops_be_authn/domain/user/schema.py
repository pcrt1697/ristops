from enum import StrEnum
from typing import ClassVar

from pydantic import BaseModel, Field, EmailStr, SecretStr

from ristops_lib_core.pydantic.types import ObjectUUID, CreatedAt
from ristops_lib_core.schema.pagination import SearchQuery


class UserCreationRequest(BaseModel):
    """Request body for creating a new user."""

    username: str = Field(
        description="Username of the user to register.",
    )
    display_name: str | None = Field(
        default=None,
        description="Display name of the user to register.",
    )
    email: EmailStr = Field(
        description="Email address of the user to register.",
    )
    password: SecretStr = Field(
        description="Password of the user to register.",
        min_length=8,
    )


class UserUpdateRequest(BaseModel):
    username: str | None = Field(
        default=None,
        description="New username of the user.",
    )
    display_name: str | None = Field(
        default=None,
        description="New display name of the user.",
    )
    email: EmailStr | None = Field(
        default=None,
        description="New email address of the user.",
    )
    password: SecretStr | None = Field(
        default=None,
        description="New password of the user.",
        min_length=8,
    )


class MemberResponse(BaseModel):
    """Public view of a user, readable by any authenticated user."""

    id: ObjectUUID
    username: str = Field(description="Username of the member.")
    display_name: str | None = Field(default=None, description="Display name of the member.")
    created_at: CreatedAt


class MemberSortField(StrEnum):
    """Fields a member search may be sorted by."""

    ID = "id"
    USERNAME = "username"
    DISPLAY_NAME = "display_name"
    CREATED_AT = "created_at"


class MemberSearchFilter(BaseModel):
    """Filter parameters for member search, exposed as `filter.<field>` query params."""

    username: str | None = Field(
        default=None,
        description="Filter by username using a like operator.",
    )
    display_name: str | None = Field(
        default=None,
        description="Filter by display name using a like operator.",
    )


class MemberSearchQuery(SearchQuery, MemberSearchFilter):
    """Full member search query: pagination, sort, and filter combined."""

    sort_field_enum: ClassVar[type[StrEnum]] = MemberSortField
