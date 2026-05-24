import logging
from typing import Callable, Awaitable, Protocol

from fastapi import Request

from ristops_lib_core.schema.authz import (
    AuthorizationGrant, AuthorizationResource,
    ResourceType
)

_logger = logging.getLogger(__name__)
POLICY = "_policy"


class PolicyInterface(Protocol):
    async def __call__(self, request: Request) -> AuthorizationGrant:
        ...


class Policy:
    """ ACL grant resource definition. """

    def __init__(
            self,
            resource_resolver: ResourceResolver,
            *permissions: str,
    ) -> None:
        self._resource_resolver = resource_resolver
        self._permissions = list(permissions)
        self._name = str(self)

    async def __call__(self, request: Request) -> AuthorizationGrant:
        _logger.debug("Parsing policy %s", self._name)
        resource = await self._resource_resolver(request)
        _logger.debug(
            "Policy %s resolved to resource %s of type %s",
            self._name, resource.resource_id, resource.resource_type
        )
        return AuthorizationGrant(
            resource=resource,
            permissions=self._permissions,
        )

    def __str__(self):
        return str(f"{self.__class__.__name__}[resolver={self._resource_resolver}, permissions={self._permissions}]")


def policy(*policies: PolicyInterface) -> Callable:
    """ Attach a policy to the route. """

    def wrapper(route_func: Callable):
        isinstance(policies, tuple)
        setattr(route_func, POLICY, policies)
        return route_func

    return wrapper


ResourceResolver = Callable[[Request], Awaitable[AuthorizationResource]]
RequestAttributeResourceResolver = Callable[[Request, str], Awaitable[str]]


class BaseResourceResolver:

    def __init__(
            self,
            resource_type: ResourceType,
            field: str = None,
            resolver: RequestAttributeResourceResolver = None,
    ) -> None:
        self._resource_type = resource_type
        self._field = field or f"{resource_type.value.lower()}_id"
        self._resolver = resolver or resolve_path_attribute

    async def __call__(self, request: Request) -> AuthorizationResource:
        _id = await self._resolver(request, self._field)
        return AuthorizationResource(
            resource_id=_id,
            resource_type=self._resource_type,
        )


async def resolve_path_attribute(request: Request, field_name: str) -> str:
    return request.path_params[field_name]


async def resolve_query_attribute(request: Request, field_name: str) -> str:
    return request.query_params[field_name]


async def resolve_body_attribute(request: Request, field_name: str) -> str:
    _json = await request.json()
    for field in field_name.split("."):
        _json = _json[field]
    return _json
