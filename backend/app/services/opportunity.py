from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.opportunity import OpportunityRepository
from app.schemas.opportunity import OpportunityRead


class OpportunityService:
    def __init__(self, repository: OpportunityRepository | None = None) -> None:
        self._repository = repository or OpportunityRepository()

    async def list(self, session: AsyncSession) -> list[OpportunityRead]:
        items = await self._repository.list(session)
        return [OpportunityRead.model_validate(item) for item in items]

    async def get(self, session: AsyncSession, opportunity_id: UUID) -> OpportunityRead | None:
        item = await self._repository.get(session, opportunity_id)
        return OpportunityRead.model_validate(item) if item else None
