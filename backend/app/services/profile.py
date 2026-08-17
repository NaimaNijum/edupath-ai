from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.entities import StudentProfile
from app.repositories.profile import ProfileRepository
from app.schemas.profile import StudentProfileCreate, StudentProfileRead, StudentProfileUpdate


class ProfileService:
    def __init__(self, repository: ProfileRepository | None = None) -> None:
        self._repository = repository or ProfileRepository()

    async def create(self, session: AsyncSession, request: StudentProfileCreate) -> StudentProfileRead:
        profile = StudentProfile(**request.model_dump())
        saved = await self._repository.create(session, profile)
        return StudentProfileRead.model_validate(saved)

    async def get(self, session: AsyncSession, profile_id: UUID) -> StudentProfileRead | None:
        profile = await self._repository.get(session, profile_id)
        return StudentProfileRead.model_validate(profile) if profile else None

    async def update(self, session: AsyncSession, profile_id: UUID, request: StudentProfileUpdate) -> StudentProfileRead | None:
        profile = await self._repository.get(session, profile_id)
        if profile is None:
            return None

        payload = request.model_dump(exclude_unset=True)
        for key, value in payload.items():
            setattr(profile, key, value)

        saved = await self._repository.update(session, profile)
        return StudentProfileRead.model_validate(saved)
