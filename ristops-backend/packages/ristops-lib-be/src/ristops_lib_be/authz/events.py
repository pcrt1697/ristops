from typing import Literal, Annotated

from pydantic import Field, TypeAdapter

from ristops_lib_be.events import LifecycleOperationType, BaseEvent
from ristops_lib_core.schema.authz import AuthorizationResource, ResourceType


class UserLifecycleEvent(BaseEvent):
    operation: Literal[LifecycleOperationType.CREATED, LifecycleOperationType.DELETED]
    user_id: str


class ResourceCreatedLifecycleEvent(BaseEvent):
    operation: Literal[LifecycleOperationType.CREATED]
    resources: list[AuthorizationResource] = Field(description="List of resources to create")
    parent_id: str = Field(description="Parent resource id")
    parent_type: ResourceType = Field(description="Parent resource type")


class ResourceDeletedLifecycleEvent(BaseEvent):
    operation: Literal[LifecycleOperationType.DELETED]
    resource_id: str = Field(description="ACL resource identifier")
    resource_type: ResourceType = Field(description="ACL resource type")


ResourceLifecycleEvent = Annotated[
    ResourceCreatedLifecycleEvent | ResourceDeletedLifecycleEvent,
    Field(discriminator="operation"),
]
resource_lifecycle_event_adapter = TypeAdapter(ResourceLifecycleEvent)
