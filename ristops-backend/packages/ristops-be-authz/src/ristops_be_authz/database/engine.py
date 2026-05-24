from _contextvars import ContextVar
from asyncio import Lock
from contextlib import asynccontextmanager
from typing import Callable, Optional, AsyncGenerator

from fastapi import FastAPI
from neo4j import AsyncTransaction, AsyncDriver, AsyncGraphDatabase
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from ristops_be_authz.database.exception import Neo4TransactionError
from ristops_be_authz.settings import Neo4jSettings
from ristops_lib_core.app.routes import RouteAttributeRegistry

_NEO4J_TRANSACTION_CONTEXT: ContextVar[Optional[AsyncTransaction]] = ContextVar("neo4j_transaction", default=None)
IS_NEO4J_TRANSACTIONAL = "is_neo4j_transactional"


def neo4j_transactional(route_func: Callable) -> Callable:
    setattr(route_func, IS_NEO4J_TRANSACTIONAL, True)
    return route_func


def get_neo4j_transaction() -> AsyncTransaction:
    session = _NEO4J_TRANSACTION_CONTEXT.get()
    if session is None:
        raise Neo4TransactionError("No neo4j transaction defined in context")
    return session


class AsyncNeo4jTransactionProvider:

    def __init__(self):
        self._driver: AsyncDriver | None = None
        self._lock = Lock()

    @property
    def driver(self) -> AsyncDriver:
        if self._driver is None:
            raise Neo4TransactionError("Neo4j driver not configured")
        return self._driver

    async def configure(self, settings: Neo4jSettings = None):
        async with self._lock:
            if self._driver is not None:
                raise Neo4TransactionError("Neo4j driver already configured")
            _settings = Neo4jSettings.get() if settings is None else settings
            self._driver: AsyncDriver = AsyncGraphDatabase.driver(
                _settings.get_url(),
                auth=(_settings.user, _settings.pwd),
                max_connection_pool_size=30,
                connection_acquisition_timeout=30,  # how long to wait for a free connection
            )

    async def __call__(self) -> AsyncGenerator[AsyncTransaction, None]:
        """Callable can be used as FastAPI dependency."""
        async with self._provide() as transaction:
            yield transaction

    @asynccontextmanager
    async def _provide(self) -> AsyncGenerator[AsyncTransaction, None]:
        async with self.driver.session(database="neo4j") as session:
            async with await session.begin_transaction() as transaction:
                token = _NEO4J_TRANSACTION_CONTEXT.set(transaction)
                try:
                    yield transaction
                    await transaction.commit()
                except Exception:
                    await transaction.rollback()
                    raise
                finally:
                    _NEO4J_TRANSACTION_CONTEXT.reset(token)

    @asynccontextmanager
    async def context(self) -> AsyncGenerator[AsyncTransaction, None]:
        """Use as an async context manager outside FastAPI dependency injection."""
        async with self._provide() as transaction:
            yield transaction

    async def close(self) -> None:
        """Call on app shutdown to release all connections."""
        async with self._lock:
            await self.driver.close()


class Neo4jTransactionMiddleware(BaseHTTPMiddleware):

    def __init__(self, app: ASGIApp, api: FastAPI, transaction_provider: AsyncNeo4jTransactionProvider) -> None:
        super().__init__(app)
        self._transaction_provider = transaction_provider
        self._routes_registry = RouteAttributeRegistry[bool](api, IS_NEO4J_TRANSACTIONAL)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if not self._routes_registry.get(request.scope, False):
            return await call_next(request)
        async with self._transaction_provider.context():
            return await call_next(request)


neo4j_transaction_provider = AsyncNeo4jTransactionProvider()
