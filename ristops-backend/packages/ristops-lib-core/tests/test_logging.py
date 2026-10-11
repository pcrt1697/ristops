import json
import logging

import pytest
from fastapi import FastAPI
from pydantic import ValidationError
from uvicorn.config import LOGGING_CONFIG

from helpers import make_client, make_tracer
from ristops_lib_core.context import APP_CONTEXT, ContextKey
from ristops_lib_core.logging import (
    ContextFilter, LogFormatter, LogSettings, RequestContextFilter, RequestLoggingMiddleware, configure_logging,
    remove_handlers, uvicorn_logging_config,
)
from ristops_lib_core.settings import BaseServiceSettings


@pytest.fixture(autouse=True)
def fresh_settings_cache():
    BaseServiceSettings.get.cache_clear()
    yield
    BaseServiceSettings.get.cache_clear()


def make_record(message: str = "hello") -> logging.LogRecord:
    return logging.LogRecord("demo", logging.INFO, __file__, 10, message, None, None)


class TestLogSettings:

    def test_defaults(self):
        settings = LogSettings()

        assert settings.level == logging.INFO
        assert settings.filter == "ristops_lib_core.logging:RequestContextFilter"
        assert settings.formatter == "ristops_lib_core.logging:LogFormatter"

    def test_reads_the_environment_with_the_log_prefix(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("RISTOPS_LOG_LEVEL", "debug")
        monkeypatch.setenv("RISTOPS_LOG_FORMATTER", "logging:Formatter")

        settings = LogSettings()

        assert settings.level == logging.DEBUG
        assert settings.formatter == "logging:Formatter"

    @pytest.mark.parametrize("value, expected", [
        (logging.ERROR, logging.ERROR),
        (5, 5),
        ("INFO", logging.INFO),
        ("debug", logging.DEBUG),
        ("Warning", logging.WARNING),
    ])
    def test_level_accepts_numbers_and_names(self, value, expected: int):
        assert LogSettings(level=value).level == expected

    @pytest.mark.parametrize("value", ["LOUD", "", "infoo"])
    def test_level_rejects_unknown_names(self, value: str):
        with pytest.raises(ValidationError, match="Invalid log level"):
            LogSettings(level=value)

    @pytest.mark.xfail(strict=True, raises=ValidationError, reason="a numeric string, like any env var, is rejected")
    def test_level_accepts_a_number_given_as_a_string(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("RISTOPS_LOG_LEVEL", "10")

        assert LogSettings().level == 10


class TestLogFormatter:

    def test_formats_the_line_with_context_and_trace_id(self):
        record = make_record("did the thing")
        record.trace_id, record.extras = "abc123", '{"user_id": "u-1"}'

        line = LogFormatter().format(record)

        assert "[INFO    ]" in line
        assert "[trace_id=abc123]" in line
        assert '[{"user_id": "u-1"}]' in line
        assert "- did the thing" in line


class TestContextFilter:

    def test_attaches_the_requested_context_keys(self):
        APP_CONTEXT.set("a", 1)
        APP_CONTEXT.set("b", "two")
        record = make_record()

        assert ContextFilter("a", "b").filter(record) is True

        assert json.loads(record.extras) == {"a": 1, "b": "two"}
        assert (record.a, record.b) == (1, "two")

    def test_only_the_requested_keys_are_attached(self):
        APP_CONTEXT.set("a", 1)
        APP_CONTEXT.set("secret", "x")
        record = make_record()

        ContextFilter("a").filter(record)

        assert "secret" not in record.extras
        assert not hasattr(record, "secret")

    def test_keys_that_are_not_set_are_skipped(self):
        APP_CONTEXT.set("a", 1)
        record = make_record()

        ContextFilter("a", "missing").filter(record)

        assert json.loads(record.extras) == {"a": 1}

    def test_extras_is_empty_when_no_key_is_set(self):
        record = make_record()

        ContextFilter("missing").filter(record)

        assert record.extras == ""

    def test_trace_id_is_empty_without_an_active_span(self):
        record = make_record()

        ContextFilter().filter(record)

        assert record.trace_id == ""

    def test_trace_id_comes_from_the_active_span(self):
        record = make_record()

        with make_tracer().start_as_current_span("work") as span:
            ContextFilter().filter(record)
            expected = format(span.get_span_context().trace_id, "032x")

        assert record.trace_id == expected

    def test_the_filter_name_is_kept(self):
        assert ContextFilter("a", name="demo").name == "demo"


class TestRequestContextFilter:

    def test_attaches_request_correlation_and_user_ids(self):
        APP_CONTEXT.set(ContextKey.REQUEST_ID, "r-1")
        APP_CONTEXT.set(ContextKey.CORRELATION_ID, "c-1")
        APP_CONTEXT.set(ContextKey.USER_ID, "u-1")
        APP_CONTEXT.set(ContextKey.JWT, "must-not-be-logged")
        record = make_record()

        RequestContextFilter().filter(record)

        assert json.loads(record.extras) == {"request_id": "r-1", "correlation_id": "c-1", "user_id": "u-1"}

    def test_additional_keys_are_attached_too(self):
        APP_CONTEXT.set(ContextKey.REQUEST_ID, "r-1")
        APP_CONTEXT.set("venue_id", "v-1")
        record = make_record()

        RequestContextFilter("venue_id").filter(record)

        assert json.loads(record.extras) == {"request_id": "r-1", "venue_id": "v-1"}


class TestRemoveHandlers:

    def test_removes_and_closes_a_handler(self):
        logger = logging.getLogger("test-remove-one")
        handler = logging.StreamHandler()
        logger.addHandler(handler)

        remove_handlers(logger)

        assert logger.handlers == []

    @pytest.mark.xfail(strict=True, reason="handlers are removed while iterating the list, so some are skipped")
    def test_removes_every_handler(self):
        logger = logging.getLogger("test-remove-many")
        logger.handlers = []
        for _ in range(3):
            logger.addHandler(logging.StreamHandler())

        remove_handlers(logger)

        assert logger.handlers == []


class TestConfigureLogging:

    def test_sets_the_root_level_from_the_settings(self, restore_root_logger: logging.Logger, monkeypatch):
        monkeypatch.setenv("RISTOPS_LOG_LEVEL", "WARNING")

        configure_logging()

        assert restore_root_logger.level == logging.WARNING

    def test_installs_one_stream_handler_with_the_configured_formatter_and_filter(
            self, restore_root_logger: logging.Logger,
    ):
        configure_logging()

        handlers = [handler for handler in restore_root_logger.handlers if type(handler) is logging.StreamHandler]
        assert len(handlers) == 1
        assert isinstance(handlers[0].formatter, LogFormatter)
        assert any(isinstance(item, RequestContextFilter) for item in handlers[0].filters)

    def test_uses_the_formatter_named_in_the_settings(self, restore_root_logger: logging.Logger, monkeypatch):
        monkeypatch.setenv("RISTOPS_LOG_FORMATTER", "logging:Formatter")

        configure_logging()

        handler = next(h for h in restore_root_logger.handlers if type(h) is logging.StreamHandler)
        assert type(handler.formatter) is logging.Formatter

    def test_an_unknown_formatter_path_fails(self, restore_root_logger: logging.Logger, monkeypatch):
        monkeypatch.setenv("RISTOPS_LOG_FORMATTER", "no_such_module:Formatter")

        with pytest.raises(ModuleNotFoundError):
            configure_logging()

    def test_a_malformed_filter_path_fails(self, restore_root_logger: logging.Logger, monkeypatch):
        monkeypatch.setenv("RISTOPS_LOG_FILTER", "no-separator")

        with pytest.raises(ValueError, match="Invalid path"):
            configure_logging()


class TestUvicornLoggingConfig:

    def test_registers_the_context_filter(self):
        config = uvicorn_logging_config()

        assert config["filters"] == {"context_filter": {"()": "ristops_lib_core.logging.RequestContextFilter"}}

    def test_attaches_the_filter_to_every_handler(self):
        config = uvicorn_logging_config()

        assert config["handlers"]
        assert all("context_filter" in handler["filters"] for handler in config["handlers"].values())

    def test_replaces_every_formatter_with_the_log_formatter(self):
        config = uvicorn_logging_config()

        for formatter in config["formatters"].values():
            assert formatter == {"()": "ristops_lib_core.logging.LogFormatter"}

    def test_access_log_is_quiet_unless_debugging(self):
        assert uvicorn_logging_config()["loggers"]["uvicorn.access"]["level"] == "WARNING"
        assert uvicorn_logging_config(debug=True)["loggers"]["uvicorn.access"]["level"] == "DEBUG"

    def test_does_not_modify_the_uvicorn_defaults(self):
        uvicorn_logging_config()

        assert "filters" not in LOGGING_CONFIG
        assert all("filters" not in handler for handler in LOGGING_CONFIG["handlers"].values())
        assert LOGGING_CONFIG["formatters"]["default"]["()"] == "uvicorn.logging.DefaultFormatter"
        assert "fmt" in LOGGING_CONFIG["formatters"]["default"]


class TestRequestLoggingMiddleware:

    @staticmethod
    def build_app() -> FastAPI:
        app = FastAPI()
        app.add_middleware(RequestLoggingMiddleware)

        @app.get("/thing")
        async def thing() -> dict:
            return {}

        return app

    @pytest.mark.anyio
    async def test_logs_before_and_after_with_the_status(self, caplog: pytest.LogCaptureFixture):
        with caplog.at_level(logging.INFO, logger="ristops_lib_core.logging"):
            async with make_client(self.build_app()) as client:
                await client.get("/thing?name=pizza")

        messages = [record.getMessage() for record in caplog.records]
        assert '[BEFORE] Processing request "GET /thing?name=pizza"' in messages
        assert any(m.startswith("[AFTER] Processed request in ") and m.endswith('"GET /thing" 200') for m in messages)

    @pytest.mark.anyio
    async def test_before_is_logged_before_after(self, caplog: pytest.LogCaptureFixture):
        with caplog.at_level(logging.INFO, logger="ristops_lib_core.logging"):
            async with make_client(self.build_app()) as client:
                await client.get("/thing")

        messages = [record.getMessage() for record in caplog.records]
        assert messages[0].startswith("[BEFORE]") and messages[1].startswith("[AFTER]")

    @pytest.mark.anyio
    async def test_logs_unknown_routes_with_their_404(self, caplog: pytest.LogCaptureFixture):
        with caplog.at_level(logging.INFO, logger="ristops_lib_core.logging"):
            async with make_client(self.build_app()) as client:
                await client.get("/nowhere")

        assert any(r.getMessage().endswith('"GET /nowhere" 404') for r in caplog.records)
