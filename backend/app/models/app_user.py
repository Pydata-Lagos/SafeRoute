import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, generate_uuid
from app.models.enums import UserRole


if TYPE_CHECKING:
    from app.models.report import Report


class AppUser(TimestampMixin, Base):
    __tablename__ = "app_user"
    __table_args__ = {"schema": "safe_route"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=generate_uuid
    )
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    role: Mapped[UserRole] = mapped_column(nullable=False, default=UserRole.REPORTER)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    submitted_reports: Mapped[list["Report"]] = relationship(
        back_populates="reporter",
        foreign_keys="[Report.reporter_id]",
    )
    approved_reports: Mapped[list["Report"]] = relationship(
        back_populates="approver", foreign_keys="[Report.approver_id]"
    )

    def __repr__(self) -> str:
        return f"<AppUser {self.email}>"
