from typing import Literal

from pydantic import BaseModel

from ristops_lib_be.events import ResourceEventType


class AuthZUserEvent(BaseModel):
    operation: Literal[ResourceEventType.created, ResourceEventType.deleted]
    user_id: str
