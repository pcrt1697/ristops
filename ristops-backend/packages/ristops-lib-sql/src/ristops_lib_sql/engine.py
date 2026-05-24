import logging
from _contextvars import ContextVar
from asyncio import Lock
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Callable, Any

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from starlette.middleware.base import RequestResponseEndpoint, BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from ristops_lib_core.app.routes import RouteAttributeRegistry
from ristops_lib_sql.exception import SqlSessionError
from ristops_lib_sql.settings import DatabaseSettings

_logger = logging.getLogger(__name__)

_SQL_SESSION_CONTEXT: ContextVar[AsyncSession | None] = ContextVar('sql_session', default=None)
IS_SQL_TRANSACTIONAL = "_is_sql_transactional"


def sql_transactional(route_func: Callable) -> Callable:
    """ Decorator to add a session variable to the route function. """
    setattr(route_func, IS_SQL_TRANSACTIONAL, True)
    return route_func


class AsyncSqlSessionProvider:

    def __init__(self):
        self._session_factory: async_sessionmaker[AsyncSession | Any] | None = None
        self._lock = Lock()

    async def configure(self, settings: DatabaseSettings = None):
        async with self._lock:
            if self._session_factory is not None:
                raise SqlSessionError("SQL session factory already configured")
            _settings = DatabaseSettings.get() if settings is None else settings
            engine = create_async_engine(
                _settings.get_database_url(),
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,  # verify connection is alive before using it
                echo=_settings.debug,  # set True to log SQL queries (debug only)
            )
            self._session_factory = async_sessionmaker(
                bind=engine,
                class_=AsyncSession,
                expire_on_commit=False,  # don't expire objects after commit — safer in async context
            )

    async def __call__(self) -> AsyncGenerator[AsyncSession, None]:
        """ Callable can be used as FastAPI dependency """
        async with self._provide() as session:
            yield session

    @asynccontextmanager
    async def _provide(self) -> AsyncGenerator[AsyncSession, None]:
        if self._session_factory is None:
            raise SqlSessionError("SQL session provider not initialized")

        async with self._session_factory() as session:
            token = _SQL_SESSION_CONTEXT.set(session)
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                _SQL_SESSION_CONTEXT.reset(token)

    @asynccontextmanager
    async def context(self) -> AsyncGenerator[AsyncSession, None]:
        """ Use as an async context manager outside FastAPI dependency injection. """
        async with self._provide() as session:
            yield session


class SqlSessionMiddleware(BaseHTTPMiddleware):
    """ Middleware used to dump a SQLAlchemy session to context vars. """

    def __init__(self, app: ASGIApp, api: FastAPI, session_provider: AsyncSqlSessionProvider) -> None:
        super().__init__(app)
        self._session_provider = session_provider
        self._routes_registry = RouteAttributeRegistry[bool](api, IS_SQL_TRANSACTIONAL)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if not self._need_session(request):
            return await call_next(request)
        async with self._session_provider.context():
            return await call_next(request)

    def _need_session(self, request: Request):
        return self._routes_registry.get(request.scope, False)


def get_sql_session() -> AsyncSession:
    session = _SQL_SESSION_CONTEXT.get()
    if session is None:
        raise SqlSessionError("No SQL session defined in context")
    return session


sql_session_provider = AsyncSqlSessionProvider()
