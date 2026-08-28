import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Any

from fastapi import FastAPI, APIRouter, Depends

from ristops_be_authn.domain.authn.routers import auth_router
from ristops_be_authn.domain.authn.service import decode_access_token
from ristops_be_authn.domain.user.routers import user_router, member_router
from ristops_be_authn.services.authz import is_authorized
from ristops_be_authn.services.http import authz_client
from ristops_be_authn.settings import BackendServiceSettings
from ristops_lib_be.authn import JwtAuthNMiddleware
from ristops_lib_be.authz.interceptor import AuthZInterceptor
from ristops_lib_core.app.health import health_router
from ristops_lib_core.app.openapi import OpenAPIConfiguration
from ristops_lib_core.auth.authn import PublicRoutesRegistry
from ristops_lib_core.context import RequestContextMiddleware
from ristops_lib_core.exception import (
    GenericExceptionMiddleware, register_exception_handler,
    RequestValidationExceptionHandler, GenericHttpExceptionHandler
)
from ristops_lib_core.http import with_clients
from ristops_lib_core.logging import RequestLoggingMiddleware
from ristops_lib_otel.instrumentation import instrument_app, instrument_clients
from ristops_lib_otel.telemetry import configure_telemetry
from ristops_lib_redis.engine import redis_client
from ristops_lib_sql.engine import sql_session_provider

_logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, Any]:
    await sql_session_provider.configure()
    await redis_client.connect()
    be_settings = BackendServiceSettings.get()
    async with with_clients((authz_client, be_settings.authz_url)):
        _logger.info("Startup complete")
        yield
    await redis_client.disconnect()
    _logger.info("Shutdown complete")


def create_app() -> FastAPI:
    configure_telemetry()
    instrument_clients()

    app = FastAPI(
        title="RistOps AuthN APIs",
        version="1.0",
        summary="REST APIs to interact with RistOps authentication backend",
        lifespan=lifespan,
    )

    # needs user ID and a session in the context
    authz_dependency = AuthZInterceptor(authorizer=is_authorized)
    app.router.dependencies.append(Depends(authz_dependency))

    api_router = APIRouter(prefix="/api")
    api_router.include_router(auth_router)
    api_router.include_router(user_router)
    api_router.include_router(member_router)
    app.include_router(api_router)
    # sits outside /api and is @public, so probes need neither auth nor a policy
    app.include_router(health_router)

    public_registry = PublicRoutesRegistry(app)

    # lazy register public routes
    authz_dependency.register(app)

    register_exception_handler(app, RequestValidationExceptionHandler)
    register_exception_handler(app, GenericHttpExceptionHandler)

    # logs ASAP (only authenticated request) and needs user/request/correlation ID
    app.add_middleware(RequestLoggingMiddleware)
    # sets user ID and JWT in context
    # noinspection PyTypeChecker
    app.add_middleware(JwtAuthNMiddleware, public_registry=public_registry, jwt_decoder=decode_access_token)
    # sets request/correlation ID (from the active span, once instrumented below)
    app.add_middleware(RequestContextMiddleware)
    # wraps everything
    app.add_middleware(GenericExceptionMiddleware)

    openapi_configuration = OpenAPIConfiguration(app, True)
    app.openapi = openapi_configuration

    # wraps the ASGI app itself, outside every middleware above, so a server span is already
    # active by the time RequestContextMiddleware runs
    instrument_app(app)

    return app
