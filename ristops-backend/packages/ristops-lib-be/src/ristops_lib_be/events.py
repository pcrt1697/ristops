from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field

from ristops_lib_core.context import APP_CONTEXT, ContextKey


class LifecycleOperationType(StrEnum):
    CREATED = "created"
    DELETED = "deleted"
    UPDATED = "updated"


class BaseEvent(BaseModel):
    """Base class for all Redis stream events.

    ``correlation_id`` is captured automatically from the current request
    context at instantiation time. Falls back to a generated UUID when no
    request context is present (e.g. CLI commands, seeding scripts).
    """

    correlation_id: str = Field(
        default_factory=lambda: APP_CONTEXT.get(ContextKey.CORRELATION_ID) or str(uuid4()),
        description="Trace correlation ID",
    )
