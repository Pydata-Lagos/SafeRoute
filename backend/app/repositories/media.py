import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.media import Media
from app.repositories.base import BaseRepository


class MediaRepository(BaseRepository[Media]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Media, session)

    async def get_by_report_id(self, report_id: uuid.UUID) -> Sequence[Media]:
        stmt = select(Media).where(Media.report_id == report_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
