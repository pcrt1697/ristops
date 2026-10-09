from ristops_be_reservation.domain.reservation.entities import ReservationEntity
from ristops_be_reservation.domain.service.entities import (
    ClosingEntity, ClosingServiceEntity, OpeningEntity, ServiceEntity,
)
from ristops_be_reservation.domain.venue.entities import VenueEntity

MODELS = (
    VenueEntity,
    ServiceEntity,
    OpeningEntity,
    ClosingEntity,
    ClosingServiceEntity,
    ReservationEntity,
)
