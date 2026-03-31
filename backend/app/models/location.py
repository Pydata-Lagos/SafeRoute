import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, CreatedAtMixin, generate_uuid

if TYPE_CHECKING:
    from app.models.report import Report


class Location(Base, CreatedAtMixin):
    __tablename__ = "location"
    __table_args__ = {"schema": "safe_route"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=generate_uuid
    )
    state: Mapped[str] = mapped_column(String, nullable=False)
    city: Mapped[str] = mapped_column(String, nullable=False)
    town: Mapped[str | None] = mapped_column(String, nullable=True)

    # relationships
    reports: Mapped[list["Report"]] = relationship(back_populates="location")

    def __repr__(self) -> str:
        return f"<Location {self.state}/{self.city}"
