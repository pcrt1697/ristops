from datetime import datetime, time, date
from uuid import UUID, uuid4

from sqlalchemy import DateTime, func, String, Integer, Time, Date, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from ristops_be_reservation.database import Base, SCHEMA_NAME, make_table_args


class OpeningEntity(Base):
    """SQLAlchemy entity for service openings."""

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


class OpeningOverrideEntity(Base):
    """SQLAlchemy entity for service opening overrides."""

    __tablename__ = "opening_overrides"

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
    weekday: Mapped[str | None] = mapped_column(
        String(9),
        doc="Weekday this override applies to within the range; null means every day in the range",
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
    weekday: Mapped[str | None] = mapped_column(
        String(9),
        doc="Weekday this closing applies to within the range; null means every day in the range",
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


class CapacityOverrideEntity(Base):
    """SQLAlchemy entity for service capacity overrides: a seat-count delta applied on top of
    the resolved hours/capacity for a date range (e.g. a summer garden adding seats), without
    touching opening hours."""

    __tablename__ = "capacity_overrides"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    service_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA_NAME}.services.id", ondelete="CASCADE"),
        index=True,
        doc="Identifier of the service this capacity override belongs to",
    )
    date_start: Mapped[date] = mapped_column(
        Date(),
        doc="First date of the capacity override period (inclusive)",
    )
    date_end: Mapped[date] = mapped_column(
        Date(),
        doc="Last date of the capacity override period (inclusive)",
    )
    weekday: Mapped[str | None] = mapped_column(
        String(9),
        doc="Weekday this override applies to within the range; null means every day in the range",
    )
    capacity_delta: Mapped[int] = mapped_column(
        Integer,
        doc="Signed change to the resolved seat count (e.g. +30 for a garden, -10 for a partial closure)",
    )
    description: Mapped[str | None] = mapped_column(
        String(1000),
        doc="Description of this capacity override",
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
