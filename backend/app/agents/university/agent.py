from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from app.agents.context import ensure_llm_budget, grounded_context
from app.core.config import settings
from app.llm.gemini import get_gemini_provider
from app.llm.usage import serialize_usage
from app.schemas.agent import AgentMessage, AgentResult


class UniversityAgentOutput(BaseModel):
    summary: str
    key_findings: list[str] = Field(default_factory=list)
    recommended_next_agent: str = "professor_agent"
    supervisor_message: str
    next_agent_message: str | None = None
    confidence: float = 0.75


def build_university_agent(provider=None):
    provider = provider or get_gemini_provider()

    def university_agent(state: dict) -> dict:
        user_request = state.get("user_request") or state.get("user_input", "")
        profile = state.get("profile", {})
        started_at = datetime.now(UTC)
        call_number, call_context = ensure_llm_budget(state, agent_name="university_agent", purpose="university_discovery")

        prompt = f"""
You are EduPath AI's University Discovery Agent.

Use the student's request and profile context to reason about suitable universities and programs.

Student request:
{user_request}

Profile context:
{profile}
{grounded_context(state, {"university_search", "web_search"})}

Return JSON with summary, key_findings, recommended_next_agent, supervisor_message, next_agent_message, confidence.
"""

        structured, raw_result = provider.generate_structured(
            prompt,
            response_model=UniversityAgentOutput,
            model=settings.gemini_model,
            context=call_context,
        )
        completed_at = datetime.now(UTC)

        result = AgentResult(
            agent_name="university_agent",
            summary=structured.summary,
            key_findings=structured.key_findings,
            recommended_next_agent=structured.recommended_next_agent,
            supervisor_message=structured.supervisor_message,
            next_agent_message=structured.next_agent_message,
            confidence=structured.confidence,
            raw_output=raw_result.text,
            started_at=started_at,
            completed_at=completed_at,
            token_usage=serialize_usage(raw_result.usage),
            estimated_cost_usd=raw_result.usage.estimated_cost_usd,
        )

        return {
            "university_research": structured.model_dump(),
            "agent_results": [result],
            "llm_call_count": call_number,
            "agent_messages": [
                AgentMessage(
                    sender="university_agent",
                    receiver="supervisor",
                    message_type="analysis",
                    content=structured.supervisor_message,
                )
            ],
            "tool_results": [],
            "memory_references": [],
        }

    return university_agent


university_agent = build_university_agent()
