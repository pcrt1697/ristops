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


class AuthorizationResponse(BaseModel):
    is_authorized: bool = Field(description="Indicates whether the user is authorized to access the resource")


class GrantAccessRequest(AuthorizationResource):
    user_id: str = Field(description="ID of the user to grant access to")
    role_id: str = Field(description="Role used to grant access to resource")


class CreateAuthorizationResourceRequest(BaseModel):
    resources: list[AuthorizationResource] = Field(description="List of resources to create")


class AuthorizationUserResponse(BaseModel):
    user_id: str = Field(description="User identifier")


class AclResponse(BaseModel):
    id: str = Field(description="Acl ID")
    created_at: datetime = Field(description="Acl creation time")


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
