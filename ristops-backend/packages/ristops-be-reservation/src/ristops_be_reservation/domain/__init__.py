from ristops_be_reservation.domain.reservation.entities import ReservationEntity
from ristops_be_reservation.domain.schedule.entities import (
    OpeningEntity, OpeningOverrideEntity, ServiceClosingEntity, CapacityOverrideEntity,
)
from ristops_be_reservation.domain.service.entities import ServiceEntity, ServiceOccurrenceEntity
from ristops_be_reservation.domain.venue.entities import VenueEntity, VenueClosingEntity

MODELS = (
    VenueEntity,
    ServiceEntity,
    OpeningEntity,
    OpeningOverrideEntity,
    ServiceClosingEntity,
    CapacityOverrideEntity,
    VenueClosingEntity,
    ServiceOccurrenceEntity,
    ReservationEntity,
)
