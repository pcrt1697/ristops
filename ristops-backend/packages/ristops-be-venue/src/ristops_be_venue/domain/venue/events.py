from typing import Literal

from pydantic import Field

from ristops_lib_be.events import BaseEvent, LifecycleOperationType


class VenueLifecycleEvent(BaseEvent):
    """Venue lifecycle event, published by be-venue on the ``venue:lifecycle`` stream."""

    operation: Literal[
        LifecycleOperationType.CREATED,
        LifecycleOperationType.UPDATED,
        LifecycleOperationType.DELETED,
    ]
    id: str = Field(description="Venue identifier")
    timezone: str | None = Field(default=None, description="IANA timezone name of the venue")
    active: bool = Field(description="Whether the venue is active")
