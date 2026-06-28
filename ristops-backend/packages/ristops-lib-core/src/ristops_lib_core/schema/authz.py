from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class ResourceType(StrEnum):
    APP = 'app'
    VENUE = 'venue'
    PERMISSION = 'permission'
    ROLE = 'role'
    ACL = 'acl'
    USER = 'user'


class PermissionAction(StrEnum):
    GET = 'get'
    LIST = 'list'
    ADD = 'add'
    EDIT = 'edit'
    REMOVE = 'remove'
    MANAGE = '*'


# Separator between a permission's scope and action (e.g. "venue:add").
PERMISSION_SEPARATOR = ":"


class AuthorizationResource(BaseModel):
    """ ACL resource definition."""
    resource_id: str = Field(description="ACL resource identifier")
    resource_type: ResourceType = Field(description="ACL resource type")


class AuthorizationGrant(BaseModel):
    """ ACL grant resource definition. """
    resource: AuthorizationResource = Field(
        description="ACL resource",
    )
    permissions: list[str] = Field(description="List of permission")


class CheckAuthorizationRequest(BaseModel):
    user_id: UUID = Field(description="Identifier of the user associated with the request")
    grants: list[AuthorizationGrant]


class AclCheckRequest(BaseModel):
    """Body for an ACL check; the user comes from the path."""
    grants: list[AuthorizationGrant] = Field(description="Grants to evaluate for the user")


class AuthorizationResponse(BaseModel):
    is_authorized: bool = Field(description="Indicates whether the user is authorized to access the resource")


class GrantAccessRequest(BaseModel):
    user_id: str = Field(description="ID of the user to grant access to")
    role_id: str = Field(description="Role used to grant access to resource")
    resource: AuthorizationResource = Field(description="Resource to grant access on")


class GrantRoleRequest(BaseModel):
    """Body for granting a role on a resource; the resource comes from the path."""
    user_id: str = Field(description="ID of the user to grant the role to")
    role_id: str = Field(description="Role to grant on the resource")


class RevokeAccessRequest(BaseModel):
    user_id: str = Field(description="ID of the user to revoke access from")
    role_id: str = Field(description="Role to revoke on the resource")
    resource: AuthorizationResource = Field(description="Resource to revoke access on")


class CreateAuthorizationResourceRequest(BaseModel):
    resources: list[AuthorizationResource] = Field(description="List of resources to create")


class AuthorizationUserResponse(BaseModel):
    user_id: str = Field(description="User identifier")


class AclResponse(BaseModel):
    id: str = Field(description="Acl ID")
    created_at: datetime = Field(description="Acl creation time")
    user_id: str = Field(description="ID of the user the access was granted to")
    role_id: str = Field(description="ID of the role granted on the resource")
    resource: AuthorizationResource = Field(description="Resource the access was granted on")


class RoleResponse(BaseModel):
    id: str = Field(description="Role identifier")
    name: str = Field(description="Role name")
    description: str = Field(description="Role description")
    permissions: list[str] = Field(description="Permissions granted by the role")


class RolePermissions(BaseModel):
    role_id: str = Field(description="Role that grants the permissions")
    permissions: list[str] = Field(description="Permissions granted by the role")


class PermissionGrant(BaseModel):
    """A set of permissions derived from a single role granted on a specific resource."""
    resource: AuthorizationResource = Field(description="Resource on which the role is assigned")
    role_id: str = Field(description="Role that grants the permissions")


class ListUserGrantsResponse(BaseModel):
    grants: list[PermissionGrant] = Field(description="Permission grants, grouped by role and source resource")


class ResourceGrant(BaseModel):
    resource: AuthorizationResource
    roles: list[RolePermissions] = Field(description="Roles granted by the resource")


class ListUserResourceGrantsResponse(BaseModel):
    grants: list[ResourceGrant] = Field(description="Permission grants, grouped by role and source resource")


class ListRolesQuery(BaseModel):
    role_id: str | None = Field(default=None, description="Filter by role id using `contains` operator")
    role_name: str | None = Field(default=None, description="Filter by role name using `contains` operator")
    permission: str | None = Field(default=None, description="Filter by permission name using `contains` operator")


class ListRolesResponse(BaseModel):
    roles: list[RoleResponse] = Field(description="List of roles")


class ListPermissionsResponse(BaseModel):
    permissions: list[str] = Field(description="List of permissions")


class ResourceUsersSearchQuery(BaseModel):
    permission: str | None = Field(default=None, description="Filter by permission using `contains` operator")
    role_id: str | None = Field(default=None, description="Filter by role ID using `contains` operator")
    role_name: str | None = Field(default=None, description="Filter by role name using `contains` operator")


class RoleGrant(BaseModel):
    resource: AuthorizationResource = Field(description="Resource to which the role is granted")
    role_id: str = Field(description="ID of the role granted on the resource")
    assigned_at: datetime = Field(description="Assignment date")


class ResourceUserGrantsResponse(BaseModel):
    user_id: str = Field(description="User identifier")
    grants: list[RoleGrant] = Field(description="List of grants")
