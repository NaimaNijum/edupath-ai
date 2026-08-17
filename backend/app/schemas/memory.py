from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MemoryRead(BaseModel):
    id: str
    profile_id: str | None = None
    memory_type: str
    scope: str
    content: dict = Field(default_factory=dict)
    source: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", "profile_id", mode="before")
    @classmethod
    def serialize_ids(cls, value: object) -> str | None:
        return str(value) if value is not None else None
