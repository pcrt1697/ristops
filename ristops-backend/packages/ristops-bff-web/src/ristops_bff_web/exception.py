import logging
from http import HTTPStatus

from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from graphql import GraphQLError, ExecutionContext
from strawberry.extensions import SchemaExtension

from ristops_lib_core.context import APP_CONTEXT, ContextKey
from ristops_lib_core.exception import get_validation_error_message, ErrorResponse

_logger = logging.getLogger(__name__)


def process_errors(errors: list[GraphQLError], _: ExecutionContext) -> None:
    for error in errors:
        original = error.original_error
        if original:
            _logger.exception(f"Unhandled GraphQL error: {original}", exc_info=original)


def http_exception_to_message(exc: HTTPException) -> str:
    if exc.detail:
        try:
            if isinstance(exc.detail, dict):
                error_message = ErrorResponse.model_validate(exc.detail)
            else:
                error_message = ErrorResponse.model_validate_json(exc.detail)
            return f"{error_message.title}. {error_message.detail}"
        except Exception as exc:
            _logger.error(f"Failed to parse HTTP exception", exc_info=exc)
    return HTTPStatus(exc.status_code).phrase


class ErrorHandlingExtension(SchemaExtension):
    async def on_execute(self):
        """ Hook to override exception messages to avoid internal code exposure. """
        yield

        result = self.execution_context.result
        if not result or not result.errors:
            return
        _errors: list[GraphQLError] = result.errors
        for error in _errors:
            original = error.original_error
            if isinstance(original, HTTPException):
                error.message = http_exception_to_message(original)
                code = original.status_code
            elif isinstance(original, RequestValidationError):
                error.message = get_validation_error_message(original)
                code = HTTPStatus.UNPROCESSABLE_ENTITY
            elif original:
                error.message = HTTPStatus.INTERNAL_SERVER_ERROR.phrase
                code = HTTPStatus.INTERNAL_SERVER_ERROR
            else:
                code = HTTPStatus.INTERNAL_SERVER_ERROR
            # Surface the status code and request id so the client can react
            # (e.g. self-heal on 404) and display a traceable id.
            error.extensions = {
                **(error.extensions or {}),
                "code": int(code),
                "correlationId": APP_CONTEXT.get(ContextKey.CORRELATION_ID),
                "requestId": APP_CONTEXT.get(ContextKey.REQUEST_ID),
            }
