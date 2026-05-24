import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends

from ristops_be_authz.database.engine import Neo4jTransactionMiddleware, neo4j_transaction_provider
from ristops_be_authz.domain.acl.routers import acl_router
from ristops_be_authz.domain.acl.service import check_acl_authorization
from ristops_be_authz.domain.resource.service import on_resource_event
from ristops_be_authz.domain.user.service import on_user_event
from ristops_be_authz.settings import BackendServiceSettings, RedisUserConsumerSettings, RedisResourceConsumerSettings
from ristops_lib_be.authn import JwtAuthNMiddleware
from ristops_lib_be.authz.interceptor import AuthZInterceptor
from ristops_lib_core.app.openapi import OpenAPIConfiguration
from ristops_lib_core.auth.authn import ClientTokenDecoder, PublicRoutesRegistry
from ristops_lib_core.context import RequestContextMiddleware
from ristops_lib_core.exception import (
    GenericExceptionMiddleware, register_exception_handler,
    RequestValidationExceptionHandler, GenericHttpExceptionHandler
)
from ristops_lib_core.logging import RequestLoggingMiddleware
from ristops_lib_redis.engine import redis_client, RedisStreamConsumer

_logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await neo4j_transaction_provider.configure()

    await redis_client.connect()
    consumer = RedisStreamConsumer.create_composite(
        redis_client,
        (RedisUserConsumerSettings.get(), on_user_event),
        (RedisResourceConsumerSettings.get(), on_resource_event)
    )
    await consumer.start()

    _logger.info("Startup complete")
    yield

    await consumer.stop()
    await redis_client.disconnect()
    await neo4j_transaction_provider.close()

    _logger.info("Shutdown complete")


def create_app() -> FastAPI:
    settings = BackendServiceSettings.get()
    jwt_decoder = ClientTokenDecoder(settings.authn_url)

    app = FastAPI(
        title="RistOps auth APIs",
        version="1.0",
        summary="REST APIs to interact with RistOps auth backend",
        root_path='/api',
        lifespan=lifespan,
    )

    # needs user ID and a session in the context
    authz_dependency = AuthZInterceptor(authorizer=check_acl_authorization)
    app.router.dependencies.append(Depends(authz_dependency))

    app.include_router(acl_router)

    public_registry = PublicRoutesRegistry(app)

    # lazy register public routes
    authz_dependency.register(app)

    register_exception_handler(app, RequestValidationExceptionHandler)
    register_exception_handler(app, GenericHttpExceptionHandler)

    # opens neo4j transaction as late as possible
    # noinspection PyTypeChecker
    app.add_middleware(Neo4jTransactionMiddleware, api=app, transaction_provider=neo4j_transaction_provider)
    # logs ASAP (only authenticated request) and needs user/request/correlation ID
    app.add_middleware(RequestLoggingMiddleware)
    # sets user ID and JWT in context
    # noinspection PyTypeChecker
    app.add_middleware(JwtAuthNMiddleware, public_registry=public_registry, jwt_decoder=jwt_decoder)
    # sets request/correlation ID
    app.add_middleware(RequestContextMiddleware)
    # wraps everything
    app.add_middleware(GenericExceptionMiddleware)

    openapi_configuration = OpenAPIConfiguration(app)
    app.openapi = openapi_configuration

    return app
