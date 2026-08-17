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
