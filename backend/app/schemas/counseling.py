from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.agent import AgentMessage, AgentResult
from app.schemas.opportunity_candidate import CandidateOpportunity, RankedOpportunity


class CounselingAnalyzeRequest(BaseModel):
    user_request: str = Field(min_length=1)
    student_profile_id: str | None = None
    workflow_type: str = "opportunity_discovery"


class CounselingAnalyzeResponse(BaseModel):
    workflow_id: str
    workflow_type: str = "opportunity_discovery"
    workflow_status: str
    approval_status: str = "not_required"
    execution_plan: list[str] = Field(default_factory=list)
    agent_results: list[AgentResult] = Field(default_factory=list)
    agent_messages: list[AgentMessage] = Field(default_factory=list)
    final_response: str | None = None
    errors: list[str] = Field(default_factory=list)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    token_usage: dict[str, float | int] = Field(default_factory=dict)
    estimated_cost_usd: float = 0.0
    candidate_opportunities: list[CandidateOpportunity] = Field(default_factory=list)
    ranked_opportunities: list[RankedOpportunity] = Field(default_factory=list)
    pending_approval: dict | None = None
    message: str = "Counseling analysis started successfully."
    status: str = "running"

    model_config = ConfigDict(from_attributes=True)
