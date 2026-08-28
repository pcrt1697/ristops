from enum import StrEnum
from uuid import uuid4

from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from pydantic import BaseModel, Field

from ristops_lib_core.context import APP_CONTEXT, ContextKey
from ristops_lib_core.tracing import get_trace_id

_propagator = TraceContextTextMapPropagator()


class LifecycleOperationType(StrEnum):
    CREATED = "created"
    DELETED = "deleted"
    UPDATED = "updated"


def _current_traceparent() -> str | None:
    """ Return the W3C traceparent header for the active span, or ``None`` without one. """
    carrier: dict[str, str] = {}
    _propagator.inject(carrier)
    return carrier.get("traceparent")


class BaseEvent(BaseModel):
    """Base class for all Redis stream events.

    ``correlation_id`` is the active trace ID when one exists, falling back to the request
    context (for parity with services not yet instrumented) and then a generated UUID.

    ``traceparent`` carries the W3C trace context so a consumer picking the event off the stream
    — potentially long after the producing request finished — can continue the same trace rather
    than start a disconnected one. ``None`` when there is no active span (telemetry disabled),
    in which case it is dropped from the published payload (``exclude_none=True``).
    """

    correlation_id: str = Field(
        default_factory=lambda: get_trace_id() or APP_CONTEXT.get(ContextKey.CORRELATION_ID) or str(uuid4()),
        description="Trace correlation ID",
    )
    traceparent: str | None = Field(
        default_factory=_current_traceparent,
        description="W3C trace context of the span that published this event, if any.",
    )
