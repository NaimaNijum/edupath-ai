from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

DocumentType = Literal["cv", "transcript", "research_proposal", "previous_sop", "publication", "other"]


class DocumentRead(BaseModel):
    id: str
    profile_id: str | None = None
    filename: str
    document_type: str
    chunk_count: int = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", "profile_id", mode="before")
    @classmethod
    def serialize_ids(cls, value: object) -> str | None:
        return str(value) if value is not None else None
