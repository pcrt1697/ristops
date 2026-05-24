from enum import StrEnum


class ResourceEventType(StrEnum):
    created = "created"
    deleted = "deleted"
    updated = "updated"
