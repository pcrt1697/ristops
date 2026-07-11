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


class DemoVenues(BaseModel):
    """Top-level schema of ``venues.json``."""

    venues: list[DemoVenue] = Field(default_factory=list)


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
