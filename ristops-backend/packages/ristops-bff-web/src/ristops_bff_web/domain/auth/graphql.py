# TODO: the lazy `role` / `user` field resolvers (e.g. on RoleGrant, ResourceUserGrants, Acl,
#  UserRoleGrant) are N+1 when selected across a page. Batch them with strawberry DataLoaders.
from datetime import datetime
from enum import Enum
from typing import Annotated, Protocol
from typing import Any

import strawberry

from ristops_bff_web.domain.auth.service import (
    find_user, find_me, update_user, find_role, find_user_roles, list_roles, grant_access,
    revoke_access, find_member, search_members, list_permissions, search_resource_grants,
)
from ristops_bff_web.graphql.pagination import Page, PaginationInput, SearchQueryParams, SortInput
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


class UserIdAware(Protocol):
    user_id: str


async def _resolve_role(root: RoleIdAware, _: strawberry.Info) -> Role:
    return await resolve_get_role(root.role_id)


async def resolve_get_member(user_id: EntityId) -> "Member":
    member = await find_member(user_id)
    return Member.from_dict(member)


async def resolve_search_members(
        _input: Annotated[
            "MemberSearchInput",
            strawberry.argument(description="Member search query.", name="input")
        ]
) -> Page["Member"]:
    params = MemberQueryParams(_input).build()
    page = await search_members(params)
    return Page.from_dict(page, Member.from_dict)


async def _resolve_member(root: UserIdAware, _: strawberry.Info) -> "Member":
    return await resolve_get_member(root.user_id)


async def resolve_search_resource_grants(
        _input: Annotated[
            "SearchResourceGrantsInput",
            strawberry.argument(description="Resource grants search query.", name="input")
        ]
) -> Page["ResourceUserGrants"]:
    params = ResourceGrantsQueryParams(_input).build()
    page = await search_resource_grants(_input.resource_type, _input.resource_id, params)
    return Page.from_dict(page, ResourceUserGrants.from_dict)


async def _resolve_list_roles(
        _input: Annotated[
            ListRolesInput,
            strawberry.argument(description="Query for roles.", name="input")
        ]) -> RolesList:
    roles = await list_roles(strawberry.asdict(_input))
    return RolesList.from_dict(roles)


async def _resolve_list_permissions(
        query: Annotated[
            str | None,
            strawberry.argument(description="Query for permissions using `contains` operator.", name="input")
        ] = None) -> PermissionsList:
    permissions = await list_permissions(query)
    return PermissionsList(permissions=permissions)


async def resolve_grant_access(
        _input: Annotated[
            GrantAccessInput,
            strawberry.argument(description="Access grant request.", name="input")
        ]
) -> Acl:
    acl = await grant_access(strawberry.asdict(_input))
    return Acl.from_dict(acl)


async def resolve_revoke_access(
        _input: Annotated[
            RevokeAccessInput,
            strawberry.argument(description="Access revoke request.", name="input")
        ]
) -> bool:
    await revoke_access(strawberry.asdict(_input))
    return True


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


