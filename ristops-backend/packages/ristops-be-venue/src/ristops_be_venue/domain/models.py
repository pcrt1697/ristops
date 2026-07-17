from enum import StrEnum


class VenueStatus(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    DISABLED = "disabled"
    CLOSED = "closed"


class VenueActionType(StrEnum):
    """A lifecycle action that can be performed on a venue — distinct from `VenueStatus`:
    ACTIVATE and ENABLE both land on ACTIVE, but are different actions requiring different
    permissions depending on the venue's current status."""

    ACTIVATE = "activate"
    CLOSE = "close"
    DISABLE = "disable"
    ENABLE = "enable"
