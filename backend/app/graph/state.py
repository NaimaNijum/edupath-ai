from __future__ import annotations

from typing import Annotated, TypedDict

from app.schemas.agent import AgentMessage, AgentResult


def _append(left, right):
    return left + right


class EduPathState(TypedDict, total=False):
    workflow_id: str
    workflow_type: str
    user_request: str
    student_profile_id: str | None
    current_task: str
    execution_plan: list[str]
    plan_index: int
    next_agent: str
    # Total Gemini generateContent calls made so far in this workflow run,
    # enforced against settings.max_llm_calls_per_workflow.
    llm_call_count: int
    workflow_status: str
    approval_status: str
    profile: dict
    agent_results: Annotated[list[AgentResult], _append]
    agent_messages: Annotated[list[AgentMessage], _append]
    memory_references: Annotated[list[dict], _append]
    tool_results: Annotated[list[dict], _append]
    errors: Annotated[list[str], _append]
    scholarship_research: dict
    university_research: dict
    professor_research: dict
    eligibility_review: dict
    sop_review: dict
    verification_report: dict
    final_response: str
