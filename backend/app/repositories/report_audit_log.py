import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report_audit_log import ReportAuditLog
from app.models.enums import ActorType, AuditAction
from app.models.base import Base


class ReportAuditLogRepository:
    """
    Append-only repository for the report audit log.

    This class intentionally does NOT extend BaseRepository.
    It exposes only create and read methods. No update. No delete.
    This is the primary enforcement mechanism for audit log immutability.
    The database trigger (see Alembic migration) provides a secondary safeguard.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        report_id: uuid.UUID,
        action: AuditAction,
        actor_id: uuid.UUID | None = None,
        actor_type: ActorType = ActorType.USER,
        old_value: str | None = None,
        new_value: str | None = None,
        note: str | None = None,
    ) -> ReportAuditLog:
        entry = ReportAuditLog(
            report_id=report_id,
            action=action,
            actor_id=actor_id,
            actor_type=actor_type,
            old_value=old_value,
            new_value=new_value,
            note=note,
        )
        self.session.add(entry)
        await self.session.flush()
        return entry

    async def get_by_report_id(self, report_id: uuid.UUID) -> Sequence[ReportAuditLog]:
        """Fetch the full audit trail for a report, most recent first."""
        stmt = (
            select(ReportAuditLog)
            .where(ReportAuditLog.report_id == report_id)
            .order_by(ReportAuditLog.created_at.desc(), ReportAuditLog.id.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_actor_id(self, actor_id: uuid.UUID) -> Sequence[ReportAuditLog]:
        """Fetch the audit trail for a user, most recent first"""
        stmt = (
            select(ReportAuditLog)
            .where(ReportAuditLog.actor_id == actor_id)
            .order_by(ReportAuditLog.created_at.desc(), ReportAuditLog.id.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
