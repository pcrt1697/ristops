from datetime import datetime, time
from uuid import UUID, uuid4

from sqlalchemy import String, Integer, Time, DateTime, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from ristops_be_reservation.database import Base, SCHEMA_NAME


class ReservationEntity(Base):
    """SQLAlchemy entity for a reservation."""

    __tablename__ = "reservations"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    service_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA_NAME}.services.id", ondelete="CASCADE"),
        index=True,
        doc="Identifier of the service this reservation is associated to",
    )
    status: Mapped[str] = mapped_column(
        String(30),
        doc="Status of the reservation",
    )
    contact_name: Mapped[str] = mapped_column(
        String(120),
        doc="Name of the customer",
    )
    contact_phone_number: Mapped[str | None] = mapped_column(
        String(20),
        doc="Phone number of the customer",
    )
    contact_email: Mapped[str | None] = mapped_column(
        String(320),
        doc="Email of the customer",
    )
    party_size: Mapped[int] = mapped_column(
        Integer,
        doc="Number of people",
    )
    arrives_at: Mapped[time] = mapped_column(
        Time,
        doc="Time of arrival",
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
