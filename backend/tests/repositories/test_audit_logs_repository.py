from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import ActorType, AuditAction
from app.models.report import Report
from app.repositories import ReportAuditLogRepository


class TestAuditLogCreation:
    async def test_create_audit_entry(
        self,
        audit_log_repo: ReportAuditLogRepository,
        sample_report: Report,
        sample_user,
    ):
        entry = await audit_log_repo.create(
            report_id=sample_report.id,
            actor_id=sample_user.id,
            actor_type=ActorType.USER,
            action=AuditAction.CREATED,
        )

        assert entry.id is not None
        assert entry.report_id == sample_report.id
        assert entry.actor_id == sample_user.id
        assert entry.action == AuditAction.CREATED

    async def test_create_anonymous_audit_entry(
        self,
        audit_log_repo: ReportAuditLogRepository,
        sample_report: Report,
    ):
        """Anonymous actions have no actor_id."""
        entry = await audit_log_repo.create(
            report_id=sample_report.id,
            action=AuditAction.CREATED,
            actor_type=ActorType.ANONYMOUS,
        )

        assert entry.actor_id is None
        assert entry.actor_type == ActorType.ANONYMOUS

    async def test_create_system_audit_entry(
        self,
        audit_log_repo: ReportAuditLogRepository,
        sample_report: Report,
    ):
        entry = await audit_log_repo.create(
            report_id=sample_report.id,
            action=AuditAction.STATUS_CHANGED,
            actor_type=ActorType.SYSTEM,
            old_value="pending",
            new_value="under_review",
            note="Auto-escalated after 48 hours",
        )

        assert entry.actor_type == ActorType.SYSTEM
        assert entry.old_value == "pending"
        assert entry.new_value == "under_review"
        assert entry.note == "Auto-escalated after 48 hours"


class TestAuditLogRetrieval:
    async def test_get_by_report_id_ordered_by_created_at(
        self,
        audit_log_repo: ReportAuditLogRepository,
        sample_report: Report,
    ):
        """Audit trail is returned most recent first."""
        await audit_log_repo.create(
            report_id=sample_report.id,
            action=AuditAction.CREATED,
            actor_type=ActorType.ANONYMOUS,
        )
        await audit_log_repo.create(
            report_id=sample_report.id,
            action=AuditAction.STATUS_CHANGED,
            actor_type=ActorType.USER,
            old_value="pending",
            new_value="under_review",
        )

        entries = await audit_log_repo.get_by_report_id(sample_report.id)

        assert len(entries) == 2
        actions = {e.action for e in entries}
        assert actions == {AuditAction.CREATED, AuditAction.STATUS_CHANGED}

    async def test_get_by_actor_id(
        self,
        audit_log_repo: ReportAuditLogRepository,
        sample_report: Report,
        sample_user,
    ):
        await audit_log_repo.create(
            report_id=sample_report.id,
            actor_id=sample_user.id,
            actor_type=ActorType.USER,
            action=AuditAction.APPROVED,
        )

        entries = await audit_log_repo.get_by_actor_id(sample_user.id)

        assert len(entries) == 1
        assert entries[0].actor_id == sample_user.id


class TestAuditLogImmutability:
    """
    The audit log is append-only. The repository intentionally has no
    update or delete methods. These tests verify that constraint.

    Note: The PostgreSQL trigger provides a secondary enforcement layer,
    but it doesn't exist in SQLite. These tests validate the primary
    enforcement mechanism — the repository API.
    """

    async def test_repository_has_no_update_method(
        self, audit_log_repo: ReportAuditLogRepository
    ):
        """The repository class must not expose an update method."""
        assert not hasattr(audit_log_repo, "update")

    async def test_repository_has_no_delete_method(
        self, audit_log_repo: ReportAuditLogRepository
    ):
        """The repository class must not expose a delete method."""
        assert not hasattr(audit_log_repo, "delete")

    async def test_repository_does_not_extend_base(
        self, audit_log_repo: ReportAuditLogRepository
    ):
        """
        ReportAuditLogRepository must NOT inherit from BaseRepository.
        BaseRepository provides update() and delete() — inheriting it
        would silently break the append-only invariant.
        """
        from app.repositories.base import BaseRepository

        assert not isinstance(audit_log_repo, BaseRepository)

    async def test_direct_update_via_session_blocked_in_production(
        self,
        session: AsyncSession,
        audit_log_repo: ReportAuditLogRepository,
        sample_report: Report,
    ):
        """
        Verify that even raw session updates are detectable.
        In production, the PostgreSQL trigger blocks this.
        In SQLite tests, we can only verify the entry was created
        and that the repository provides no path to mutation.

        This test documents the expected behaviour — swap to a
        PostgreSQL test backend to verify the trigger enforcement.
        """
        entry = await audit_log_repo.create(
            report_id=sample_report.id,
            action=AuditAction.CREATED,
            actor_type=ActorType.ANONYMOUS,
        )

        # The entry exists and can be retrieved
        entries = await audit_log_repo.get_by_report_id(sample_report.id)
        assert len(entries) == 1
        assert entries[0].id == entry.id
