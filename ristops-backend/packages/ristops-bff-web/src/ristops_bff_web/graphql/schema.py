import strawberry
from strawberry.tools import merge_types

from ristops_bff_web.domain.auth.graphql import AuthMutation, AuthQuery
from ristops_bff_web.domain.reservation.graphql import ReservationMutation, ReservationQuery
from ristops_bff_web.domain.schedule.graphql import ScheduleMutation, ScheduleQuery
from ristops_bff_web.domain.service.graphql import ServiceQuery, ServiceMutation
from ristops_bff_web.domain.venue.graphql import VenueQuery, VenueMutation

QUERY = merge_types("Query", (AuthQuery, VenueQuery, ServiceQuery, ScheduleQuery, ReservationQuery,))
MUTATION = merge_types(
    "Mutation", (AuthMutation, VenueMutation, ServiceMutation, ScheduleMutation, ReservationMutation,)
)

schema = strawberry.Schema(query=QUERY, mutation=MUTATION)
