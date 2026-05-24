from contextlib import asynccontextmanager

from fastapi import FastAPI
from starsessions import SessionMiddleware
from starsessions.stores.redis import RedisStore
from strawberry import Schema
from strawberry.fastapi import GraphQLRouter
from strawberry.tools import merge_types

from ristops_bff_web.authn import SessionAuthNMiddleware
from ristops_bff_web.context import ContextExtension
from ristops_bff_web.domain.auth.resolvers import AuthQuery, AuthMutation
from ristops_bff_web.domain.auth.routers import auth_router
from ristops_bff_web.exception import ErrorHandlingExtension
from ristops_bff_web.http import http_service, HttpClient
from ristops_bff_web.logging import ResolverLoggingExtension
from ristops_bff_web.session import get_redis_client
from ristops_bff_web.settings import BackendServiceSettings
from ristops_lib_core.app.openapi import OpenAPIConfiguration
from ristops_lib_core.auth.authn import ClientTokenDecoder
from ristops_lib_core.context import RequestContextMiddleware
from ristops_lib_core.exception import GenericExceptionMiddleware
from ristops_lib_core.logging import RequestLoggingMiddleware


def create_app() -> FastAPI:
    be_settings = BackendServiceSettings.get()
    jwt_decoder = ClientTokenDecoder(be_settings.auth_url)

    redis_client = get_redis_client()
    session_store = RedisStore(connection=redis_client)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        clients = {
            HttpClient.AUTHN: be_settings.authn_url,
        }
        async with http_service(clients):
            try:
                yield
            finally:
                await redis_client.aclose()

    query = merge_types("Query", (AuthQuery,))
    mutation = merge_types("Mutation", (AuthMutation,))

    schema = Schema(
        query=query,
        mutation=mutation,
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
        root_path='/api',
        lifespan=lifespan,
    )
    app.include_router(auth_router)
    app.include_router(graphql_router, prefix="/graphql")

    # logs ASAP (only authenticated request) and needs user/request/correlation ID
    app.add_middleware(RequestLoggingMiddleware)
    # sets user/session ID
    # noinspection PyTypeChecker
    app.add_middleware(SessionAuthNMiddleware, api=app, jwt_decoder=jwt_decoder)
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

    openapi_configuration = OpenAPIConfiguration(app)
    app.openapi = openapi_configuration

    return app
