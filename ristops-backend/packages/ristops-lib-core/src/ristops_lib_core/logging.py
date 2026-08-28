import json
import logging
import time
from copy import deepcopy
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import SettingsConfigDict
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from uvicorn.config import LOGGING_CONFIG

from ristops_lib_core.context import APP_CONTEXT, ContextKey
from ristops_lib_core.settings import BaseServiceSettings, ENVVARS_PREFIX
from ristops_lib_core.tracing import get_trace_id
from ristops_lib_core.utils import load_object

_logger = logging.getLogger(__name__)
LINE_FORMAT = (
    "%(asctime)s [%(levelname)-8s] [%(name)s:%(lineno)d] "
    "[trace_id=%(trace_id)s] [%(extras)s] "
    "- %(message)s "
)


class LogSettings(BaseServiceSettings):
    """ Logging settings """
    model_config = SettingsConfigDict(
        env_prefix=ENVVARS_PREFIX + "LOG_",
    )

    filter: str = Field(
        default="ristops_lib_core.logging:RequestContextFilter",
        description="Path to the log filter, using the format `package.path:<class-name>`.",
        examples=["ristops_lib_core.logging:RequestContextFilter"]
    )
    formatter: str = Field(
        default="ristops_lib_core.logging:LogFormatter",
        description="Path to the log formatter, using the format `package.path:<class-name>`.",
        examples=["ristops_lib_core.logging:LogFormatter"]
    )
    level: int = Field(
        default=logging.INFO,
        description="Log level compatible with Python logging module (number or string).",
        examples=["INFO", logging.DEBUG],
    )

    @field_validator("level", mode="before")
    @classmethod
    def parse_level(cls, value):
        if isinstance(value, int):
            return value
        _value = str(value).upper()
        level = logging.getLevelName(value.upper())
        if isinstance(level, int):
            return level
        raise ValueError(f"Invalid log level: {value}")


class LogFormatter(logging.Formatter):
    def __init__(self):
        super().__init__(LINE_FORMAT)


def _get_context_keys(*keys: str) -> dict[str, Any]:
    """ Return a dictionary containing the requested context keys """
    _keys = {}
    for key in keys:
        if (value := APP_CONTEXT.get(key)) is not None:
            _keys[key] = value
    return _keys


class ContextFilter(logging.Filter):
    """ Attach context keys to log records """

    def __init__(self, *context_keys: str, name: str = ''):
        super().__init__(name)
        self._context_keys = context_keys

    def filter(self, record: logging.LogRecord) -> bool:
        # serialize any extra fields passed via extra={}
        extras = _get_context_keys(*self._context_keys)
        record.extras = json.dumps(extras) if extras else ""
        # also set each key as its own record attribute, so the OTLP log exporter (when the
        # service has telemetry enabled) ships them as structured, queryable attributes rather
        # than fields buried inside one opaque JSON string
        for key, value in extras.items():
            setattr(record, key, value)
        # always present, even with no active span, so LINE_FORMAT can reference it unconditionally
        record.trace_id = get_trace_id() or ""
        return True


class RequestContextFilter(ContextFilter):
    """ Attach request context keys to log records """

    def __init__(self, *additional_keys: str, name: str = ''):
        super().__init__(
            *(ContextKey.REQUEST_ID, ContextKey.CORRELATION_ID, ContextKey.USER_ID) + additional_keys,
            name=name,
        )


def remove_handlers(logger: logging.Logger):
    """ Remove all logging handlers """
    for handler in logger.handlers:
        logger.removeHandler(handler)
        handler.close()


def configure_logging():
    """ Configure app loggers """
    settings = LogSettings.get()

    logger = logging.getLogger()
    remove_handlers(logger)

    level = logging.getLevelName(settings.level)
    logger.setLevel(level)

    _filter_cls = load_object(settings.filter)
    _filter = _filter_cls()
    _formatter_cls = load_object(settings.formatter)
    _formatter = _formatter_cls()

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(_formatter)
    stream_handler.addFilter(_filter)
    logger.addHandler(stream_handler)


def uvicorn_logging_config(debug: bool = False) -> dict:
    """ Return logging configuration to use for uvicorn app """
    logging_config = deepcopy(LOGGING_CONFIG)

    # set filter
    logging_config["filters"] = {
        "context_filter": {
            "()": RequestContextFilter.__module__ + "." + RequestContextFilter.__name__,
        }
    }

    # set formatter
    for name, cfg in logging_config['formatters'].items():
        cfg.pop('fmt', None)
        cfg.pop('use_colors', None)
        cfg['()'] = LogFormatter.__module__ + '.' + LogFormatter.__name__

    # attach filter to all handlers
    for handler in logging_config["handlers"].values():
        handler.setdefault("filters", []).append("context_filter")

    logging_config["loggers"]["uvicorn.access"] = {
        "level": "DEBUG" if debug else "WARNING",
        "handlers": ["default"],
        "propagate": False,
    }
    return logging_config


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """ Middleware used to log requests. """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.time()
        _logger.info('[BEFORE] Processing request "%s %s?%s"', request.method, request.url.path, request.url.query)
        response = await call_next(request)
        _logger.info(
            '[AFTER] Processed request in %.3fs "%s %s" %s',
            time.time() - start_time,
            request.method,
            request.url.path,
            response.status_code,
        )
        return response
