from __future__ import annotations

from datetime import datetime
from typing import Iterable

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.opportunity import OpportunityRepository
from app.repositories.professor import ProfessorRepository
from app.repositories.university import UniversityRepository
from app.schemas.opportunity_candidate import CandidateOpportunity


def _parse_deadline(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


class CatalogSyncService:
    """Persists candidates discovered during a workflow run into the real
    catalog tables, so the Catalog/Dashboard actually reflect what Discover
    found -- previously, discovered candidates only ever lived inside that
    one workflow's response, which is why the Catalog could never show what
    a discovery run had just surfaced.

    Categorization is intentionally non-exclusive: a single candidate can
    write to more than one table (e.g. a professor candidate that also
    carries funding info becomes both a Professor row and an Opportunity
    row) -- mirrors the same fix already applied to the Excel export's
    sheet-bucketing logic.
    """

    def __init__(
        self,
        opportunity_repository: OpportunityRepository | None = None,
        university_repository: UniversityRepository | None = None,
        professor_repository: ProfessorRepository | None = None,
    ) -> None:
        self._opportunity_repository = opportunity_repository or OpportunityRepository()
        self._university_repository = university_repository or UniversityRepository()
        self._professor_repository = professor_repository or ProfessorRepository()

    async def sync_candidates_to_catalog(self, session: AsyncSession, candidates: Iterable[CandidateOpportunity]) -> None:
        for candidate in candidates:
            if candidate.university:
                await self._university_repository.upsert_by_name(
                    session,
                    name=candidate.university,
                    country=candidate.country,
                    website_url=candidate.official_url if not candidate.professor_name else None,
                    description=None,
                )

            if candidate.professor_name:
                await self._professor_repository.upsert_by_name_and_university(
                    session,
                    name=candidate.professor_name,
                    university=candidate.university,
                    research_interests=candidate.research_areas,
                    profile_url=candidate.official_url,
                )

            if candidate.funding_type:
                await self._opportunity_repository.upsert_by_title(
                    session,
                    title=candidate.title,
                    university=candidate.university,
                    degree_level=candidate.degree_level,
                    country=candidate.country,
                    field=", ".join(candidate.research_areas) if candidate.research_areas else None,
                    funding_type=candidate.funding_type,
                    deadline=_parse_deadline(candidate.deadline),
                    application_url=candidate.official_url,
                    description=None,
                )
