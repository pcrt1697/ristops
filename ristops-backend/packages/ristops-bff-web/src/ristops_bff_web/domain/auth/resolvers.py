from typing import Annotated

import strawberry

from ristops_bff_web.domain.auth.models import User, UpdateUserInput
from ristops_bff_web.domain.auth.service import find_user, find_me, update_user
from ristops_bff_web.types import EntityId


async def _get_user(
        user_id: EntityId
) -> User:
    user = await find_user(user_id)
    return User.from_dict(user)


async def _get_me() -> User:
    me = await find_me()
    return User.from_dict(me)


async def _update_user(
        user_id: EntityId,
        _input: Annotated[
            UpdateUserInput,
            strawberry.argument(description="User information to update.", name="input")
        ]
) -> User:
    user = await update_user(user_id, _input)
    return User.from_dict(user)


@strawberry.type
class AuthQuery:
    user: User = strawberry.field(
        resolver=_get_user,
        description="Fetch user by ID",
    )
    me: User = strawberry.field(
        resolver=_get_me,
        description="Fetch authenticated user",
    )


@strawberry.type
class AuthMutation:
    update_user = strawberry.mutation(
        resolver=_update_user,
        description="Update user data",
    )
