from pydantic import BaseModel, Field, EmailStr, SecretStr


class UserCreationRequest(BaseModel):
    """Request body for registering a new user via the BFF."""

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
