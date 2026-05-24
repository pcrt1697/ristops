from typing import Literal, Annotated

from pydantic import BaseModel, Field, TypeAdapter

from ristops_lib_be.events import ResourceEventType
from ristops_lib_core.schema.authz import AuthorizationResource, ResourceType


class AuthZUserEvent(BaseModel):
    operation: Literal[ResourceEventType.CREATED, ResourceEventType.DELETED]
    user_id: str


class AuthZResourceCreatedEvent(BaseModel):
    operation: Literal[ResourceEventType.CREATED]
    resources: list[AuthorizationResource] = Field(description="List of resources to create")
    parent_id: str = Field(description="Parent resource id")
    parent_type: ResourceType = Field(description="Parent resource type")


class AuthZResourceDeletedEvent(AuthorizationResource):
    operation: Literal[ResourceEventType.DELETED]


AuthZResourceEvent = Annotated[
    AuthZResourceCreatedEvent | AuthZResourceDeletedEvent,
    Field(discriminator="operation"),
]
authz_resource_event_adapter = TypeAdapter(AuthZResourceEvent)
