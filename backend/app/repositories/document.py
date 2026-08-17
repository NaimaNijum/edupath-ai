from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models.entities import Document, DocumentChunk


class DocumentRepository:
    async def create(self, session: AsyncSession, document: Document) -> Document:
        session.add(document)
        await session.commit()
        await session.refresh(document)
        return document

    async def get(self, session: AsyncSession, document_id: UUID) -> Document | None:
        result = await session.execute(
            select(Document).where(Document.id == document_id).options(selectinload(Document.chunks))
        )
        return result.scalar_one_or_none()

    async def list_for_profile(self, session: AsyncSession, profile_id: UUID) -> list[Document]:
        result = await session.execute(
            select(Document)
            .where(Document.profile_id == profile_id)
            .options(selectinload(Document.chunks))
            .order_by(Document.created_at.desc())
        )
        return list(result.scalars().all())

    async def delete(self, session: AsyncSession, document: Document) -> None:
        await session.delete(document)
        await session.commit()

    async def search_similar_chunks(
        self, session: AsyncSession, query_embedding: list[float], *, profile_id: UUID, limit: int = 5
    ) -> list[DocumentChunk]:
        if not query_embedding:
            return []
        result = await session.execute(
            select(DocumentChunk)
            .join(Document, DocumentChunk.document_id == Document.id)
            .where(Document.profile_id == profile_id)
            .order_by(DocumentChunk.embedding.cosine_distance(query_embedding))
            .limit(limit)
        )
        return list(result.scalars().all())
