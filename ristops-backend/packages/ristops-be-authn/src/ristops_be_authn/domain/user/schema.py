from pydantic import BaseModel, Field, EmailStr, SecretStr


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
