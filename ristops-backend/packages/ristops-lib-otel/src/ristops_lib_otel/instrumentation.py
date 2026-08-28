import logging

from fastapi import FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

from ristops_lib_otel.settings import TelemetrySettings

_logger = logging.getLogger(__name__)

_clients_instrumented = False


def instrument_app(app: FastAPI) -> None:
    """ Instrument ``app``'s ASGI stack: one server span per request.

    A no-op when telemetry is disabled. This wraps the ASGI app itself, which sits *outside*
    every ``add_middleware`` layer — so by the time ``RequestContextMiddleware`` runs, the server
    span it reads from is already active.
    """
    if not TelemetrySettings.get().enabled:
        return
    FastAPIInstrumentor.instrument_app(app, excluded_urls="/health")


def instrument_clients() -> None:
    """ Instrument the process-wide HTTP/Redis/SQL clients used across services.

    Each of these instruments at the class level (a monkeypatch applied once, not per instance),
    so this is called once per process rather than once per client. A no-op when telemetry is
    disabled, and safe to call more than once — repeat calls are ignored.
    """
    global _clients_instrumented
    if not TelemetrySettings.get().enabled or _clients_instrumented:
        return

    HTTPXClientInstrumentor().instrument()
    RedisInstrumentor().instrument()
    SQLAlchemyInstrumentor().instrument()

    _clients_instrumented = True
    _logger.info("Instrumented httpx, redis and SQLAlchemy clients")
