import functools
from typing import Callable

from opentelemetry import trace

# auto-instrumentation only sees library boundaries (a route, a query, a cache call) — it has no
# idea a particular query is "the schedule conflict check" versus any other SELECT. This decorator
# is the escape hatch for the handful of domain operations worth naming as their own span.
_tracer = trace.get_tracer("ristops.domain")


def traced(name: str | None = None) -> Callable:
    """ Wrap an async function in its own span, named after it unless ``name`` is given.

    A no-op when telemetry is disabled, exactly like the auto-instrumentors: with no
    TracerProvider installed, ``start_as_current_span`` is a cheap no-op context manager.
    """
    def decorator(func: Callable) -> Callable:
        span_name = name or func.__qualname__

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            with _tracer.start_as_current_span(span_name):
                return await func(*args, **kwargs)

        return wrapper

    return decorator
