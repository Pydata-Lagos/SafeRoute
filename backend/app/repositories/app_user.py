from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.app_user import AppUser
from app.repositories.base import BaseRepository


class AppUserRepository(BaseRepository[AppUser]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(AppUser, session)

    async def get_by_email(self, email: str) -> AppUser | None:
        stmt = select(AppUser).where(AppUser.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_users(self) -> list[AppUser]:
        stmt = select(AppUser).where(AppUser.is_active.is_(True))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def deactivate(self, user: AppUser) -> AppUser:
        """
        Soft-deactivate a user. Never hard-delete.
        FKs in report and audit log depend on this row.
        """
        return await self.update(user, is_active=False)
