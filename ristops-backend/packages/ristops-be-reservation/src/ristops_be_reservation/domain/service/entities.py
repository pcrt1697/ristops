from datetime import datetime, time, date
from uuid import UUID, uuid4

from sqlalchemy import DateTime, func, String, Integer, Time, Enum, Date, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from ristops_be_reservation.database import Base, SCHEMA_NAME, make_table_args
from ristops_be_reservation.domain.models import Weekday


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


class ServiceOpeningEntity(Base):
    """SQLAlchemy entity for service openings."""

    __tablename__ = "service_openings"
    __table_args__ = make_table_args(
        UniqueConstraint("service_id", "weekday", name="uq_service_opening_service_weekday"),
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
        doc="Identifier of the service this opening belongs to",
    )
    weekday: Mapped[Weekday] = mapped_column(
        Enum(Weekday),
        doc="Day of the week this opening applies to",
    )
    capacity: Mapped[int] = mapped_column(
        Integer,
        doc="Maximum number of reservable seats",
    )
    start_time: Mapped[time] = mapped_column(
        Time,
        doc="Time the service opens",
    )
    end_time: Mapped[time] = mapped_column(
        Time,
        doc="Time the service closes",
    )
    description: Mapped[str | None] = mapped_column(
        String(1000),
        doc="Description of this opening",
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


class ServiceOpeningOverrideEntity(Base):
    """SQLAlchemy entity for service opening overrides."""

    __tablename__ = "service_opening_overrides"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    service_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA_NAME}.services.id", ondelete="CASCADE"),
        index=True,
        doc="Identifier of the service this override belongs to",
    )
    date_start: Mapped[date] = mapped_column(
        Date(),
        doc="First date of the override period (inclusive)",
    )
    date_end: Mapped[date] = mapped_column(
        Date(),
        doc="Last date of the override period (inclusive)",
    )
    capacity: Mapped[int] = mapped_column(
        Integer,
        doc="Overridden maximum number of reservable seats",
    )
    start_time: Mapped[time] = mapped_column(
        Time,
        doc="Overridden opening time",
    )
    end_time: Mapped[time] = mapped_column(
        Time,
        doc="Overridden closing time",
    )
    description: Mapped[str | None] = mapped_column(
        String(1000),
        doc="Description of this override",
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


class ServiceClosingEntity(Base):
    """SQLAlchemy entity for service closings."""

    __tablename__ = "service_closings"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    service_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA_NAME}.services.id", ondelete="CASCADE"),
        index=True,
        doc="Identifier of the service this closing belongs to",
    )
    date_start: Mapped[date] = mapped_column(
        Date(),
        doc="First date of the closing period (inclusive)",
    )
    date_end: Mapped[date] = mapped_column(
        Date(),
        doc="Last date of the closing period (inclusive)",
    )
    description: Mapped[str | None] = mapped_column(
        String(1000),
        doc="Description of this closing",
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
