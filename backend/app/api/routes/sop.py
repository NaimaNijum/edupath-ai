from __future__ import annotations

from fastapi import APIRouter, Depends
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
    return await service.generate(request)


@router.post("/revise", response_model=SOPResponse)
async def revise_sop(
    request: SOPReviseRequest,
    session: AsyncSession = Depends(get_db),
    service: SOPService = Depends(get_sop_service),
) -> SOPResponse:
    return await service.revise(request)
