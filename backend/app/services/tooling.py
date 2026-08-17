from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.tools import OpportunitySearchTool, ProfessorSearchTool, UniversitySearchTool, WebSearchTool


class ToolingService:
    def __init__(
        self,
        web_search: WebSearchTool | None = None,
        university_search: UniversitySearchTool | None = None,
        professor_search: ProfessorSearchTool | None = None,
        opportunity_search: OpportunitySearchTool | None = None,
    ) -> None:
        self._web_search = web_search or WebSearchTool()
        self._university_search = university_search or UniversitySearchTool()
        self._professor_search = professor_search or ProfessorSearchTool()
        self._opportunity_search = opportunity_search or OpportunitySearchTool()

    async def build_context(self, session: AsyncSession, query: str) -> list[dict]:
        results = []

        university_result = await self._university_search.search(session, query, limit=3)
        professor_result = await self._professor_search.search(session, query, limit=3)
        opportunity_result = await self._opportunity_search.search(session, query, limit=3)
        web_result = await self._web_search.search(query, limit=3)

        for item in (university_result, professor_result, opportunity_result, web_result):
            results.append(item.model_dump())

        return results
