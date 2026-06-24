from datetime import datetime
from typing import Annotated, Protocol
from typing import Any

import strawberry

from ristops_bff_web.domain.auth.service import find_user, find_me, update_user, find_role, find_user_roles, list_roles
from ristops_bff_web.graphql.types import EntityId
from ristops_lib_core.context import APP_CONTEXT, ContextKey
from ristops_lib_core.schema.authz import ResourceType as _ResourceType


async def resolve_get_user(
        user_id: EntityId
) -> User:
    user = await find_user(user_id)
    return User.from_dict(user)


async def resolve_get_me() -> User:
    me = await find_me()
    return User.from_dict(me)


async def resolve_update_user(
        user_id: EntityId,
        _input: Annotated[
            UpdateUserInput,
            strawberry.argument(description="User information to update.", name="input")
        ]
) -> User:
    user = await update_user(user_id, strawberry.asdict(_input))
    return User.from_dict(user)


async def resolve_update_me(
        _input: Annotated[
            UpdateUserInput,
            strawberry.argument(description="User information to update.", name="input")
        ]
) -> User:
    """Update the currently authenticated user."""
    user_id = APP_CONTEXT.get_or_throw(ContextKey.USER_ID)
    return await resolve_update_user(user_id, _input)


async def resolve_get_role(
        role_id: str
) -> Role:
    role = await find_role(role_id)
    return Role.from_dict(role)


async def resolve_get_my_grants(
        _input: Annotated[
            ListGrantsInput,
            strawberry.argument(description="Query for user grants.", name="input")
        ]
) -> UserRoleGrants:
    user_id = APP_CONTEXT.get_or_throw(ContextKey.USER_ID)
    grants_data = await find_user_roles(user_id, strawberry.asdict(_input))
    return UserRoleGrants(grants=[
        UserRoleGrant(
            resource=AuthorizationResource(
                resource_id=grant["resource"]["resource_id"],
                resource_type=grant["resource"]["resource_type"],
            ),
            role_id=grant["role_id"],
        )
        for grant in grants_data["grants"]
    ])


class RoleIdAware(Protocol):
    role_id: str


async def _resolve_role(root: RoleIdAware, _: strawberry.Info) -> Role:
    return await resolve_get_role(root.role_id)


async def _resolve_list_roles(
        _input: Annotated[
            ListRolesInput,
            strawberry.argument(description="Query for roles.", name="input")
        ]) -> RolesList:
    roles = await list_roles(strawberry.asdict(_input))
    return RolesList.from_dict(roles)


ResourceType = strawberry.enum(_ResourceType)


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
        return User(
            id=obj["id"],
            username=obj["username"],
            display_name=obj.get("display_name"),
            email=obj["email"],
            created_at=obj["created_at"],
            updated_at=obj["updated_at"],
        )


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


@strawberry.type(
    description="Role entity information.",
)
class Role:
    id: str = strawberry.field(description="Role identifier.")
    name: str = strawberry.field(description="Name of the role.")
    description: str = strawberry.field(description="Description of the role.")
    permissions: list[str] = strawberry.field(description="List of permissions granted by the role.")

    @classmethod
    def from_dict(cls, obj: dict[str, Any]) -> "Role":
        return Role(
            id=obj["id"],
            name=obj["name"],
            description=obj["description"],
            permissions=obj["permissions"],
        )


@strawberry.type(
    description="Authorization resource definition.",
)
class AuthorizationResource:
    resource_id: str = strawberry.field(description="ACL resource identifier")
    resource_type: ResourceType = strawberry.field(description="ACL resource type")


@strawberry.type(
    description="Resource the user has access to, given a specific set of permissions.",
)
class UserRoleGrant:
    role_id: strawberry.Private[str]
    resource: AuthorizationResource = strawberry.field(
        description="Resource identifier.",
    )
    role: Role = strawberry.field(
        description="Role assigned on the resource.",
        resolver=_resolve_role
    )


@strawberry.type(
    description="Resources the user has access to, given a specific set of permissions.",
)
class UserRoleGrants:
    grants: list[UserRoleGrant] = strawberry.field(
        description="List of resources the user has access to, given a specific set of permissions.",
    )


@strawberry.input(
    description="Input query to list roles.",
)
class ListRolesInput:
    role_id: str | None = strawberry.field(
        default=None,
        description="Filter by role id using `contains` operator.",
    )
    role_name: str | None = strawberry.field(
        default=None,
        description="Filter by role name using `contains` operator.",
    )
    permission: str | None = strawberry.field(
        default=None,
        description="Filter by permission using `contains` operator.",
    )


@strawberry.type(
    description="List of app roles.",
)
class RolesList:
    roles: list[Role] = strawberry.field(
        description="List of roles.",
    )

    @classmethod
    def from_dict(cls, items: list[dict[str, Any]]) -> "RolesList":
        return RolesList(
            roles=[
                Role.from_dict(role)
                for role in items
            ]
        )


@strawberry.input(
    description="Input query to list grants.",
)
class ListGrantsInput:
    resource_id: str = strawberry.field(
        description="Resource identifier.",
    )
    resource_type: ResourceType = strawberry.field(
        description="Resource type.",
    )


@strawberry.type
class AuthQuery:
    user: User = strawberry.field(
        resolver=resolve_get_user,
        description="Fetch user by ID",
    )
    me: User = strawberry.field(
        resolver=resolve_get_me,
        description="Fetch authenticated user",
    )
    role: Role = strawberry.field(
        resolver=resolve_get_role,
        description="Fetch role by ID",
    )
    my_grants: UserRoleGrants = strawberry.field(
        resolver=resolve_get_my_grants,
        description="Fetch roles assigned to the authenticated user on a resource",
    )
    list_roles: RolesList = strawberry.field(
        resolver=_resolve_list_roles,
        description="List app roles, optionally filtered by id, name or permission",
    )


@strawberry.type
class AuthMutation:
    update_user = strawberry.mutation(
        resolver=resolve_update_user,
        description="Update user data by ID",
    )
    update_me = strawberry.mutation(
        resolver=resolve_update_me,
        description="Update current user data",
    )
