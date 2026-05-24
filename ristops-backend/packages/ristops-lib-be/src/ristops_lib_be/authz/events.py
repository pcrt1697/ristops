from typing import Literal, Annotated

from pydantic import Field, TypeAdapter

from ristops_lib_be.events import ResourceEventType, BaseEvent
from ristops_lib_core.schema.authz import AuthorizationResource, ResourceType


class AuthZUserEvent(BaseEvent):
    operation: Literal[ResourceEventType.CREATED, ResourceEventType.DELETED]
    user_id: str


class AuthZResourceCreatedEvent(BaseEvent):
    operation: Literal[ResourceEventType.CREATED]
    resources: list[AuthorizationResource] = Field(description="List of resources to create")
    parent_id: str = Field(description="Parent resource id")
    parent_type: ResourceType = Field(description="Parent resource type")


class AuthZResourceDeletedEvent(BaseEvent):
    operation: Literal[ResourceEventType.DELETED]
    resource_id: str = Field(description="ACL resource identifier")
    resource_type: ResourceType = Field(description="ACL resource type")


AuthZResourceEvent = Annotated[
    AuthZResourceCreatedEvent | AuthZResourceDeletedEvent,
    Field(discriminator="operation"),
]
authz_resource_event_adapter = TypeAdapter(AuthZResourceEvent)
