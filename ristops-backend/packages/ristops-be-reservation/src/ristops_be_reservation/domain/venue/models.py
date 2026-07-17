from enum import StrEnum


class VenueStatus(StrEnum):
    """Local, narrow copy of be-venue's venue status — not imported from be-venue's package."""

    PENDING = "pending"
    ACTIVE = "active"
    DISABLED = "disabled"
    CLOSED = "closed"
