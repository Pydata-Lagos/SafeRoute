import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, CreatedAtMixin, generate_uuid
from app.models.enums import MediaType


if TYPE_CHECKING:
    from app.models.report import Report


class Media(Base, CreatedAtMixin):
    __tablename__ = "media"
    __table_args__ = {"schema": "safe_route"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=generate_uuid
    )
    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("safe_route.report.id"), nullable=False
    )
    type: Mapped[MediaType] = mapped_column(nullable=False)
    media_link: Mapped[String] = mapped_column(String, nullable=False)

    # Relationships
    report: Mapped["Report"] = relationship(back_populates="media")

    def __repr__(self) -> str:
        return f"<Media {self.type.value}:{self.id}>"
