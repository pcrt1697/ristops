from pydantic import BaseModel, Field, SecretStr
from pydantic import EmailStr

from ristops_lib_core.schema.types import ObjectUUID, CreatedAt, UpdatedAt


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


class UserCreationRequest(BaseModel):
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
