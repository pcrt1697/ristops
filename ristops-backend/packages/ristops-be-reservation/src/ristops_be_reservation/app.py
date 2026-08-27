import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Any

from fastapi import FastAPI, APIRouter, Depends

from ristops_be_reservation.domain.reservation.routers import reservation_router
from ristops_be_reservation.domain.schedule.routers import schedule_router
from ristops_be_reservation.domain.service.routers import service_router
from ristops_be_reservation.domain.venue.routers import venue_closing_router
from ristops_be_reservation.domain.venue.service import on_venue_event
from ristops_be_reservation.services.authz import is_authorized
from ristops_be_reservation.services.http import authn_client, authz_client
from ristops_be_reservation.settings import BackendServiceSettings, VenueLifecycleConsumerSettings
from ristops_lib_be.authn import JwtAuthNMiddleware
from ristops_lib_be.authz.interceptor import AuthZInterceptor
from ristops_lib_core.app.openapi import OpenAPIConfiguration
from ristops_lib_core.auth.authn import PublicRoutesRegistry, ClientTokenDecoder
from ristops_lib_core.context import RequestContextMiddleware
from ristops_lib_core.exception import (
    GenericExceptionMiddleware, register_exception_handler,
    RequestValidationExceptionHandler, GenericHttpExceptionHandler
)
from ristops_lib_core.http import with_clients
from ristops_lib_core.logging import RequestLoggingMiddleware
from ristops_lib_redis.engine import redis_client, RedisStreamConsumer
from ristops_lib_sql.engine import sql_session_provider

_logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, Any]:
    await sql_session_provider.configure()
    await redis_client.connect()

    consumer = RedisStreamConsumer.create_composite(
        redis_client,
        (VenueLifecycleConsumerSettings.get(), on_venue_event)
    )
    await consumer.start()

    be_settings = BackendServiceSettings.get()
    async with with_clients(
            (authn_client, be_settings.authn_url),
            (authz_client, be_settings.authz_url),
    ):
        _logger.info("Startup complete")
        yield
    await consumer.stop()
    await redis_client.disconnect()
    _logger.info("Shutdown complete")


def create_app() -> FastAPI:
    settings = BackendServiceSettings.get()
    jwt_decoder = ClientTokenDecoder(settings.authn_url)

    app = FastAPI(
        title="RistOps Reservation APIs",
        version="1.0",
        summary="REST APIs to interact with RistOps reservation backend",
        lifespan=lifespan,
    )

    # needs venue ID and a session in the context
    authz_dependency = AuthZInterceptor(authorizer=is_authorized)
    app.router.dependencies.append(Depends(authz_dependency))

    api_router = APIRouter(prefix="/api")
    api_router.include_router(service_router)
    api_router.include_router(schedule_router)
    api_router.include_router(venue_closing_router)
    api_router.include_router(reservation_router)
    app.include_router(api_router)

    public_registry = PublicRoutesRegistry(app)

    # lazy register public routes
    authz_dependency.register(app)

    register_exception_handler(app, RequestValidationExceptionHandler)
    register_exception_handler(app, GenericHttpExceptionHandler)

    # logs ASAP (only authenticated request) and needs venue/request/correlation ID
    app.add_middleware(RequestLoggingMiddleware)
    # sets venue ID and JWT in context
    # noinspection PyTypeChecker
    app.add_middleware(JwtAuthNMiddleware, public_registry=public_registry, jwt_decoder=jwt_decoder)
    # sets request/correlation ID
    app.add_middleware(RequestContextMiddleware)
    # wraps everything
    app.add_middleware(GenericExceptionMiddleware)

    openapi_configuration = OpenAPIConfiguration(app, True)
    app.openapi = openapi_configuration

    return app
