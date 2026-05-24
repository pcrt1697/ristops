from enum import StrEnum


class ResourceEventType(StrEnum):
    CREATED = "created"
    DELETED = "deleted"
    UPDATED = "updated"
