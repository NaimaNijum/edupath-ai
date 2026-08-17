from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AgentMessage(BaseModel):
    sender: str
    receiver: str
    message_type: str = "handoff"
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AgentResult(BaseModel):
    agent_name: str
    status: Literal["success", "needs_human_review", "failed"] = "success"
    summary: str
    key_findings: list[str] = Field(default_factory=list)
    recommended_next_agent: str | None = None
    supervisor_message: str
    next_agent_message: str | None = None
    confidence: float | None = None
    needs_human_approval: bool = False
    raw_output: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    token_usage: dict[str, float | int] = Field(default_factory=dict)
    estimated_cost_usd: float = 0.0

    model_config = ConfigDict(extra="forbid")


class TokenUsage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0


class SupervisorDecision(BaseModel):
    next_agent: str
    reason: str
    execution_plan: list[str] = Field(default_factory=list)
    workflow_status: Literal["running", "completed", "awaiting_approval", "failed"] = "running"
    final_response: str | None = None


class WorkflowExecutionSummary(BaseModel):
    workflow_status: str
    execution_plan: list[str]
    agent_results: list[AgentResult]
    agent_messages: list[AgentMessage]
    final_response: str | None = None
    errors: list[str] = Field(default_factory=list)

