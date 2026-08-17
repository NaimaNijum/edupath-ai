from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.document import DocumentRead, DocumentType
from app.services.document import DocumentService, DocumentValidationError

router = APIRouter(prefix="/documents", tags=["documents"])


def get_document_service() -> DocumentService:
    return DocumentService()


@router.post("", response_model=DocumentRead)
async def upload_document(
    profile_id: UUID = Form(...),
    document_type: DocumentType = Form(...),
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db),
    service: DocumentService = Depends(get_document_service),
) -> DocumentRead:
    raw = await file.read()
    try:
        return await service.upload(
            session, profile_id=profile_id, filename=file.filename or "upload", document_type=document_type, raw=raw
        )
    except DocumentValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("", response_model=list[DocumentRead])
async def list_documents(
    profile_id: UUID,
    session: AsyncSession = Depends(get_db),
    service: DocumentService = Depends(get_document_service),
) -> list[DocumentRead]:
    return await service.list_for_profile(session, profile_id)


@router.delete("/{document_id}")
async def delete_document(
    document_id: UUID,
    session: AsyncSession = Depends(get_db),
    service: DocumentService = Depends(get_document_service),
) -> dict:
    deleted = await service.delete(session, document_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"status": "deleted"}
