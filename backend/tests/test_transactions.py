from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import (
    ActorType,
    AuditAction,
    ReportStatus,
    SeverityLevel,
)
from app.models.location import Location
from app.models.report import Report
from app.repositories import (
    ReportRepository,
    ReportAuditLogRepository,
)


class TestTransactionalConsistency:
    """
    Verify that report mutations and audit log entries
    share the same session and can be committed atomically.
    """

    async def test_report_and_audit_share_session(
        self,
        session: AsyncSession,
        report_repo: ReportRepository,
        audit_log_repo: ReportAuditLogRepository,
        sample_report: Report,
    ):
        """Both repos use the same session — changes are visible to each other."""
        old_status = sample_report.status.value

        await report_repo.update(sample_report, status=ReportStatus.UNDER_REVIEW)

        await audit_log_repo.create(
            report_id=sample_report.id,
            action=AuditAction.STATUS_CHANGED,
            actor_type=ActorType.USER,
            old_value=old_status,
            new_value=ReportStatus.UNDER_REVIEW.value,
        )

        # Both changes are in the same session
        entries = await audit_log_repo.get_by_report_id(sample_report.id)
        assert len(entries) == 1
        assert entries[0].old_value == "pending"
        assert entries[0].new_value == "under_review"
        assert sample_report.status == ReportStatus.UNDER_REVIEW

    async def test_severity_change_logged(
        self,
        report_repo: ReportRepository,
        audit_log_repo: ReportAuditLogRepository,
        sample_report: Report,
        sample_user,
    ):
        """Severity escalation produces the correct audit entry."""
        old_severity = sample_report.severity.value

        await report_repo.update(sample_report, severity=SeverityLevel.HIGH)

        await audit_log_repo.create(
            report_id=sample_report.id,
            actor_id=sample_user.id,
            actor_type=ActorType.USER,
            action=AuditAction.SEVERITY_CHANGED,
            old_value=old_severity,
            new_value=SeverityLevel.HIGH.value,
            note="Escalated based on witness corroboration",
        )

        entries = await audit_log_repo.get_by_report_id(sample_report.id)
        assert len(entries) == 1
        assert entries[0].old_value == "low"
        assert entries[0].new_value == "high"
        assert entries[0].note == "Escalated based on witness corroboration"

    async def test_full_report_lifecycle(
        self,
        report_repo: ReportRepository,
        audit_log_repo: ReportAuditLogRepository,
        sample_location: Location,
        sample_user,
    ):
        """
        Simulate a complete report lifecycle:
        create → under_review → approved → resolved.
        Each transition produces an audit entry.
        """
        # 1. Anonymous creation
        report = await report_repo.create(
            location_id=sample_location.id,
            description="Lifecycle test",
            incident_at=datetime(2026, 3, 15, tzinfo=timezone.utc),
        )
        await audit_log_repo.create(
            report_id=report.id,
            action=AuditAction.CREATED,
            actor_type=ActorType.ANONYMOUS,
        )

        # 2. Reviewer picks it up
        await report_repo.update(report, status=ReportStatus.UNDER_REVIEW)
        await audit_log_repo.create(
            report_id=report.id,
            actor_id=sample_user.id,
            actor_type=ActorType.USER,
            action=AuditAction.STATUS_CHANGED,
            old_value="pending",
            new_value="under_review",
        )

        # 3. Reviewer approves
        await report_repo.update(
            report,
            status=ReportStatus.APPROVED,
            approver_id=sample_user.id,
        )
        await audit_log_repo.create(
            report_id=report.id,
            actor_id=sample_user.id,
            actor_type=ActorType.USER,
            action=AuditAction.APPROVED,
            old_value="under_review",
            new_value="approved",
        )

        # 4. Resolved
        await report_repo.update(report, status=ReportStatus.RESOLVED)
        await audit_log_repo.create(
            report_id=report.id,
            actor_id=sample_user.id,
            actor_type=ActorType.USER,
            action=AuditAction.STATUS_CHANGED,
            old_value="approved",
            new_value="resolved",
        )

        # Verify final state
        assert report.status == ReportStatus.RESOLVED
        assert report.approver_id == sample_user.id

        # Verify complete audit trail
        entries = await audit_log_repo.get_by_report_id(report.id)
        assert len(entries) == 4

        actions = [e.action for e in entries]
        assert AuditAction.CREATED in actions
        assert AuditAction.APPROVED in actions
        assert actions.count(AuditAction.STATUS_CHANGED) == 2
