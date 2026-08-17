from __future__ import annotations

from sqlalchemy import or_, select, cast, Text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.entities import Professor


class ProfessorRepository:
    async def search(self, session: AsyncSession, query: str, limit: int = 5) -> list[Professor]:
        if not query.strip():
            return []

        pattern = f"%{query.strip()}%"
        result = await session.execute(
            select(Professor).where(
                or_(
                    Professor.name.ilike(pattern),
                    Professor.university.ilike(pattern),
                    Professor.department.ilike(pattern),
                    cast(Professor.research_interests, Text).ilike(pattern),
                    cast(Professor.publications, Text).ilike(pattern),
                )
            ).limit(limit)
        )
        return list(result.scalars().all())
