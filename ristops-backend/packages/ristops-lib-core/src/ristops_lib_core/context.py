import uuid
from contextvars import ContextVar
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from ristops_lib_core.utils import Singleton


class ContextHeader:
    REQUEST_ID = "x-request-id"
    CORRELATION_ID = "x-correlation-id"


class ContextKey:
    REQUEST_ID = "request_id"
    CORRELATION_ID = "correlation_id"
    USER_ID = "user_id"
    JWT = "jwt"


class AsyncContext(metaclass=Singleton):
    """Request-scoped key/value store backed by a ``ContextVar``.

    Each call to ``set`` replaces the stored dict with a new immutable snapshot,
    so child tasks spawned via ``asyncio.create_task`` inherit the context at the
    moment of creation and cannot affect the parent's context (and vice versa).

    Accessed via the module-level ``APP_CONTEXT`` singleton.
    """

    _store: ContextVar[dict] = ContextVar('request_store', default=None)

    def set(self, key: str, value: Any) -> None:
        """Store ``value`` under ``key`` in the current task's context.

        Creates a new dict snapshot on every call, ensuring that parent and child
        tasks do not share mutable state even when they hold the same ContextVar.
        """
        store = self._store.get() or {}
        self._store.set({**store, key: value})

    def get(self, key: str, default: Any = None) -> Any:
        """Return the value stored under ``key``, or ``default`` if not set."""
        store = self._store.get()
        if store is None:
            return default
        return store.get(key, default)

    def get_or_throw(self, key: str) -> Any:
        """Return the value stored under ``key``, or raise ``KeyError`` if not set."""
        value = self.get(key)
        if value is None:
            raise KeyError(f"Context value not set {key}")
        return value

    def reset(self) -> None:
        """Clear all values from the current task's context store."""
        self._store.set({})


class RequestContextMiddleware(BaseHTTPMiddleware):
    """ Middleware used to dump request context to context vars. """

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        correlation_id = request.headers.get(ContextHeader.CORRELATION_ID, str(uuid.uuid4()))
        APP_CONTEXT.set(ContextKey.REQUEST_ID, request_id)
        APP_CONTEXT.set(ContextKey.CORRELATION_ID, correlation_id)
        response = await call_next(request)
        response.headers[ContextHeader.REQUEST_ID] = request_id
        response.headers[ContextHeader.CORRELATION_ID] = correlation_id
        return response


APP_CONTEXT = AsyncContext()
