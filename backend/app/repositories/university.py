from __future__ import annotations

from sqlalchemy import or_, select, cast, Text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.entities import University


class UniversityRepository:
    async def search(self, session: AsyncSession, query: str, limit: int = 5) -> list[University]:
        if not query.strip():
            return []

        pattern = f"%{query.strip()}%"
        result = await session.execute(
            select(University).where(
                or_(
                    University.name.ilike(pattern),
                    University.country.ilike(pattern),
                    University.description.ilike(pattern),
                    cast(University.metadata_json, Text).ilike(pattern),
                )
            ).limit(limit)
        )
        return list(result.scalars().all())
