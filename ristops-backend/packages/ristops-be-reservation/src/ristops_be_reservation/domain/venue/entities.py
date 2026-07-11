from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, func, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from ristops_be_reservation.database import Base


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
    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        doc="Whether the venue is active; false once be-venue reports it deleted",
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
