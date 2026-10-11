from datetime import UTC, datetime
from uuid import UUID

import pytest
from pydantic import SecretStr, ValidationError

from ristops_lib_core.schema.authn import LoginRequest, LoginResponse, RefreshTokenRequest
from ristops_lib_core.schema.user import AppMember, MemberResponse, UserResponse

USER_ID = "3f2b8c1e-0000-4000-8000-000000000001"
NOW = "2026-10-01T10:00:00Z"


class TestLoginRequest:

    def test_parses_a_valid_login(self):
        request = LoginRequest(email="alice@example.com", password="s3cret")

        assert request.email == "alice@example.com"
        assert request.password.get_secret_value() == "s3cret"

    @pytest.mark.parametrize("email", ["alice", "alice@", "@example.com", ""])
    def test_rejects_an_invalid_email(self, email: str):
        with pytest.raises(ValidationError):
            LoginRequest(email=email, password="x")

    def test_the_password_is_not_revealed_by_repr_or_json(self):
        request = LoginRequest(email="alice@example.com", password="s3cret")

        assert "s3cret" not in repr(request)
        assert "s3cret" not in request.model_dump_json()

    def test_the_password_is_a_secret_string(self):
        assert isinstance(LoginRequest(email="alice@example.com", password="x").password, SecretStr)

    def test_both_fields_are_required(self):
        with pytest.raises(ValidationError):
            LoginRequest.model_validate({"email": "alice@example.com"})


class TestTokens:

    def test_a_login_response_carries_both_tokens(self):
        response = LoginResponse(user_id="alice", access_token="a", refresh_token="r")

        assert response.model_dump() == {"user_id": "alice", "access_token": "a", "refresh_token": "r"}

    def test_a_login_response_requires_every_field(self):
        with pytest.raises(ValidationError):
            LoginResponse.model_validate({"user_id": "alice", "access_token": "a"})

    def test_a_refresh_request_requires_its_token(self):
        assert RefreshTokenRequest(refresh_token="r").refresh_token == "r"
        with pytest.raises(ValidationError):
            RefreshTokenRequest.model_validate({})


class TestUserResponse:

    def valid(self, **overrides) -> dict:
        return {
            "id": USER_ID, "username": "alice", "email": "alice@example.com",
            "created_at": NOW, "updated_at": NOW, **overrides,
        }

    def test_parses_a_user(self):
        user = UserResponse.model_validate(self.valid())

        assert user.id == UUID(USER_ID)
        assert user.created_at == datetime(2026, 10, 1, 10, tzinfo=UTC)

    def test_the_display_name_is_optional(self):
        assert UserResponse.model_validate(self.valid()).display_name is None
        assert UserResponse.model_validate(self.valid(display_name="Alice")).display_name == "Alice"

    def test_rejects_an_invalid_email(self):
        with pytest.raises(ValidationError):
            UserResponse.model_validate(self.valid(email="not-an-email"))

    def test_rejects_an_invalid_id(self):
        with pytest.raises(ValidationError):
            UserResponse.model_validate(self.valid(id="1234"))


class TestMemberResponse:

    def test_a_member_has_no_email(self):
        member = MemberResponse.model_validate(
            {"id": USER_ID, "username": "alice", "created_at": NOW, "email": "alice@example.com"},
        )

        assert "email" not in member.model_dump()
        assert "email" not in MemberResponse.model_fields

    def test_a_member_is_an_app_member_with_a_creation_date(self):
        assert issubclass(MemberResponse, AppMember)
        assert set(MemberResponse.model_fields) - set(AppMember.model_fields) == {"created_at"}

    def test_the_display_name_is_optional(self):
        assert AppMember(id=USER_ID, username="alice").display_name is None
