from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.entities import Opportunity


class OpportunityRepository:
    async def list(self, session: AsyncSession) -> list[Opportunity]:
        result = await session.execute(select(Opportunity).order_by(Opportunity.created_at.desc()))
        return list(result.scalars().all())

    async def get(self, session: AsyncSession, opportunity_id: UUID) -> Opportunity | None:
        return await session.get(Opportunity, opportunity_id)

    async def upsert_by_title(
        self,
        session: AsyncSession,
        *,
        title: str,
        university: str | None,
        degree_level: str | None,
        country: str | None,
        field: str | None,
        funding_type: str | None,
        deadline,
        application_url: str | None,
        description: str | None,
    ) -> Opportunity:
        """Used by CatalogSyncService to persist opportunities discovered
        during a workflow run, so the Catalog reflects what Discover found."""
        existing = await session.scalar(select(Opportunity).where(Opportunity.title == title))
        if existing is not None:
            existing.university = university or existing.university
            existing.degree_level = degree_level or existing.degree_level
            existing.country = country or existing.country
            existing.field = field or existing.field
            existing.funding_type = funding_type or existing.funding_type
            existing.deadline = deadline or existing.deadline
            existing.application_url = application_url or existing.application_url
            existing.description = description or existing.description
            return existing

        opportunity = Opportunity(
            title=title, university=university, degree_level=degree_level, country=country,
            field=field, funding_type=funding_type, deadline=deadline,
            application_url=application_url, source_url=application_url, description=description,
        )
        session.add(opportunity)
        return opportunity
