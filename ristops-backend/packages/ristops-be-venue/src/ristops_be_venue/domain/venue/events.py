from typing import Literal

from pydantic import Field

from ristops_be_venue.domain.models import VenueStatus
from ristops_lib_be.events import BaseEvent, LifecycleOperationType


class VenueLifecycleEvent(BaseEvent):
    """Venue lifecycle event, published by be-venue on the ``venue:lifecycle`` stream."""

    operation: Literal[
        LifecycleOperationType.CREATED,
        LifecycleOperationType.UPDATED,
    ]
    id: str = Field(description="Venue identifier")
    timezone: str = Field(description="IANA timezone name of the venue")
    status: VenueStatus = Field(description="Current lifecycle status of the venue")
