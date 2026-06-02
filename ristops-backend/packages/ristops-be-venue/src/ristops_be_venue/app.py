import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Any

from fastapi import FastAPI, APIRouter, Depends

from ristops_be_venue.domain.venue.routers import venue_router
from ristops_be_venue.services.authz import is_authorized
from ristops_be_venue.services.http import get_http_clients, http_service
from ristops_be_venue.settings import BackendServiceSettings
from ristops_lib_be.authn import JwtAuthNMiddleware
from ristops_lib_be.authz.interceptor import AuthZInterceptor
from ristops_lib_core.app.openapi import OpenAPIConfiguration
from ristops_lib_core.auth.authn import PublicRoutesRegistry, ClientTokenDecoder
from ristops_lib_core.context import RequestContextMiddleware
from ristops_lib_core.exception import (
    GenericExceptionMiddleware, register_exception_handler,
    RequestValidationExceptionHandler, GenericHttpExceptionHandler
)
from ristops_lib_core.logging import RequestLoggingMiddleware
from ristops_lib_redis.engine import redis_client
from ristops_lib_sql.engine import sql_session_provider

_logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, Any]:
    await sql_session_provider.configure()
    await redis_client.connect()
    clients = get_http_clients()
    async with http_service(clients):
        _logger.info("Startup complete")
        yield
    await redis_client.disconnect()
    _logger.info("Shutdown complete")


def create_app() -> FastAPI:
    settings = BackendServiceSettings.get()
    jwt_decoder = ClientTokenDecoder(settings.authn_url)

    app = FastAPI(
        title="RistOps Venue APIs",
        version="1.0",
        summary="REST APIs to interact with RistOps venue backend",
        lifespan=lifespan,
    )

    # needs venue ID and a session in the context
    authz_dependency = AuthZInterceptor(authorizer=is_authorized)
    app.router.dependencies.append(Depends(authz_dependency))

    api_router = APIRouter(prefix="/api")
    api_router.include_router(venue_router)
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
