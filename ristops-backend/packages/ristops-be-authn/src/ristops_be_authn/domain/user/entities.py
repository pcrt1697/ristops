from datetime import datetime
from uuid import uuid4, UUID

from sqlalchemy import String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from ristops_be_authn.database import Base


class UserEntity(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    username: Mapped[str] = mapped_column(
        String(30),
        unique=True,
    )
    display_name: Mapped[str | None] = mapped_column(
        String(60),
        index=True,
    )
    email: Mapped[str] = mapped_column(
        String(320),
        unique=True,
    )
    password: Mapped[str] = mapped_column(
        String(255),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
