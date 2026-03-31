import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, ForeignKey, Index, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import generate_uuid, Base, TimestampMixin
from app.models.enums import ReportStatus, SeverityLevel, ReportType


if TYPE_CHECKING:
    from app.models.app_user import AppUser
    from app.models.location import Location
    from app.models.media import Media
    from app.models.report_audit_log import ReportAuditLog


class Report(Base, TimestampMixin):
    __tablename__ = "report"
    __table_args__ = (
        Index("idx_report_reporter_id", "reporter_id"),
        Index("idx_report_location_id", "location_id"),
        Index("idx_report_status", "status"),
        Index("idx_report_severity", "severity"),
        Index("idx_report_incident_at", "incident_at"),
        Index("idx_report_reference_no", "reference_no"),
        {"schema": "safe_route"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=generate_uuid
    )
    reporter_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("safe_route.app_user.id"), nullable=True
    )
    location_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("safe_route.location.id"), nullable=False
    )
    approver_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("safe_route.app_user.id"), nullable=True
    )
    reference_no: Mapped[str] = mapped_column(String(12), nullable=False, unique=True)
    status: Mapped[ReportStatus] = mapped_column(
        nullable=False, default=ReportStatus.PENDING
    )
    # TODO: add report enum type
    report_type: Mapped[ReportType] = mapped_column(
        nullable=False, default=ReportType.OTHER
    )
    severity: Mapped[SeverityLevel] = mapped_column(
        nullable=False, default=SeverityLevel.LOW
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    incident_at: Mapped[datetime] = mapped_column(nullable=False)
    approval_date: Mapped[datetime | None] = mapped_column(nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relationships
    reporter: Mapped["AppUser | None"] = relationship(
        back_populates="submitted_reports",
        foreign_keys=[reporter_id],
    )
    approver: Mapped["AppUser | None"] = relationship(
        back_populates="approved_reports", foreign_keys=[approver_id]
    )
    location: Mapped["Location"] = relationship(back_populates="reports")
    media: Mapped[list["Media"]] = relationship(back_populates="report")
    audit_logs: Mapped[list["ReportAuditLog"]] = relationship(back_populates="report")

    def __repr__(self) -> str:
        return f"<Report {self.reference_no}>"
