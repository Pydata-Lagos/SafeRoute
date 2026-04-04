import secrets
import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import ReportStatus, SeverityLevel
from app.models.report import Report
from app.repositories.base import BaseRepository


def _generate_reference_no() -> str:
    """
    Generate a crytpographically secure reference number.
    Format: SR-xxxxxxxxx
    """
    return f"SR-{secrets.token_urlsafe(8)[:10]}"


class ReportRepository(BaseRepository[Report]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Report, session)

    async def create(self, **kwargs) -> Report:
        """Override create to auto-generate reference_no."""
        if "reference_no" not in kwargs:
            kwargs["reference_no"] = _generate_reference_no()
        return await super().create(**kwargs)

    async def get_by_reference_no(self, reference_no: str) -> Report | None:
        """
        Look up a report by its public reference number.
        Used by the tracking endpoint.
        """
        stmt = select(Report).where(
            Report.reference_no == reference_no,
            Report.is_deleted.is_(False),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_reports(
        self,
        *,
        status: ReportStatus | None = None,
        severity: SeverityLevel | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> Sequence[Report]:
        """Fetch non-deleted reports with optional status and severity filters"""
        stmt = select(Report).where(Report.is_deleted.is_(False))

        if status is not None:
            stmt = stmt.where(Report.status == status)

        if severity is not None:
            stmt = stmt.where(Report.severity == severity)

        stmt = stmt.order_by(Report.created_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def soft_delete(self, report: Report) -> Report:
        """
        Mark a report as deleted. Never hard-delete.
        Audit log entries reference this row
        """
        return await self.update(report, is_deleted=True)

    async def get_by_location(self, location_id: uuid.UUID) -> Sequence[Report]:
        stmt = select(Report).where(
            Report.location_id == location_id, Report.is_deleted._is(False)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
