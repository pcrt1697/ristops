from typing import Literal

from pydantic import Field

from ristops_be_reservation.domain.venue.models import VenueStatus
from ristops_lib_be.events import BaseEvent, LifecycleOperationType


class VenueLifecycleEvent(BaseEvent):
    """Local, narrow view of be-venue's venue lifecycle event: only the fields this service needs."""

    operation: Literal[
        LifecycleOperationType.CREATED,
        LifecycleOperationType.UPDATED,
    ]
    id: str = Field(description="Venue identifier")
    timezone: str = Field(description="IANA timezone name of the venue")
    status: VenueStatus = Field(description="Current lifecycle status of the venue")
