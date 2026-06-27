from pydantic import BaseModel, Field
from pydantic import EmailStr

from ristops_lib_core.pydantic.types import ObjectUUID, CreatedAt, UpdatedAt


class UserResponse(BaseModel):
    id: ObjectUUID
    username: str = Field(
        description="Username of the user.",
    )
    display_name: str | None = Field(
        default=None,
        description="Display name of the user.",
    )
    email: EmailStr = Field(
        description="Email address of the user.",
    )
    created_at: CreatedAt
    updated_at: UpdatedAt


class AppMember(BaseModel):
    """Base model for app members."""
    id: ObjectUUID
    username: str = Field(description="Username of the member.")
    display_name: str | None = Field(default=None, description="Display name of the member.")


class MemberResponse(AppMember):
    """Public view of a user, readable by any authenticated user."""
    created_at: CreatedAt
