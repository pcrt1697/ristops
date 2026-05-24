import logging
from typing import Callable, Any

from graphql import GraphQLResolveInfo
from graphql.pyutils import AwaitableOrValue
from strawberry.extensions import SchemaExtension

from ristops_bff_web.context import BffContextKey
from ristops_lib_core.logging import RequestContextFilter

_logger = logging.getLogger(__name__)


class ResolverLoggingExtension(SchemaExtension):
    """ Log resolver paths before executing them."""

    def resolve(
            self,
            _next: Callable,
            root: Any,
            info: GraphQLResolveInfo,
            *args: str,
            **kwargs: Any,
    ) -> AwaitableOrValue[object]:
        if info.path.typename == "Query":
            _logger.info("Resolving graphql path: %s", info.path)
        return _next(root, info, *args, **kwargs)


class GraphQLRequestContextFilter(RequestContextFilter):
    """ Attach GraphQL and HTTP request context keys to log records """

    def __init__(self) -> None:
        super().__init__(BffContextKey.GRAPHQL_OPERATION, BffContextKey.SESSION_ID)
