from pydantic import BaseModel, Field, EmailStr, SecretStr


class LoginRequest(BaseModel):
    email: EmailStr = Field(
        description="Email address of the user to log in.",
    )
    password: SecretStr = Field(
        description="Password of the user to log in.",
    )


class LoginResponse(BaseModel):
    user_id: str = Field(
        description="Username of the user.",
    )
    access_token: str = Field(
        description="Access token to use for user authentication.",
    )
    refresh_token: str = Field(
        description="Token to use for refreshing access token.",
    )


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(
        description="Token to use for refreshing access token.",
    )
