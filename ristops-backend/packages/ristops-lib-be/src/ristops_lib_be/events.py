from enum import StrEnum

from pydantic import BaseModel, Field

from ristops_lib_core.context import APP_CONTEXT, ContextKey


class ResourceEventType(StrEnum):
    CREATED = "created"
    DELETED = "deleted"
    UPDATED = "updated"


class BaseEvent(BaseModel):
    """Base class for all Redis stream events.

    ``correlation_id`` is captured automatically from the current request
    context at instantiation time, so producers do not need to set it manually.
    """

    correlation_id: str | None = Field(
        default_factory=lambda: APP_CONTEXT.get(ContextKey.CORRELATION_ID),
        description="Trace correlation ID",
    )
