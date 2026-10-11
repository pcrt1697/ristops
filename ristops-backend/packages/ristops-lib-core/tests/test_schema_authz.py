from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from ristops_lib_core.schema.authz import (
    PERMISSION_SEPARATOR, AclCheckRequest, AclResponse, AuthorizationGrant, AuthorizationResource,
    CheckAuthorizationRequest, GrantRoleRequest, ListRolesQuery, ListRolesResponse, ListUserResourceGrantsResponse,
    ResourceType, ResourceUserGrantsResponse, RevokeAccessRequest, RoleGrant, RoleResponse,
)

VENUE = {"resource_id": "v-1", "resource_type": "venue"}


def test_resource_types():
    assert {member.value for member in ResourceType} == {
        "app", "venue", "service", "reservation", "permission", "role", "acl", "user",
    }


def test_the_permission_separator_splits_scope_from_action():
    assert "venue:add".split(PERMISSION_SEPARATOR) == ["venue", "add"]


class TestAuthorizationResource:

    def test_parses_the_type_into_the_enum(self):
        resource = AuthorizationResource.model_validate(VENUE)

        assert resource.resource_type is ResourceType.VENUE

    def test_rejects_an_unknown_type(self):
        with pytest.raises(ValidationError):
            AuthorizationResource(resource_id="x", resource_type="spaceship")

    def test_requires_an_id(self):
        with pytest.raises(ValidationError):
            AuthorizationResource.model_validate({"resource_type": "venue"})

    def test_serializes_the_type_as_a_plain_string(self):
        assert AuthorizationResource.model_validate(VENUE).model_dump(mode="json") == VENUE


class TestCheckAuthorizationRequest:

    def test_parses_nested_grants(self):
        request = CheckAuthorizationRequest.model_validate({
            "user_id": "u-1",
            "grants": [{"resource": VENUE, "permissions": ["venue:get", "venue:edit"]}],
        })

        assert request.grants[0].resource.resource_id == "v-1"
        assert request.grants[0].permissions == ["venue:get", "venue:edit"]

    def test_accepts_no_grants(self):
        assert CheckAuthorizationRequest(user_id="u-1", grants=[]).grants == []

    def test_requires_a_user(self):
        with pytest.raises(ValidationError):
            CheckAuthorizationRequest.model_validate({"grants": []})

    def test_a_grant_requires_its_permissions(self):
        with pytest.raises(ValidationError):
            AuthorizationGrant.model_validate({"resource": VENUE})

    def test_the_acl_check_body_has_only_grants(self):
        body = AclCheckRequest.model_validate({"grants": [{"resource": VENUE, "permissions": []}]})

        assert "user_id" not in body.model_dump()


class TestGrantRoleRequest:

    def test_the_expiry_is_optional(self):
        assert GrantRoleRequest(user_id="u-1", role_id="venue.owner").expires_at is None

    def test_parses_the_expiry(self):
        request = GrantRoleRequest.model_validate(
            {"user_id": "u-1", "role_id": "venue.owner", "expires_at": "2026-12-31T23:59:00Z"},
        )

        assert request.expires_at == datetime(2026, 12, 31, 23, 59, tzinfo=UTC)

    def test_rejects_an_invalid_expiry(self):
        with pytest.raises(ValidationError):
            GrantRoleRequest(user_id="u-1", role_id="venue.owner", expires_at="tomorrow-ish")


class TestRevokeAccessRequest:

    def test_parses_the_nested_resource(self):
        request = RevokeAccessRequest.model_validate({"user_id": "u-1", "role_id": "r", "resource": VENUE})

        assert request.resource.resource_type is ResourceType.VENUE


class TestAclResponse:

    def test_round_trips_through_json(self):
        acl = AclResponse(
            id="a-1", created_at=datetime(2026, 10, 1, tzinfo=UTC), user_id="u-1", role_id="venue.owner",
            resource=AuthorizationResource(resource_id="v-1", resource_type=ResourceType.VENUE),
            expires_at=datetime(2027, 1, 1, tzinfo=UTC),
        )

        assert AclResponse.model_validate_json(acl.model_dump_json()) == acl

    def test_the_expiry_defaults_to_none(self):
        acl = AclResponse.model_validate({
            "id": "a-1", "created_at": "2026-10-01T00:00:00Z", "user_id": "u-1", "role_id": "r", "resource": VENUE,
        })

        assert acl.expires_at is None


class TestRoles:

    def test_a_role_response_has_a_scope_and_permissions(self):
        role = RoleResponse.model_validate({
            "id": "venue.manager", "scope": "venue", "name": "Venue Manager", "description": "d",
            "permissions": ["venue:get"],
        })

        assert role.scope is ResourceType.VENUE
        assert ListRolesResponse(roles=[role]).roles == [role]

    def test_a_role_requires_a_valid_scope(self):
        with pytest.raises(ValidationError):
            RoleResponse.model_validate(
                {"id": "r", "scope": "nowhere", "name": "n", "description": "d", "permissions": []},
            )

    def test_the_roles_query_has_no_filter_by_default(self):
        query = ListRolesQuery()

        assert (query.role_id, query.role_name, query.permission, query.scope) == (None, None, None, None)

    def test_the_roles_query_scope_is_an_enum(self):
        assert ListRolesQuery(scope="venue").scope is ResourceType.VENUE
        with pytest.raises(ValidationError):
            ListRolesQuery(scope="nowhere")


class TestGrantListings:

    def test_resource_grants_nest_roles_and_permissions(self):
        response = ListUserResourceGrantsResponse.model_validate({
            "grants": [{"resource": VENUE, "roles": [{"role_id": "venue.owner", "permissions": ["*"]}]}],
        })

        assert response.grants[0].roles[0].permissions == ["*"]

    def test_user_grants_carry_the_assignment_and_expiry(self):
        response = ResourceUserGrantsResponse.model_validate({
            "user_id": "u-1",
            "grants": [{"resource": VENUE, "role_id": "venue.owner", "assigned_at": "2026-10-01T00:00:00Z"}],
        })

        grant: RoleGrant = response.grants[0]
        assert grant.expires_at is None
        assert grant.assigned_at == datetime(2026, 10, 1, tzinfo=UTC)
