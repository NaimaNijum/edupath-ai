from __future__ import annotations

from sqlalchemy import or_, select, cast, Text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.search import extract_keywords
from app.database.models.entities import University


class UniversityRepository:
    async def search(self, session: AsyncSession, query: str, limit: int = 5) -> list[University]:
        keywords = extract_keywords(query)
        if not keywords:
            return []

        conditions = [
            or_(
                University.name.ilike(f"%{keyword}%"),
                University.country.ilike(f"%{keyword}%"),
                University.description.ilike(f"%{keyword}%"),
                cast(University.metadata_json, Text).ilike(f"%{keyword}%"),
            )
            for keyword in keywords
        ]
        result = await session.execute(select(University).where(or_(*conditions)).limit(limit))
        return list(result.scalars().all())

    async def upsert_by_name(
        self, session: AsyncSession, *, name: str, country: str | None, website_url: str | None, description: str | None
    ) -> University:
        """Used by CatalogSyncService to persist universities discovered
        during a workflow run, so the Catalog reflects what Discover found."""
        existing = await session.scalar(select(University).where(University.name == name))
        if existing is not None:
            existing.country = country or existing.country
            existing.website_url = website_url or existing.website_url
            existing.description = description or existing.description
            return existing

        university = University(name=name, country=country, website_url=website_url, description=description)
        session.add(university)
        return university
