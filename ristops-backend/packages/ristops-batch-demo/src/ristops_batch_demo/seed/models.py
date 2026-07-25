from pydantic import BaseModel, Field


class DemoUser(BaseModel):
    """A demo user to register through the authn API (``users.json``)."""

    username: str = Field(description="Unique username; also used as the login password.")
    email: str = Field(description="Unique email address.")
    display_name: str | None = Field(default=None, description="Human-readable name.")
    password: str | None = Field(
        default=None,
        description="Login password; falls back to the username when omitted.",
    )

    @property
    def login_password(self) -> str:
        """Return the password to register, defaulting to the username."""
        return self.password or self.username


class DemoUsers(BaseModel):
    """Top-level schema of ``users.json``."""

    users: list[DemoUser] = Field(default_factory=list)


class DemoVenue(BaseModel):
    """A demo venue to create through the venue API (``venues.json``)."""

    key: str = Field(description="Symbolic reference used by assignments (e.g. 'stark').")
    name: str = Field(description="Venue name.")
    address: str = Field(description="Venue address.")
    description: str | None = Field(default=None, description="Venue description.")
    timezone: str = Field(description="IANA timezone name of the venue.")
    # Forward ref: DemoClosing (same date/weekday shape as a service closing) is defined below;
    # resolved by the DemoVenue.model_rebuild() at the end of the module.
    closings: list["DemoClosing"] = Field(
        default_factory=list,
        description="Venue-wide calendar closings (closes every service for date ranges).",
    )


class DemoVenues(BaseModel):
    """Top-level schema of ``venues.json``."""

    venues: list[DemoVenue] = Field(default_factory=list)


class DemoOpening(BaseModel):
    """A single weekly opening (open day) for a service."""

    weekday: str = Field(
        description="Day of the week, lowercase (e.g. 'monday').",
    )
    capacity: int = Field(description="Maximum number of reservable seats.", gt=0)
    start_time: str = Field(description="Time the service opens, 'HH:MM'.")
    end_time: str = Field(description="Time the service closes, 'HH:MM'.")
    description: str | None = Field(
        default=None, description="Optional note for this opening.", max_length=1000
    )


class DemoExceptionDates(BaseModel):
    """When a calendar exception (override/closing) occurs: a fixed annual ``"MM-DD"`` range,
    materialized once per entry in ``year_offsets`` (relative to the current *year* only — the
    day/month are always fixed, so seed data never depends on which day it happens to be seeded
    on). ``[-1, 0, 1]`` gives the previous, current, and next year.
    """

    month_day_start: str = Field(description="Annual start 'MM-DD'.")
    month_day_end: str = Field(description="Annual end 'MM-DD'.")
    year_offsets: list[int] = Field(
        default_factory=lambda: [-1, 0, 1],
        description="Year offsets relative to the current year.",
    )


class DemoOverride(BaseModel):
    """A calendar opening override (special hours/capacity for a date range)."""

    dates: DemoExceptionDates = Field(description="When the override applies.")
    weekday: str | None = Field(
        default=None,
        description="Lowercase weekday (e.g. 'friday') to scope to; null means every day in the range.",
    )
    capacity: int = Field(description="Overridden maximum number of reservable seats.", gt=0)
    start_time: str = Field(description="Overridden opening time, 'HH:MM'.")
    end_time: str = Field(description="Overridden closing time, 'HH:MM'.")
    description: str | None = Field(
        default=None, description="Optional note for this override.", max_length=1000
    )


class DemoClosing(BaseModel):
    """A calendar closing (the service is closed for a date range)."""

    dates: DemoExceptionDates = Field(description="When the closing applies.")
    weekday: str | None = Field(
        default=None,
        description="Lowercase weekday (e.g. 'monday') to scope to; null means every day in the range.",
    )
    description: str | None = Field(
        default=None, description="Optional note for this closing.", max_length=1000
    )


class DemoCapacityOverride(BaseModel):
    """A calendar capacity override (a signed seat delta on top of the resolved capacity)."""

    dates: DemoExceptionDates = Field(description="When the capacity override applies.")
    weekday: str | None = Field(
        default=None,
        description="Lowercase weekday to scope to; null means every day in the range.",
    )
    capacity_delta: int = Field(
        description="Signed change to the resolved seat count (e.g. 30 for a garden, -10 for a partial closure).",
    )
    description: str | None = Field(
        default=None, description="Optional note for this capacity override.", max_length=1000
    )


class DemoService(BaseModel):
    """A demo service to create under a venue through the reservation API (``services.json``)."""

    venue: str = Field(description="Venue key, matching a 'key' in venues.json.")
    name: str = Field(description="Service name.", max_length=120)
    description: str | None = Field(
        default=None, description="Service description.", max_length=1000
    )
    turn_time_m: int = Field(description="Reservation duration, in minutes.", gt=0)
    advance_notice_m: int = Field(
        description="Minimum notice required before a reservation slot, in minutes.", ge=0
    )
    slot_interval_m: int = Field(
        description="Interval between reservation slots, in minutes.", gt=0
    )
    grace_period_m: int = Field(
        description="Minutes past a reservation's start time before it may be marked a no-show.",
        ge=0,
    )
    openings: list[DemoOpening] = Field(
        default_factory=list,
        description="Weekly opening hours (open days) for this service.",
    )
    overrides: list[DemoOverride] = Field(
        default_factory=list,
        description="Calendar opening overrides (special hours for date ranges).",
    )
    closings: list[DemoClosing] = Field(
        default_factory=list,
        description="Calendar closings (service closed for date ranges).",
    )
    capacity_overrides: list[DemoCapacityOverride] = Field(
        default_factory=list,
        description="Calendar capacity overrides (seat deltas for date ranges).",
    )


class DemoServices(BaseModel):
    """Top-level schema of ``services.json``."""

    services: list[DemoService] = Field(default_factory=list)


class DemoAssignment(BaseModel):
    """A role grant for a set of users on a venue (``assignments.json``)."""

    venue: str = Field(description="Venue key, matching a 'key' in venues.json.")
    role_id: str = Field(description="Role to grant (e.g. 'venue.owner').")
    usernames: list[str] = Field(
        default_factory=list,
        description="Usernames, matching 'username' values in users.json.",
    )


class DemoAssignments(BaseModel):
    """Top-level schema of ``assignments.json``."""

    assignments: list[DemoAssignment] = Field(default_factory=list)


# Resolve DemoVenue's forward reference to DemoClosing, now that it is defined above.
DemoVenue.model_rebuild()
