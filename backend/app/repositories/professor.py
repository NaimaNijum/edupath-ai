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

    async def upsert_by_name_and_university(
        self,
        session: AsyncSession,
        *,
        name: str,
        university: str | None,
        research_interests: list[str],
        profile_url: str | None,
    ) -> Professor:
        """Used by CatalogSyncService to persist professors discovered
        during a workflow run (e.g. via the faculty directory finder), so
        the Catalog reflects what Discover found. Never writes an email --
        that field is left null unless a future, higher-confidence source
        is added, per the project's anti-hallucination stance on contact info."""
        existing = await session.scalar(
            select(Professor).where(Professor.name == name, Professor.university == university)
        )
        if existing is not None:
            if research_interests:
                existing.research_interests = sorted(set(existing.research_interests) | set(research_interests))
            existing.profile_url = profile_url or existing.profile_url
            return existing

        professor = Professor(name=name, university=university, research_interests=research_interests, profile_url=profile_url)
        session.add(professor)
        return professor
