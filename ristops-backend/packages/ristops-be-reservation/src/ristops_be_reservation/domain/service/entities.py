from datetime import datetime, time, date
from uuid import UUID, uuid4

from sqlalchemy import DateTime, func, String, Integer, Time, Date, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from ristops_be_reservation.database import Base, SCHEMA_NAME, make_table_args


class ServiceEntity(Base):
    """SQLAlchemy entity for a service: what a venue offers over a validity period, with the
    seats it can take. Its hours live in `OpeningEntity`, one row per weekday."""

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
    date_from: Mapped[date] = mapped_column(
        Date(),
        index=True,
        doc="First date the service runs on (inclusive)",
    )
    date_to: Mapped[date | None] = mapped_column(
        Date(),
        default=None,
        index=True,
        doc="Last date the service runs on (inclusive); null runs it indefinitely",
    )
    capacity: Mapped[int] = mapped_column(
        Integer,
        doc="Maximum number of seats bookable on any date the service runs",
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


class OpeningEntity(Base):
    """SQLAlchemy entity for a service opening: the hours a service runs on one weekday. An
    opening whose ``end_time`` is not after its ``start_time`` runs overnight and closes on the
    following calendar day."""

    __tablename__ = "openings"
    __table_args__ = make_table_args(
        UniqueConstraint("service_id", "weekday", name="uq_opening_service_weekday"),
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
    weekday: Mapped[str] = mapped_column(
        String(9),
        doc="Day of the week this opening applies to; validated as an enum at the API layer, stored as plain text",
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


class ClosingEntity(Base):
    """SQLAlchemy entity for a closing: a date range over which the linked services do not run.

    A closing is venue-scoped and targets one or more services through `ClosingServiceEntity`;
    a venue-wide shutdown is a closing linked to every service.
    """

    __tablename__ = "closings"

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
    date_from: Mapped[date] = mapped_column(
        Date(),
        index=True,
        doc="First date of the closing period (inclusive)",
    )
    date_to: Mapped[date] = mapped_column(
        Date(),
        index=True,
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


class ClosingServiceEntity(Base):
    """SQLAlchemy entity linking a closing to one of the services it closes."""

    __tablename__ = "closing_services"

    closing_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA_NAME}.closings.id", ondelete="CASCADE"),
        primary_key=True,
        doc="Identifier of the closing",
    )
    service_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA_NAME}.services.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
        doc="Identifier of the service the closing applies to",
    )
