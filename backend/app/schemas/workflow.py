from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.agent import AgentMessage, AgentResult
from app.schemas.opportunity_candidate import CandidateOpportunity, RankedOpportunity


class WorkflowCreateRequest(BaseModel):
    user_request: str = Field(min_length=1)
    student_profile_id: str | None = None
    workflow_type: str = "opportunity_discovery"


class ApprovalDecisionRequest(BaseModel):
    """Body for POST /workflows/{id}/approve and /reject."""

    opportunity_id: str | None = None


class WorkflowRead(BaseModel):
    id: str
    profile_id: str | None = None
    workflow_type: str
    status: str
    started_at: datetime
    completed_at: datetime | None = None
    error: str | None = None
    user_request: str
    token_usage: dict[str, float | int] = Field(default_factory=dict)
    estimated_cost_usd: float = 0.0

    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", "profile_id", mode="before")
    @classmethod
    def serialize_ids(cls, value: object) -> str | None:
        return str(value) if value is not None else None


class AgentExecutionRead(BaseModel):
    id: str
    workflow_id: str
    agent_name: str
    status: str
    started_at: datetime
    completed_at: datetime | None = None
    input: dict = Field(default_factory=dict)
    output: dict = Field(default_factory=dict)
    token_usage: dict[str, float | int] = Field(default_factory=dict)
    estimated_cost: float = 0.0
    error: str | None = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", "workflow_id", mode="before")
    @classmethod
    def serialize_ids(cls, value: object) -> str:
        return str(value)


class AgentMessageRead(BaseModel):
    id: str
    workflow_id: str
    sender: str
    receiver: str
    message_type: str
    content: str
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", "workflow_id", mode="before")
    @classmethod
    def serialize_ids(cls, value: object) -> str:
        return str(value)


class WorkflowExecutionResponse(BaseModel):
    workflow_id: str
    workflow_type: str
    workflow_status: str
    approval_status: str = "not_required"
    execution_plan: list[str]
    agent_results: list[AgentResult]
    agent_messages: list[AgentMessage]
    final_response: str | None = None
    errors: list[str] = Field(default_factory=list)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    token_usage: dict[str, float | int] = Field(default_factory=dict)
    estimated_cost_usd: float = 0.0

    # Structured opportunity data (see app/schemas/opportunity_candidate.py).
    candidate_opportunities: list[CandidateOpportunity] = Field(default_factory=list)
    ranked_opportunities: list[RankedOpportunity] = Field(default_factory=list)

    # Set only when workflow_status == "awaiting_approval": the raw payload
    # approval_gate's interrupt() surfaced, for the frontend to render a
    # real approve/reject UI. POST /workflows/{id}/approve or /reject
    # resumes the paused graph using this same workflow_id.
    pending_approval: dict | None = None

    model_config = ConfigDict(from_attributes=True)


class WorkflowLogsResponse(BaseModel):
    events: list[dict]

