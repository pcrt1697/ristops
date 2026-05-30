import strawberry
from strawberry.tools import merge_types

from ristops_bff_web.domain.auth.resolvers import AuthMutation, AuthQuery

QUERY = merge_types("Query", (AuthQuery,))
MUTATION = merge_types("Mutation", (AuthMutation,))

schema = strawberry.Schema(query=QUERY, mutation=MUTATION)
