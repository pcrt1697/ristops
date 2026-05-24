from strawberry.extensions import SchemaExtension
from strawberry.utils.await_maybe import AsyncIteratorOrIterator

from ristops_lib_core.context import APP_CONTEXT


class BffContextKey:
    GRAPHQL_OPERATION = "gql_operation"
    SESSION_ID = "session_id"
    JWT = "jwt"


class ContextExtension(SchemaExtension):
    """ Dump operation name to APP context."""

    async def on_execute(self) -> AsyncIteratorOrIterator[None]:
        execution_context = self.execution_context
        operation_name = execution_context.operation_name
        APP_CONTEXT.set(BffContextKey.GRAPHQL_OPERATION, operation_name or "anonymous")
        yield
