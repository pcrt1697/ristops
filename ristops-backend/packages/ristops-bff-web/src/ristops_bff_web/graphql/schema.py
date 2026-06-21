import strawberry
from strawberry.tools import merge_types

from ristops_bff_web.domain.auth.graphql import AuthMutation, AuthQuery
from ristops_bff_web.domain.venue.graphql import VenueQuery, VenueMutation

QUERY = merge_types("Query", (AuthQuery, VenueQuery,))
MUTATION = merge_types("Mutation", (AuthMutation, VenueMutation,))

schema = strawberry.Schema(query=QUERY, mutation=MUTATION)
