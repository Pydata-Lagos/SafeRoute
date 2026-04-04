from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.location import Location
from app.repositories.base import BaseRepository


class LocationRepository(BaseRepository[Location]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Location, session)

    async def find_or_create(
        self, state: str, city: str, town: str | None = None
    ) -> Location:
        """
        Look up an existing location by exact match. If none exists, create one.
        This prevents duplicate location rows for the same state/city/town combination.
        """
        stmt = select(Location).where(
            Location.state == state, Location.city == city, Location.town == town
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is not None:
            return existing

        return await self.create(state=state, city=city, town=town)
