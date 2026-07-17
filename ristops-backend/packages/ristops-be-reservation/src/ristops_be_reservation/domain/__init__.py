from ristops_be_reservation.domain.schedule.entities import (
    OpeningEntity, OpeningOverrideEntity, ClosingEntity,
)
from ristops_be_reservation.domain.service.entities import ServiceEntity, ServiceOccurrenceEntity
from ristops_be_reservation.domain.venue.entities import VenueEntity

MODELS = (
    VenueEntity,
    ServiceEntity,
    OpeningEntity,
    OpeningOverrideEntity,
    ClosingEntity,
    ServiceOccurrenceEntity,
)
