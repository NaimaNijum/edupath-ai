from __future__ import annotations

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
