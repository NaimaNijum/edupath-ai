from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


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
    draft_version: int = 1
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("sop_id", mode="before")
    @classmethod
    def serialize_id(cls, value: object) -> str | None:
        return str(value) if value is not None else None


class SOPRead(BaseModel):
    id: str
    profile_id: str | None = None
    title: str | None = None
    content: str | None = None
    status: str
    draft_version: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", "profile_id", mode="before")
    @classmethod
    def serialize_ids(cls, value: object) -> str | None:
        return str(value) if value is not None else None
