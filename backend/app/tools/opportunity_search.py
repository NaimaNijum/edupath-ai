from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.opportunity import OpportunityRepository
from app.schemas.tool import ToolSearchResponse, ToolSearchResult, ToolSource


class OpportunitySearchTool:
    def __init__(self, repository: OpportunityRepository | None = None) -> None:
        self._repository = repository or OpportunityRepository()

    async def search(self, session: AsyncSession, query: str, limit: int = 5) -> ToolSearchResponse:
        opportunities = await self._repository.list(session)
        filtered = [
            opportunity
            for opportunity in opportunities
            if query.lower() in " ".join(
                filter(None, [opportunity.title, opportunity.provider or "", opportunity.university or "", opportunity.field or ""])
            ).lower()
        ]
        results = [
            ToolSearchResult(
                title=opportunity.title,
                description=opportunity.description,
                source=ToolSource(
                    source="postgresql",
                    url=opportunity.application_url or opportunity.source_url,
                    retrieved_at=datetime.now(UTC),
                    confidence=0.85,
                ),
                metadata={
                    "university": opportunity.university,
                    "degree_level": opportunity.degree_level,
                    "country": opportunity.country,
                    "funding_type": opportunity.funding_type,
                },
            )
            for opportunity in filtered[:limit]
        ]
        return ToolSearchResponse(tool_name="opportunity_search", query=query, results=results)
