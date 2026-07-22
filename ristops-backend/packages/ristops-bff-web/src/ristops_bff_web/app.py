from contextlib import asynccontextmanager

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from starsessions import SessionMiddleware
from starsessions.stores.redis import RedisStore
from strawberry import Schema
from strawberry.fastapi import GraphQLRouter

from ristops_bff_web.authn import SessionAuthNMiddleware
from ristops_bff_web.context import ContextExtension
from ristops_bff_web.domain.auth.routers import auth_router
from ristops_bff_web.exception import ErrorHandlingExtension
from ristops_bff_web.graphql.schema import QUERY, MUTATION
from ristops_bff_web.http import authn_client, authz_client, venue_client, reservation_client
from ristops_bff_web.logging import ResolverLoggingExtension
from ristops_bff_web.session import get_redis_client
from ristops_bff_web.settings import BackendServiceSettings, BffSettings
from ristops_lib_core.app.openapi import OpenAPIConfiguration
from ristops_lib_core.auth.authn import ClientTokenDecoder, PublicRoutesRegistry
from ristops_lib_core.context import RequestContextMiddleware
from ristops_lib_core.exception import (
    GenericExceptionMiddleware, register_exception_handler,
    GenericHttpExceptionHandler, RequestValidationExceptionHandler
)
from ristops_lib_core.http import with_clients
from ristops_lib_core.logging import RequestLoggingMiddleware


def create_app() -> FastAPI:
    be_settings = BackendServiceSettings.get()
    bff_settings = BffSettings.get()
    jwt_decoder = ClientTokenDecoder(be_settings.authn_url)

    redis_client = get_redis_client()
    session_store = RedisStore(connection=redis_client)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        async with with_clients(
                (authn_client, be_settings.authn_url),
                (authz_client, be_settings.authz_url),
                (venue_client, be_settings.venue_url),
                (reservation_client, be_settings.reservation_url),
        ):
            try:
                yield
            finally:
                await redis_client.aclose()

    schema = Schema(
        query=QUERY,
        mutation=MUTATION,
        extensions=[
            ResolverLoggingExtension,
            ErrorHandlingExtension,
            ContextExtension,
        ],
    )
    graphql_router = GraphQLRouter(schema)

    app = FastAPI(
        title="RistOps BFF APIs",
        version="1.0",
        summary="APIs to interact with RistOps BFF",
        lifespan=lifespan,
    )

    register_exception_handler(app, RequestValidationExceptionHandler)
    register_exception_handler(app, GenericHttpExceptionHandler)

    api_router = APIRouter(prefix="/api")
    api_router.include_router(auth_router)
    api_router.include_router(graphql_router, prefix="/graphql")
    app.include_router(api_router)

    public_registry = PublicRoutesRegistry(app)

    # logs ASAP (only authenticated request) and needs user/request/correlation ID
    app.add_middleware(RequestLoggingMiddleware)
    # sets user/session ID
    # noinspection PyTypeChecker
    app.add_middleware(SessionAuthNMiddleware, public_registry=public_registry, jwt_decoder=jwt_decoder)
    # dump session to request object
    # noinspection PyTypeChecker
    app.add_middleware(
        SessionMiddleware,
        store=session_store,
        lifetime=3600,
        rolling=True,
        cookie_same_site="lax",
        cookie_name="session",
        # todo: uncomment and maybe add cookie encryption
        # cookie_https_only=True,
    )
    # sets request/correlation ID
    app.add_middleware(RequestContextMiddleware)
    # wraps everything
    app.add_middleware(GenericExceptionMiddleware)
    # outermost: handles CORS preflight before any auth check
    app.add_middleware(
        CORSMiddleware,
        allow_origins=bff_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    openapi_configuration = OpenAPIConfiguration(app)
    app.openapi = openapi_configuration

    return app