@strawberry.type(
    description="List of app permissions.",
)
class PermissionsList:
    permissions: list[str] = strawberry.field(
        description="List of permissions.",
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


@strawberry.input(
    description="Request to grant a role to a user on a resource.",
)
class GrantAccessInput:
    user_id: str = strawberry.field(
        description="ID of the user to grant access to.",
    )
    role_id: str = strawberry.field(
        description="Role to grant on the resource.",
    )
    resource_id: str = strawberry.field(
        description="Resource identifier.",
    )
    resource_type: ResourceType = strawberry.field(
        description="Resource type.",
    )


@strawberry.input(
    description="Request to revoke a role from a user on a resource.",
)
class RevokeAccessInput:
    user_id: str = strawberry.field(
        description="ID of the user to revoke access from.",
    )
    role_id: str = strawberry.field(
        description="Role to revoke on the resource.",
    )
    resource_id: str = strawberry.field(
        description="Resource identifier.",
    )
    resource_type: ResourceType = strawberry.field(
        description="Resource type.",
    )


@strawberry.type(
    description="Access control entry granting a role to a user on a resource.",
)
class Acl:
    role_id: strawberry.Private[str]
    user_id: strawberry.Private[str]
    id: str = strawberry.field(description="ACL identifier.")
    created_at: datetime = strawberry.field(description="Creation date.")
    resource: AuthorizationResource = strawberry.field(
        description="Resource the access was granted on.",
    )
    role: Role = strawberry.field(
        description="Role granted on the resource.",
        resolver=_resolve_role,
    )
    user: "Member" = strawberry.field(
        description="User the access was granted to (public view).",
        resolver=_resolve_member,
    )

    @classmethod
    def from_dict(cls, obj: dict[str, Any]) -> "Acl":
        return Acl(
            id=obj["id"],
            created_at=obj["created_at"],
            role_id=obj["role_id"],
            user_id=obj["user_id"],
            resource=AuthorizationResource(
                resource_id=obj["resource"]["resource_id"],
                resource_type=obj["resource"]["resource_type"],
            ),
        )


@strawberry.type(
    description="Public view of a user.",
)
class Member:
    id: str = strawberry.field(description="User identifier.")
    username: str = strawberry.field(description="Username of the member.")
    display_name: str | None = strawberry.field(description="Display name of the member.")
    created_at: datetime = strawberry.field(description="Registration date.")

    @classmethod
    def from_dict(cls, obj: dict[str, Any]) -> "Member":
        return Member(
            id=obj["id"],
            username=obj["username"],
            display_name=obj.get("display_name"),
            created_at=obj["created_at"],
        )


@strawberry.input(
    description="Member search filter.",
)
class MemberFilterInput:
    username: str | None = strawberry.field(
        default=None,
        description="Filter by username using `like` operator.",
    )
    display_name: str | None = strawberry.field(
        default=None,
        description="Filter by display name using `like` operator.",
    )


@strawberry.enum(description="Fields a member search may be sorted by.")
class MemberSortField(Enum):
    ID = "id"
    USERNAME = "username"
    DISPLAY_NAME = "display_name"
    CREATED_AT = "created_at"


@strawberry.input(description="Member search query.")
class MemberSearchInput:
    pagination: PaginationInput = strawberry.field(
        default_factory=PaginationInput,
        description="Pagination parameters.",
    )
    sort: list[SortInput[MemberSortField]] = strawberry.field(
        default_factory=list,
        description="Sort instructions.",
    )
    filter: MemberFilterInput | None = strawberry.field(
        default=None,
        description="Filter parameters.",
    )


class MemberQueryParams(SearchQueryParams):
    """Builds the backend member-search query params from a MemberSearchInput."""

    def __init__(self, search: MemberSearchInput) -> None:
        super().__init__(search.pagination, search.sort)
        self._filter = search.filter

    def _finalize(self) -> None:
        if self._filter is not None:
            self._set_filter("username", self._filter.username)
            self._set_filter("display_name", self._filter.display_name)


@strawberry.type(description="A role granted to a user on a resource.")
class RoleGrant:
    role_id: strawberry.Private[str]
    resource: AuthorizationResource = strawberry.field(description="Resource the role is granted on.")
    assigned_at: datetime = strawberry.field(description="Assignment date.")
    role: Role = strawberry.field(
        description="Role granted on the resource.",
        resolver=_resolve_role,
    )

    @classmethod
    def from_dict(cls, obj: dict[str, Any]) -> "RoleGrant":
        return RoleGrant(
            role_id=obj["role_id"],
            resource=AuthorizationResource(
                resource_id=obj["resource"]["resource_id"],
                resource_type=obj["resource"]["resource_type"],
            ),
            assigned_at=datetime.fromisoformat(obj["assigned_at"]),
        )


@strawberry.type(description="A user and the roles they hold on a resource (direct or inherited).")
class ResourceUserGrants:
    user_id: strawberry.Private[str]
    grants: list[RoleGrant] = strawberry.field(description="Roles the user holds on the resource.")
    user: Member = strawberry.field(
        description="The user the grants belong to (public view).",
        resolver=_resolve_member,
    )

    @classmethod
    def from_dict(cls, obj: dict[str, Any]) -> "ResourceUserGrants":
        return ResourceUserGrants(
            user_id=obj["user_id"],
            grants=[RoleGrant.from_dict(grant) for grant in obj["grants"]],
        )


@strawberry.input(description="Resource grants search filter.")
class ResourceGrantsFilterInput:
    username: str | None = strawberry.field(
        default=None,
        description="Filter by username using `like` operator.",
    )
    display_name: str | None = strawberry.field(
        default=None,
        description="Filter by display name using `like` operator.",
    )
    permission: str | None = strawberry.field(
        default=None,
        description="Filter by permission using `contains` operator.",
    )
    role_id: str | None = strawberry.field(
        default=None,
        description="Filter by role id using `contains` operator.",
    )
    role_name: str | None = strawberry.field(
        default=None,
        description="Filter by role name using `contains` operator.",
    )


@strawberry.enum(description="Fields a resource grants search may be sorted by.")
class ResourceGrantSortField(Enum):
    ID = "id"
    USERNAME = "username"
    DISPLAY_NAME = "display_name"


@strawberry.input(description="Resource grants search query.")
class SearchResourceGrantsInput:
    resource_type: ResourceType = strawberry.field(description="Resource type.")
    resource_id: str = strawberry.field(description="Resource identifier.")
    pagination: PaginationInput = strawberry.field(
        default_factory=PaginationInput,
        description="Pagination parameters.",
    )
    sort: list[SortInput[ResourceGrantSortField]] = strawberry.field(
        default_factory=list,
        description="Sort instructions.",
    )
    filter: ResourceGrantsFilterInput | None = strawberry.field(
        default=None,
        description="Filter parameters.",
    )


class ResourceGrantsQueryParams(SearchQueryParams):
    """Builds the backend resource-grants query params from a SearchResourceGrantsInput."""

    def __init__(self, search: "SearchResourceGrantsInput") -> None:
        super().__init__(search.pagination, search.sort)
        self._filter = search.filter

    def _finalize(self) -> None:
        if self._filter is not None:
            self._set_filter("username", self._filter.username)
            self._set_filter("display_name", self._filter.display_name)
            self._set_filter("permission", self._filter.permission)
            self._set_filter("role_id", self._filter.role_id)
            self._set_filter("role_name", self._filter.role_name)


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
        description="List app roles",
    )
    list_permissions: PermissionsList = strawberry.field(
        resolver=_resolve_list_permissions,
        description="List app permissions",
    )
    member: Member = strawberry.field(
        resolver=resolve_get_member,
        description="Fetch a member (public user view) by ID",
    )
    search_members: Page[Member] = strawberry.field(
        resolver=resolve_search_members,
        description="Search members (public user view)",
    )
    search_resource_grants: Page[ResourceUserGrants] = strawberry.field(
        resolver=resolve_search_resource_grants,
        description="Search users with their granted roles on a resource (direct or inherited)",
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
    grant_access = strawberry.mutation(
        resolver=resolve_grant_access,
        description="Grant a role to a user on a resource",
    )
    revoke_access = strawberry.mutation(
        resolver=resolve_revoke_access,
        description="Revoke a role from a user on a resource",
    )
