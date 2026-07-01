import logging
from datetime import datetime, UTC
from enum import StrEnum

from pydantic import BaseModel, Field

from ristops_lib_neo4j.migration import MigrationNode

logging.getLogger("neo4j.notifications").setLevel(logging.WARNING)


class RelationType(StrEnum):
    BELONGS_TO = "BELONGS_TO"  # child resource -> parent resource
    GRANTS = "GRANTS"  # role -> permission
    HAS_ACCESS = "HAS_ACCESS"  # user -> ACL
    ON = "ON"  # ACL -> resource
    WITH_ROLE = "WITH_ROLE"  # ACL -> role


class RoleNode(BaseModel):
    __label__ = "Role"

    id: str = Field(description="Role ID")
    name: str = Field(description="Role name")
    description: str = Field(description="Role description")
    scope: str = Field(description="Resource type this role can be assigned to")


class PermissionNode(BaseModel):
    __label__ = "Permission"

    id: str = Field(description="Permission ID")


class UserNode(BaseModel):
    __label__ = "User"

    id: str = Field(description="User ID")
    username: str = Field(description="Username, replicated from be-authn")
    display_name: str | None = Field(default=None, description="Display name, replicated from be-authn")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Acl creation time")


class ResourceNode(BaseModel):
    __label__ = "Resource"

    resource_id: str = Field(description="Resource ID")
    resource_type: str = Field(description="Resource type")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Acl creation time")


class AclNode(BaseModel):
    __label__ = "Acl"

    id: str = Field(description="Acl ID")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Acl creation time")
    expires_at: datetime | None = Field(default=None, description="Optional grant expiry time")


NODES = (
    UserNode,
    PermissionNode,
    AclNode,
    ResourceNode,
    RoleNode,
    MigrationNode,
)
