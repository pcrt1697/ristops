from datetime import UTC, datetime
from uuid import UUID

import pytest
from pydantic import BaseModel, ValidationError

from ristops_lib_core.pydantic.types import CreatedAt, DeletedAt, ObjectUUID, UpdatedAt


class Thing(BaseModel):
    id: ObjectUUID
    created_at: CreatedAt
    updated_at: UpdatedAt
    deleted_at: DeletedAt


VALID = {
    "id": "3f2b8c1e-0000-4000-8000-000000000001",
    "created_at": "2026-10-01T10:00:00Z",
    "updated_at": "2026-10-02T10:00:00Z",
}


def test_values_are_parsed():
    thing = Thing.model_validate(VALID)

    assert thing.id == UUID(VALID["id"])
    assert thing.created_at == datetime(2026, 10, 1, 10, 0, tzinfo=UTC)
    assert thing.updated_at == datetime(2026, 10, 2, 10, 0, tzinfo=UTC)


def test_deleted_at_defaults_to_none():
    assert Thing.model_validate(VALID).deleted_at is None


def test_deleted_at_accepts_a_date():
    thing = Thing.model_validate({**VALID, "deleted_at": "2026-10-03T10:00:00Z"})

    assert thing.deleted_at == datetime(2026, 10, 3, 10, 0, tzinfo=UTC)


def test_invalid_id_is_rejected():
    with pytest.raises(ValidationError):
        Thing.model_validate({**VALID, "id": "not-a-uuid"})


def test_missing_creation_date_is_rejected():
    with pytest.raises(ValidationError):
        Thing.model_validate({key: value for key, value in VALID.items() if key != "created_at"})


def test_fields_carry_a_description_in_the_schema():
    properties = Thing.model_json_schema()["properties"]

    assert all("description" in properties[name] for name in ("id", "created_at", "updated_at", "deleted_at"))
