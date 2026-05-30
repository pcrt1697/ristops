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


class AuthorizationResourceResponse(BaseModel):
    resource_type: str = Field(description="Resource type")
    resource_id: str = Field(description="Resource identifier")


class AuthorizationResourcesResponse(BaseModel):
    resources: list[AuthorizationResourceResponse] = Field(description="List of resources")


class AuthorizationUserResponse(BaseModel):
    user_id: str = Field(description="User identifier")


class AclResponse(BaseModel):
    id: str = Field(description="Acl ID")
    created_at: datetime = Field(description="Acl creation time")
