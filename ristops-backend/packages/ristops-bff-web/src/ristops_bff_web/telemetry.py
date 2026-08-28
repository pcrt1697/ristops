from opentelemetry import trace
from strawberry.extensions import SchemaExtension
from strawberry.utils.await_maybe import AsyncIteratorOrIterator

# strawberry-graphql 0.314 ships no built-in OpenTelemetry extension (later versions do), so this
# is the minimal equivalent: one span per GraphQL operation, nested inside the FastAPI server span
# that ristops_lib_otel.instrument_app installs for the /api/graphql route.
_tracer = trace.get_tracer(__name__)


class GraphQLOperationSpanExtension(SchemaExtension):
    """ Wrap each GraphQL operation execution in its own span. """

    async def on_execute(self) -> AsyncIteratorOrIterator[None]:
        operation_name = self.execution_context.operation_name or "anonymous"
        with _tracer.start_as_current_span(f"graphql.execute:{operation_name}"):
            yield
