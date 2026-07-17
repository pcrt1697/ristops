import logging
from http import HTTPStatus
from typing import Callable, Awaitable, Protocol

from fastapi import Request, HTTPException

from ristops_lib_core.schema.authz import (
    AuthorizationGrant, AuthorizationResource,
    ResourceType
)

_logger = logging.getLogger(__name__)
POLICY = "_policy"


class PolicyInterface(Protocol):
    async def __call__(self, request: Request) -> AuthorizationGrant:
        ...


PermissionsResolver = Callable[[Request], Awaitable[list[str]]]


class Policy:
    """ ACL grant resource definition. """

    def __init__(
            self,
            resource_resolver: ResourceResolver,
            *permissions: str,
            permissions_resolver: PermissionsResolver | None = None,
    ) -> None:
        self._resource_resolver = resource_resolver
        self._permissions = list(permissions)
        self._permissions_resolver = permissions_resolver
        self._name = str(self)

    async def __call__(self, request: Request) -> AuthorizationGrant:
        _logger.debug("Parsing policy %s", self._name)
        resource = await self._resource_resolver(request)
        permissions = (
            await self._permissions_resolver(request)
            if self._permissions_resolver is not None
            else self._permissions
        )
        _logger.debug(
            "Policy %s resolved to resource %s of type %s, permissions %s",
            self._name, resource.resource_id, resource.resource_type, permissions
        )
        return AuthorizationGrant(
            resource=resource,
            permissions=permissions,
        )

    def __str__(self):
        return str(f"{self.__class__.__name__}[resolver={self._resource_resolver}, permissions={self._permissions}]")


def policy(*policies: PolicyInterface) -> Callable:
    """ Attach a policy to the route. """

    def wrapper(route_func: Callable):
        assert isinstance(policies, tuple)
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


def resolve_static_resource(resource_id: str, resource_type: ResourceType) -> ResourceResolver:
    async def _resolver(_: Request) -> AuthorizationResource:
        return AuthorizationResource(
            resource_id=resource_id,
            resource_type=resource_type,
        )

    return _resolver


async def resolve_path_resource(request: Request) -> AuthorizationResource:
    """Resolve the target resource from the `resource_type` and `resource_id` path params."""
    return AuthorizationResource(
        resource_id=request.path_params["resource_id"],
        resource_type=ResourceType(request.path_params["resource_type"]),
    )


def resolve_permission_from_body_field(field_name: str, mapping: dict[str, str]) -> PermissionsResolver:
    """Build a `permissions_resolver` that reads `field_name` from the request body and maps its
    value to a single required permission via `mapping`. Raises 400 on an unmapped value.

    Lets one route require a different permission per request, based on request content, rather
    than a fixed permission list decided at route-decoration time (e.g. a single "perform this
    action" endpoint whose action type determines who may call it).
    """

    async def _resolver(request: Request) -> list[str]:
        value = await resolve_body_attribute(request, field_name)
        permission = mapping.get(value)
        if permission is None:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Unknown {field_name}: {value}",
            )
        return [permission]

    return _resolver
