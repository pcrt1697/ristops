from datetime import datetime
from uuid import uuid4, UUID

from sqlalchemy import String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from ristops_be_venue.database import Base


class VenueEntity(Base):
    """SQLAlchemy entity for a venue."""

    __tablename__ = "venues"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(120),
    )
    address: Mapped[str] = mapped_column(
        String(255),
    )
    description: Mapped[str | None] = mapped_column(
        String(1000),
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
