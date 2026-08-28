from opentelemetry import trace

# opentelemetry-api alone (no SDK, no exporters) is enough to read the current span: with no
# TracerProvider installed it returns INVALID_SPAN, so these helpers are true no-ops when
# ristops-lib-otel's instrumentation is disabled or not wired up for the running service.


def get_trace_id() -> str | None:
    """ Return the active trace ID as lowercase hex, or ``None`` if there is no active span. """
    span_context = trace.get_current_span().get_span_context()
    if not span_context.is_valid:
        return None
    return format(span_context.trace_id, "032x")


def get_span_id() -> str | None:
    """ Return the active span ID as lowercase hex, or ``None`` if there is no active span. """
    span_context = trace.get_current_span().get_span_context()
    if not span_context.is_valid:
        return None
    return format(span_context.span_id, "016x")
