from fastapi import APIRouter

from ristops_lib_neo4j.engine import neo4j_transactional
from ristops_be_authz.domain.acl.service import check_acl_authorization, grant_access
from ristops_lib_be.authz.policy import policy, Policy, BaseResourceResolver, resolve_body_attribute
from ristops_lib_core.schema.authz import (
    AuthorizationResponse, CheckAuthorizationRequest, ResourceType,
    GrantAccessRequest, AclResponse
)

_user_body_resolver = BaseResourceResolver(ResourceType.USER, resolver=resolve_body_attribute)
acl_router = APIRouter(
    prefix="/acl",
    tags=["acl"],
)


@acl_router.post(
    "/check",
    response_model=AuthorizationResponse
)
@policy(Policy(_user_body_resolver, "acl~get"))
@neo4j_transactional
async def check(
        request: CheckAuthorizationRequest,
) -> AuthorizationResponse:
    is_authorized = await check_acl_authorization(request)
    return AuthorizationResponse(is_authorized=is_authorized)


@acl_router.post(
    "",
    response_model=AuthorizationResponse
)
@policy(Policy(_user_body_resolver, "acl~add"))
@neo4j_transactional
async def create_acl(
        request: GrantAccessRequest,
) -> AclResponse:
    """ Grant access to resource. """
    acl = await grant_access(request)
    return AclResponse(
        id=acl.id,
        created_at=acl.created_at,
    )
