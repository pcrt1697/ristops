from ristops_be_reservation.domain.service.entities import (
    ServiceEntity, ServiceOpeningEntity,
    ServiceOpeningOverrideEntity, ServiceClosingEntity, ServiceOccurrenceEntity
)
from ristops_be_reservation.domain.venue.entities import VenueEntity

MODELS = (
    VenueEntity,
    ServiceEntity,
    ServiceOpeningEntity,
    ServiceOpeningOverrideEntity,
    ServiceClosingEntity,
    ServiceOccurrenceEntity,
)
