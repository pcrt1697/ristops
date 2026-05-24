from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Path, Body
from starlette.requests import Request

from ristops_be_authz.database.engine import neo4j_transactional
from ristops_be_authz.domain.resource.service import find_or_create_resources, delete_resource
from ristops_lib_be.authz.policy import (
    resolve_path_attribute, policy, Policy,
)
from ristops_lib_core.schema.authz import (
    CreateAuthorizationResourceRequest, AuthorizationResourceResponse, AuthorizationResource, ResourceType,
    AuthorizationResourcesResponse
)


async def _authorization_resource_path_resolver(request: Request) -> AuthorizationResource:
    resource_id = await resolve_path_attribute(request, "resource_id")
    _resource_type = await resolve_path_attribute(request, "resource_type")
    resource_type = ResourceType(_resource_type)
    return AuthorizationResource(
        resource_id=resource_id,
        resource_type=resource_type,
    )


resource_router = APIRouter(
    prefix="/resources",
    tags=["resources"],
)


@resource_router.post(
    "/{resource_type}/{resource_id}/children",
    response_model=AuthorizationResourcesResponse
)
@policy(Policy(_authorization_resource_path_resolver, "resource~add"))
@neo4j_transactional
async def create(
        resource_type: Annotated[ResourceType, Path(description="Resource type")],
        resource_id: Annotated[str, Path(description="Resource ID")],
        request: Annotated[CreateAuthorizationResourceRequest, Body(description="Resource definition")],
) -> AuthorizationResourcesResponse:
    """ Create an auth resource. User must have resource creation permissions to a parent resource. """
    _resources = await find_or_create_resources(resource_type, resource_id, request)
    resources = [
        AuthorizationResourceResponse(
            resource_type=resource.resource_type,
            resource_id=resource.resource_id,
        )
        for resource in _resources
    ]
    return AuthorizationResourcesResponse(resources=resources)


@resource_router.delete(
    "/{resource_type}/{resource_id}",
    status_code=HTTPStatus.NO_CONTENT,
)
@policy(Policy(_authorization_resource_path_resolver, "resource~remove"))
@neo4j_transactional
async def delete(
        resource_type: Annotated[ResourceType, Path(description="Resource type")],
        resource_id: Annotated[str, Path(description="Resource ID")],
) -> None:
    """ Create an auth resource. User must have resource delete permissions a parent resource. """
    await delete_resource(resource_type, resource_id)
