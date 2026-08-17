from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ToolSource(BaseModel):
    source: str
    url: str | None = None
    retrieved_at: datetime
    confidence: float = 0.0


class ToolSearchResult(BaseModel):
    title: str
    description: str | None = None
    source: ToolSource
    metadata: dict = Field(default_factory=dict)


class ToolSearchResponse(BaseModel):
    tool_name: str
    query: str
    results: list[ToolSearchResult] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    tool_status: str = "available"

    model_config = ConfigDict(from_attributes=True)
