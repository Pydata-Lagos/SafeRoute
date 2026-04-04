import uuid
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


class TimestampMixin:
    """Mixin that adds created_at and updated_at columns."""

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )


class CreatedAtMixin:
    """Mixin that adds only a created_at column, for immutable tables."""

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )


def generate_uuid() -> uuid.UUID:
    return uuid.uuid4()
