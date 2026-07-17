from datetime import datetime, date
from uuid import UUID, uuid4

from sqlalchemy import DateTime, func, String, Integer, Date, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from ristops_be_reservation.database import Base, SCHEMA_NAME, make_table_args


class ServiceEntity(Base):
    """SQLAlchemy entity for a service."""

    __tablename__ = "services"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    venue_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA_NAME}.venues.id", ondelete="RESTRICT"),
        index=True,
        doc="Identifier of the venue this service belongs to",
    )
    name: Mapped[str] = mapped_column(
        String(120),
        index=True,
        doc="Name of the service",
    )
    turn_time_m: Mapped[int] = mapped_column(
        Integer,
        doc="Reservation duration, in minutes",
    )
    advance_notice_m: Mapped[int] = mapped_column(
        Integer,
        doc="Minimum notice required before a reservation slot, in minutes",
    )
    slot_interval_m: Mapped[int] = mapped_column(
        Integer,
        doc="Interval between reservation slots, in minutes",
    )
    grace_period_m: Mapped[int] = mapped_column(
        Integer,
        doc="Minutes past a reservation's start time before it may be marked as a no-show",
    )
    description: Mapped[str | None] = mapped_column(
        String(1000),
        doc="Description of the service",
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=None,
        doc="When the service was soft-deleted; null while active",
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


class ServiceOccurrenceEntity(Base):
    """SQLAlchemy entity for a service occurrence."""

    __tablename__ = "service_occurrences"
    __table_args__ = make_table_args(
        UniqueConstraint("service_id", "date", name="uq_service_occurrence_service_date"),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    service_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA_NAME}.services.id", ondelete="CASCADE"),
        index=True,
        doc="Identifier of the service this occurrence belongs to",
    )
    date: Mapped[date] = mapped_column(
        Date(),
        doc="Venue-local calendar date this occurrence belongs to",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        doc="Occurrence status; validated as an enum at the API layer, stored as plain text",
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        doc="When the occurrence was opened",
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        doc="When the occurrence was closed",
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
