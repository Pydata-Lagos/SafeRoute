import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.enums import ActorType, AuditAction
from app.models.base import Base, CreatedAtMixin, generate_uuid

if TYPE_CHECKING:
    from app.models.report import Report
    from app.models.app_user import AppUser


class ReportAuditLog(Base, CreatedAtMixin):
    __tablename__ = "report_audit_log"
    __table_args__ = (
        Index("idx_audit_log_report_id", "report_id"),
        Index("idx_audit_log_actor_id", "actor_id"),
        Index("idx_audit_log_created_at", "created_at"),
        {"schema": "safe_route"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=generate_uuid
    )
    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("safe_route.report.id"), nullable=False
    )
    actor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("safe_route.app_user.id"), nullable=True
    )
    actor_type: Mapped[ActorType] = mapped_column(
        nullable=False, default=ActorType.USER
    )
    action: Mapped[AuditAction] = mapped_column(nullable=False)
    old_value: Mapped[str] = mapped_column(String, nullable=True)
    new_value: Mapped[str] = mapped_column(String, nullable=True)
    note: Mapped[str] = mapped_column(String, nullable=True)

    # Relationships
    report: Mapped["Report"] = relationship(back_populates="audit_logs")
    actor: Mapped["AppUser | None"] = relationship()

    def __repr__(self) -> str:
        return f"<AuditLog {self.action.value} on {self.report_id}>"
