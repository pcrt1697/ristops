from _contextvars import ContextVar
from asyncio import Lock
from contextlib import asynccontextmanager
from functools import wraps
from typing import Callable, Optional, AsyncGenerator

from neo4j import AsyncTransaction, AsyncDriver, AsyncGraphDatabase

from ristops_lib_neo4j.exception import Neo4TransactionError
from ristops_lib_neo4j.settings import Neo4jSettings

_NEO4J_TRANSACTION_CONTEXT: ContextVar[Optional[AsyncTransaction]] = ContextVar("neo4j_transaction", default=None)


def has_neo4j_transaction() -> bool:
    """Return True if a Neo4j transaction is already open in the current context."""
    return _NEO4J_TRANSACTION_CONTEXT.get() is not None


def with_neo4j_db(func: Callable = None, *, settings: Neo4jSettings = None) -> Callable:
    """Configure the Neo4j provider before running the decorated function.

    Intended for CLI commands. Must be the outermost decorator so the provider
    is ready before ``@neo4j_transactional`` opens a transaction.
    Closes the driver on exit.

    Can be used with or without arguments::

        @with_neo4j_db
        async def seed(): ...

        @with_neo4j_db(settings=test_settings)
        async def seed(): ...
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        async def wrapper(*args, **kwargs):
            await neo4j_transaction_provider.configure(settings)
            try:
                return await f(*args, **kwargs)
            finally:
                await neo4j_transaction_provider.close()
        return wrapper

    if func is not None:
        return decorator(func)
    return decorator


def neo4j_transactional(func: Callable) -> Callable:
    """Open a Neo4j transaction for the duration of the decorated function.

    If a transaction is already open in the current context it is reused, so the
    outermost decorated call controls commit/rollback (join-if-exists semantics).

    Works in any async context: FastAPI route handlers, CLI commands, background tasks.
    Use ``get_neo4j_transaction()`` to access the transaction from within the call.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        if has_neo4j_transaction():
            return await func(*args, **kwargs)
        async with neo4j_transaction_provider.context():
            return await func(*args, **kwargs)

    return wrapper


def get_neo4j_transaction() -> AsyncTransaction:
    """Return the Neo4j transaction for the current context.

    Raises ``Neo4TransactionError`` if no transaction is open.
    Use ``@neo4j_transactional`` to open one.
    """
    transaction = _NEO4J_TRANSACTION_CONTEXT.get()
    if transaction is None:
        raise Neo4TransactionError("No neo4j transaction defined in context")
    return transaction


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
                connection_acquisition_timeout=30,
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
        """Release all connections. Call on app or CLI shutdown."""
        async with self._lock:
            await self.driver.close()


neo4j_transaction_provider = AsyncNeo4jTransactionProvider()
