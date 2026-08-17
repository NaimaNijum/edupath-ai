from __future__ import annotations

from pydantic import BaseModel, Field


class SOPGenerateRequest(BaseModel):
    profile_id: str
    target_program: str | None = None
    target_university: str | None = None
    prompt: str | None = None


class SOPReviseRequest(BaseModel):
    profile_id: str
    sop_id: str
    feedback: str


class SOPResponse(BaseModel):
    sop_id: str | None = None
    title: str
    content: str
    status: str = "draft"
