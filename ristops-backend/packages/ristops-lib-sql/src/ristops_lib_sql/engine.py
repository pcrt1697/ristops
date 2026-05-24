import logging
from _contextvars import ContextVar
from asyncio import Lock
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from functools import wraps
from typing import Callable, Any

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from ristops_lib_sql.exception import SqlSessionError
from ristops_lib_sql.settings import DatabaseSettings

_logger = logging.getLogger(__name__)

_SQL_SESSION_CONTEXT: ContextVar[AsyncSession | None] = ContextVar('sql_session', default=None)


def has_sql_session() -> bool:
    """Return True if a SQL session is already open in the current context."""
    return _SQL_SESSION_CONTEXT.get() is not None


def with_sql_db(func: Callable = None, *, settings: DatabaseSettings = None) -> Callable:
    """Configure the SQL provider before running the decorated function.

    Intended for CLI commands. Must be the outermost decorator so the provider
    is ready before ``@sql_transactional`` opens a session.

    Can be used with or without arguments::

        @with_sql_db
        async def seed(): ...

        @with_sql_db(settings=test_settings)
        async def seed(): ...
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        async def wrapper(*args, **kwargs):
            await sql_session_provider.configure(settings)
            return await f(*args, **kwargs)
        return wrapper

    if func is not None:
        # used as @with_sql_db without parentheses
        return decorator(func)
    # used as @with_sql_db(settings=...) — return the decorator
    return decorator


def sql_transactional(func: Callable) -> Callable:
    """Open a SQL session for the duration of the decorated function.

    If a session is already open in the current context it is reused, so the
    outermost decorated call controls commit/rollback (join-if-exists semantics).

    Works in any async context: FastAPI route handlers, CLI commands, background tasks.
    Use ``get_sql_session()`` to access the session from within the call.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        if has_sql_session():
            return await func(*args, **kwargs)
        async with sql_session_provider.context():
            return await func(*args, **kwargs)
    return wrapper


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


def get_sql_session() -> AsyncSession:
    session = _SQL_SESSION_CONTEXT.get()
    if session is None:
        raise SqlSessionError("No SQL session defined in context")
    return session


sql_session_provider = AsyncSqlSessionProvider()
