import asyncio
import contextvars
import uuid

import pytest

from helpers import make_client, make_tracer
from fastapi import FastAPI

from ristops_lib_core.context import (
    APP_CONTEXT, AsyncContext, ContextHeader, ContextKey, RequestContextMiddleware,
)


def test_constants():
    assert ContextHeader.REQUEST_ID == "x-request-id"
    assert ContextHeader.CORRELATION_ID == "x-correlation-id"
    assert {ContextKey.REQUEST_ID, ContextKey.CORRELATION_ID, ContextKey.USER_ID, ContextKey.JWT} == {
        "request_id", "correlation_id", "user_id", "jwt",
    }


class TestAsyncContext:

    def test_app_context_is_the_singleton(self):
        assert AsyncContext() is APP_CONTEXT

    def test_stores_and_returns_a_value(self):
        APP_CONTEXT.set("key", "value")

        assert APP_CONTEXT.get("key") == "value"

    def test_returns_the_default_for_a_missing_key(self):
        assert APP_CONTEXT.get("missing") is None
        assert APP_CONTEXT.get("missing", "fallback") == "fallback"

    def test_returns_the_default_when_nothing_was_ever_set(self):
        assert contextvars.Context().run(APP_CONTEXT.get, "key", "fallback") == "fallback"

    def test_setting_a_key_overwrites_it_and_keeps_the_others(self):
        APP_CONTEXT.set("a", 1)
        APP_CONTEXT.set("b", 2)
        APP_CONTEXT.set("a", 3)

        assert (APP_CONTEXT.get("a"), APP_CONTEXT.get("b")) == (3, 2)

    def test_get_or_throw_returns_a_value(self):
        APP_CONTEXT.set("key", "value")

        assert APP_CONTEXT.get_or_throw("key") == "value"

    def test_get_or_throw_raises_for_a_missing_key(self):
        with pytest.raises(KeyError, match="key"):
            APP_CONTEXT.get_or_throw("key")

    def test_reset_clears_every_key(self):
        APP_CONTEXT.set("key", "value")

        APP_CONTEXT.reset()

        assert APP_CONTEXT.get("key") is None

    @pytest.mark.anyio
    async def test_a_child_task_inherits_but_cannot_change_the_parent(self):
        APP_CONTEXT.set("key", "parent")

        async def child() -> tuple[str, str]:
            inherited = APP_CONTEXT.get("key")
            APP_CONTEXT.set("key", "child")
            return inherited, APP_CONTEXT.get("key")

        assert await asyncio.create_task(child()) == ("parent", "child")
        assert APP_CONTEXT.get("key") == "parent"

    @pytest.mark.anyio
    async def test_concurrent_tasks_do_not_see_each_other(self):
        async def run(name: str) -> str:
            APP_CONTEXT.set("user", name)
            await asyncio.sleep(0.01)
            return APP_CONTEXT.get("user")

        results = await asyncio.gather(*(asyncio.create_task(run(f"user-{i}")) for i in range(10)))

        assert results == [f"user-{i}" for i in range(10)]


class TestRequestContextMiddleware:

    @staticmethod
    def build_app() -> FastAPI:
        app = FastAPI()
        app.add_middleware(RequestContextMiddleware)

        @app.get("/ids")
        async def ids() -> dict:
            return {
                "request_id": APP_CONTEXT.get(ContextKey.REQUEST_ID),
                "correlation_id": APP_CONTEXT.get(ContextKey.CORRELATION_ID),
            }

        return app

    @pytest.mark.anyio
    async def test_generates_uuids_when_there_is_no_active_span(self):
        async with make_client(self.build_app()) as client:
            response = await client.get("/ids")

        body = response.json()
        assert uuid.UUID(body["request_id"]) and uuid.UUID(body["correlation_id"])
        assert response.headers[ContextHeader.REQUEST_ID] == body["request_id"]
        assert response.headers[ContextHeader.CORRELATION_ID] == body["correlation_id"]

    @pytest.mark.anyio
    async def test_every_request_gets_new_ids(self):
        async with make_client(self.build_app()) as client:
            first = (await client.get("/ids")).json()
            second = (await client.get("/ids")).json()

        assert first["request_id"] != second["request_id"]
        assert first["correlation_id"] != second["correlation_id"]

    @pytest.mark.anyio
    async def test_uses_the_active_span_ids(self):
        with make_tracer().start_as_current_span("request") as span:
            async with make_client(self.build_app()) as client:
                response = await client.get("/ids")
            context = span.get_span_context()

        body = response.json()
        assert body["request_id"] == format(context.span_id, "016x")
        assert body["correlation_id"] == format(context.trace_id, "032x")
        assert response.headers[ContextHeader.CORRELATION_ID] == body["correlation_id"]
