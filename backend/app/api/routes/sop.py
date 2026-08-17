from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.sop import SOPGenerateRequest, SOPResponse, SOPReviseRequest
from app.services.sop import SOPService

router = APIRouter(prefix="/sop", tags=["sop"])


def get_sop_service() -> SOPService:
    return SOPService()


@router.post("/generate", response_model=SOPResponse)
async def generate_sop(
    request: SOPGenerateRequest,
    session: AsyncSession = Depends(get_db),
    service: SOPService = Depends(get_sop_service),
) -> SOPResponse:
    return await service.generate(session, request)


@router.post("/revise", response_model=SOPResponse)
async def revise_sop(
    request: SOPReviseRequest,
    session: AsyncSession = Depends(get_db),
    service: SOPService = Depends(get_sop_service),
) -> SOPResponse:
    response = await service.revise(session, request)
    if response is None:
        raise HTTPException(status_code=404, detail="SOP not found")
    return response


@router.get("/{sop_id}", response_model=SOPResponse)
async def get_sop(
    sop_id: UUID,
    session: AsyncSession = Depends(get_db),
    service: SOPService = Depends(get_sop_service),
) -> SOPResponse:
    response = await service.get(session, sop_id)
    if response is None:
        raise HTTPException(status_code=404, detail="SOP not found")
    return response


@router.get("", response_model=list[SOPResponse])
async def list_sops(
    profile_id: UUID,
    session: AsyncSession = Depends(get_db),
    service: SOPService = Depends(get_sop_service),
) -> list[SOPResponse]:
    return await service.list_for_profile(session, profile_id)
