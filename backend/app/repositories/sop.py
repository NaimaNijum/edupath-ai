from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.entities import SOPDocument


class SOPRepository:
    async def create(self, session: AsyncSession, sop: SOPDocument) -> SOPDocument:
        session.add(sop)
        await session.commit()
        await session.refresh(sop)
        return sop

    async def update(self, session: AsyncSession, sop: SOPDocument) -> SOPDocument:
        await session.commit()
        await session.refresh(sop)
        return sop

    async def get(self, session: AsyncSession, sop_id: UUID) -> SOPDocument | None:
        return await session.get(SOPDocument, sop_id)

    async def list_for_profile(self, session: AsyncSession, profile_id: UUID) -> list[SOPDocument]:
        result = await session.execute(
            select(SOPDocument).where(SOPDocument.profile_id == profile_id).order_by(SOPDocument.updated_at.desc())
        )
        return list(result.scalars().all())
