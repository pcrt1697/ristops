from datetime import datetime, date
from uuid import UUID, uuid4

from sqlalchemy import DateTime, func, Text, String, ForeignKey, Date
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from ristops_be_reservation.database import Base, SCHEMA_NAME


class VenueEntity(Base):
    """SQLAlchemy entity for the local venue read-model, replicated from be-venue."""

    __tablename__ = "venues"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
    )
    timezone: Mapped[str] = mapped_column(
        Text(),
        doc="IANA timezone name of the venue",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        doc="Venue status; validated as an enum at the API layer, stored as plain text",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class VenueClosingEntity(Base):
    """SQLAlchemy entity for venue-wide closings: closes every service of a venue for a date
    range (e.g. a renovation week or seasonal shutdown), independent of per-service closings."""

    __tablename__ = "venue_closings"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    venue_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA_NAME}.venues.id", ondelete="CASCADE"),
        index=True,
        doc="Identifier of the venue this closing belongs to",
    )
    date_start: Mapped[date] = mapped_column(
        Date(),
        doc="First date of the closing period (inclusive)",
    )
    date_end: Mapped[date] = mapped_column(
        Date(),
        doc="Last date of the closing period (inclusive)",
    )
    weekday: Mapped[str | None] = mapped_column(
        String(9),
        doc="Weekday this closing applies to within the range; null means every day in the range",
    )
    description: Mapped[str | None] = mapped_column(
        String(1000),
        doc="Description of this venue closing",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
