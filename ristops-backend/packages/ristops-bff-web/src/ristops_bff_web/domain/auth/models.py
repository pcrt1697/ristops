from datetime import datetime
from typing import Any

import strawberry


@strawberry.type(
    description="User entity information.",
)
class User:
    id: str = strawberry.field(
        description="User identifier.",
    )
    username: str = strawberry.field(
        description="Username of the user.",
    )
    display_name: str | None = strawberry.field(
        description="Display name of the user.",
    )
    email: str = strawberry.field(
        description="Email address of the user.",
    )
    created_at: datetime = strawberry.field(
        description="Registration date.",
    )
    updated_at: datetime = strawberry.field(
        description="Last update date.",
    )

    @classmethod
    def from_dict(cls, obj: dict[str, Any]) -> "User":
        return User(**obj)


@strawberry.input(
    description="User information to update.",
)
class UpdateUserInput:
    username: str | None = strawberry.field(
        default=None,
        description="New username of the user.",
    )
    display_name: str | None = strawberry.field(
        default=None,
        description="New display name of the user.",
    )
    email: str | None = strawberry.field(
        default=None,
        description="New email address of the user.",
    )
    password: str | None = strawberry.field(
        default=None,
        description="New password of the user.",
    )
