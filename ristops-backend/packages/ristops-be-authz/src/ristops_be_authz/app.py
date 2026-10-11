import logging
from collections.abc import Sequence
from contextlib import asynccontextmanager

from fastapi import FastAPI, APIRouter, Depends, params
from starlette.types import Lifespan

from ristops_be_authz.domain.acl.service import check_acl_authorization
from ristops_be_authz.domain.permission.routers import permissions_router
from ristops_be_authz.domain.resource.routers import resource_router
from ristops_be_authz.domain.resource.service import on_resource_event
from ristops_be_authz.domain.role.routers import roles_router
from ristops_be_authz.domain.user.routers import user_router
from ristops_be_authz.domain.user.service import on_user_event
from ristops_be_authz.settings import (
    BackendServiceSettings, UserLifecycleConsumerSettings,
    ResourceLifecycleConsumerSettings
)
from ristops_lib_be.authn import JwtAuthNMiddleware
from ristops_lib_be.authz.interceptor import AuthZInterceptor
from ristops_lib_core.app.health import health_router
from ristops_lib_core.app.openapi import OpenAPIConfiguration
from ristops_lib_core.auth.authn import ClientTokenDecoder, PublicRoutesRegistry
from ristops_lib_core.context import RequestContextMiddleware
from ristops_lib_core.exception import (
    GenericExceptionMiddleware, register_exception_handler,
    RequestValidationExceptionHandler, GenericHttpExceptionHandler
)
from ristops_lib_core.logging import RequestLoggingMiddleware
from ristops_lib_neo4j.engine import neo4j_transaction_provider
from ristops_lib_otel.instrumentation import instrument_app, instrument_clients
from ristops_lib_otel.telemetry import configure_telemetry
from ristops_lib_redis.engine import redis_client, RedisStreamConsumer

_logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await neo4j_transaction_provider.configure()

    await redis_client.connect()
    consumer = RedisStreamConsumer.create_composite(
        redis_client,
        (UserLifecycleConsumerSettings.get(), on_user_event),
        (ResourceLifecycleConsumerSettings.get(), on_resource_event)
    )
    await consumer.start()

    _logger.info("Startup complete")
    yield

    await consumer.stop()
    await redis_client.disconnect()
    await neo4j_transaction_provider.close()

    _logger.info("Shutdown complete")


def build_api(lifespan: Lifespan[FastAPI] | None = None, dependencies: Sequence[params.Depends] = ()) -> FastAPI:
    """Build the API definition: metadata, routes and OpenAPI configuration.

    Reads no settings and performs no I/O, so the OpenAPI schema can be exported without an environment.
    `dependencies` are set at construction because FastAPI copies router dependencies into each route when the
    route is included.
    """
    app = FastAPI(
        title="RistOps auth APIs",
        version="1.0",
        summary="REST APIs to interact with RistOps auth backend",
        lifespan=lifespan,
        dependencies=dependencies,
    )

    api_router = APIRouter(prefix="/api")
    api_router.include_router(resource_router)
    api_router.include_router(user_router)
    api_router.include_router(roles_router)
    api_router.include_router(permissions_router)
    app.include_router(api_router)
    # sits outside /api and is @public, so probes need neither auth nor a policy
    app.include_router(health_router)

    app.openapi = OpenAPIConfiguration(app)
    return app


def create_app() -> FastAPI:
    """Build the runnable app: the API definition plus telemetry, settings, authN/authZ and middleware."""
    configure_telemetry()
    instrument_clients()

    settings = BackendServiceSettings.get()
    jwt_decoder = ClientTokenDecoder(settings.authn_url)

    # needs user ID and a session in the context
    authz_dependency = AuthZInterceptor(authorizer=check_acl_authorization)
    app = build_api(lifespan, [Depends(authz_dependency)])

    public_registry = PublicRoutesRegistry(app)

    # lazy register public routes
    authz_dependency.register(app)

    register_exception_handler(app, RequestValidationExceptionHandler)
    register_exception_handler(app, GenericHttpExceptionHandler)

    # logs ASAP (only authenticated request) and needs user/request/correlation ID
    app.add_middleware(RequestLoggingMiddleware)
    # sets user ID and JWT in context
    # noinspection PyTypeChecker
    app.add_middleware(JwtAuthNMiddleware, public_registry=public_registry, jwt_decoder=jwt_decoder)
    # sets request/correlation ID (from the active span, once instrumented below)
    app.add_middleware(RequestContextMiddleware)
    # wraps everything
    app.add_middleware(GenericExceptionMiddleware)

    # wraps the ASGI app itself, outside every middleware above, so a server span is already
    # active by the time RequestContextMiddleware runs
    instrument_app(app)

    return app
