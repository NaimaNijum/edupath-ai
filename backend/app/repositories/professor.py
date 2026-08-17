from __future__ import annotations

from sqlalchemy import or_, select, cast, Text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.search import extract_keywords
from app.database.models.entities import Professor


class ProfessorRepository:
    async def search(self, session: AsyncSession, query: str, limit: int = 5) -> list[Professor]:
        keywords = extract_keywords(query)
        if not keywords:
            return []

        conditions = [
            or_(
                Professor.name.ilike(f"%{keyword}%"),
                Professor.university.ilike(f"%{keyword}%"),
                Professor.department.ilike(f"%{keyword}%"),
                cast(Professor.research_interests, Text).ilike(f"%{keyword}%"),
                cast(Professor.publications, Text).ilike(f"%{keyword}%"),
            )
            for keyword in keywords
        ]
        result = await session.execute(select(Professor).where(or_(*conditions)).limit(limit))
        return list(result.scalars().all())
