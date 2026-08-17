from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.profile import StudentProfileCreate, StudentProfileRead, StudentProfileUpdate
from app.services.profile import ProfileService

router = APIRouter(prefix="/profiles", tags=["profiles"])


def get_profile_service() -> ProfileService:
    return ProfileService()


@router.post("", response_model=StudentProfileRead)
async def create_profile(
    request: StudentProfileCreate,
    session: AsyncSession = Depends(get_db),
    service: ProfileService = Depends(get_profile_service),
) -> StudentProfileRead:
    try:
        return await service.create(session, request)
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail="A profile with this email already exists") from exc


@router.get("/{profile_id}", response_model=StudentProfileRead)
async def get_profile(
    profile_id: UUID,
    session: AsyncSession = Depends(get_db),
    service: ProfileService = Depends(get_profile_service),
) -> StudentProfileRead:
    profile = await service.get(session, profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.patch("/{profile_id}", response_model=StudentProfileRead)
async def update_profile(
    profile_id: UUID,
    request: StudentProfileUpdate,
    session: AsyncSession = Depends(get_db),
    service: ProfileService = Depends(get_profile_service),
) -> StudentProfileRead:
    profile = await service.update(session, profile_id, request)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile
