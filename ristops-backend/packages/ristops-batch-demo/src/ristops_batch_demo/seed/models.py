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


class DemoDateRange(BaseModel):
    """A fixed annual ``"MM-DD"`` range, materialized once per entry in ``year_offsets``
    (relative to the current *year* only — the day/month are always fixed, so seed data never
    depends on which day it happens to be seeded on). ``[-1, 0, 1]`` gives the previous, current
    and next year.
    """

    month_day_start: str = Field(description="Annual start 'MM-DD'.")
    month_day_end: str = Field(description="Annual end 'MM-DD'.")
    year_offsets: list[int] = Field(
        default_factory=lambda: [-1, 0, 1],
        description="Year offsets relative to the current year.",
    )


class DemoClosing(BaseModel):
    """A closing: a date range over which the named services do not run (``venues.json``).

    Listing every service of the venue is how a venue-wide shutdown is expressed. A closing is
    also what makes room for a one-off service on a date the regular one already covers.
    """

    dates: DemoDateRange = Field(description="When the closing applies.")
    services: list[str] = Field(
        default_factory=list,
        description="Service names to close, matching 'name' values in services.json. Empty "
                    "closes every service of the venue.",
    )
    description: str | None = Field(
        default=None, description="Optional note for this closing.", max_length=1000
    )
    after_reservations: bool = Field(
        default=False,
        description="Create the closing once the demo bookings exist. A date cannot be booked "
                    "once it is closed, so this is how a closing is made to cover bookings, "
                    "leaving them on a closed service.",
    )


class DemoVenue(BaseModel):
    """A demo venue to create through the venue API (``venues.json``)."""

    key: str = Field(description="Symbolic reference used by assignments (e.g. 'stark').")
    name: str = Field(description="Venue name.")
    address: str = Field(description="Venue address.")
    description: str | None = Field(default=None, description="Venue description.")
    timezone: str = Field(description="IANA timezone name of the venue.")
    closings: list[DemoClosing] = Field(
        default_factory=list,
        description="Closings for this venue's services.",
    )


class DemoVenues(BaseModel):
    """Top-level schema of ``venues.json``."""

    venues: list[DemoVenue] = Field(default_factory=list)


class DemoOpening(BaseModel):
    """A single weekly opening (open day) for a service."""

    weekday: str = Field(
        description="Day of the week, lowercase (e.g. 'monday').",
    )
    start_time: str = Field(description="Time the service opens, 'HH:MM'.")
    end_time: str = Field(
        description="Time the service closes, 'HH:MM'. An end at or before the start runs the "
                    "opening overnight, closing on the following day.",
    )
    description: str | None = Field(
        default=None, description="Optional note for this opening.", max_length=1000
    )


class DemoService(BaseModel):
    """A demo service to create under a venue through the reservation API (``services.json``).

    ``dates`` is optional: omitted, the service runs indefinitely. Giving a single-day range
    makes a one-off service — the way a special evening is modelled, paired with a closing on
    the regular service for the same date.
    """

    venue: str = Field(description="Venue key, matching a 'key' in venues.json.")
    name: str = Field(description="Service name.", max_length=120)
    description: str | None = Field(
        default=None, description="Service description.", max_length=1000
    )
    capacity: int = Field(description="Seats bookable on any date the service runs.", gt=0)
    dates: DemoDateRange | None = Field(
        default=None,
        description="When the service runs. Omit to run it indefinitely from a year ago.",
    )
    openings: list[DemoOpening] = Field(
        default_factory=list,
        description="Weekly opening hours (open days) for this service.",
    )
    deleted: bool = Field(
        default=False,
        description="Delete the service once the demo bookings exist, leaving those bookings on "
                    "a deleted service that staff must resolve.",
    )


class DemoServices(BaseModel):
    """Top-level schema of ``services.json``."""

    services: list[DemoService] = Field(default_factory=list)


class DemoReservation(BaseModel):
    """A demo booking to create through the reservation API (``reservations.json``)."""

    venue: str = Field(description="Venue key, matching a 'key' in venues.json.")
    service: str = Field(description="Service name, matching a service in services.json.")
    dates: DemoDateRange = Field(
        description="When the booking occurs. A booking is a single day, so "
                    "``month_day_start`` and ``month_day_end`` are the same value.",
    )
    time: str = Field(description="Booking time, 'HH:MM'. Must fall inside the service window.")
    party_size: int = Field(description="Number of people.", gt=0)
    contact_name: str = Field(description="Name of the customer.")
    contact_phone_number: str | None = Field(default=None, description="Customer phone number.")
    contact_email: str | None = Field(default=None, description="Customer email.")
    notes: str | None = Field(default=None, description="Staff notes for the booking.")
    status: str | None = Field(
        default=None,
        description="Optional follow-up action applied after creation: 'confirmed', 'rejected' "
                    "or 'canceled'. Check-in and no-show are not available — a future booking "
                    "cannot already have arrived. Omit to leave the booking pending.",
    )


class DemoReservations(BaseModel):
    """Top-level schema of ``reservations.json``."""

    reservations: list[DemoReservation] = Field(default_factory=list)


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
