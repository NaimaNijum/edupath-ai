from __future__ import annotations

import json

from app.core.config import settings
from app.core.exceptions import LLMQuotaError
from app.core.logging import get_logger
from app.llm.gemini import LLMCallContext

_logger = get_logger(component="workflow_budget")


def ensure_llm_budget(state: dict, *, agent_name: str, purpose: str) -> tuple[int, LLMCallContext]:
    """Reserve the next Gemini call slot for this workflow run.

    Returns ``(call_number, call_context)`` for the caller to pass into the
    provider call and to persist back onto ``state["llm_call_count"]``.
    Raises ``LLMQuotaError`` (without contacting Gemini) once the workflow has
    already made ``settings.max_llm_calls_per_workflow`` calls, so a looping
    or overly broad plan cannot keep burning quota indefinitely.
    """
    workflow_id = state.get("workflow_id")
    call_number = int(state.get("llm_call_count", 0)) + 1
    budget = settings.max_llm_calls_per_workflow

    if call_number > budget:
        _logger.warning(
            "llm_call_budget_exceeded",
            workflow_id=workflow_id,
            agent_name=agent_name,
            purpose=purpose,
            call_number=call_number,
            budget=budget,
        )
        raise LLMQuotaError(
            f"Workflow reached the per-run budget of {budget} Gemini calls.",
            provider="gemini",
            model=settings.gemini_model,
            status_code=429,
            retry_after=None,
            quota_message=(
                f"Per-workflow LLM call budget ({budget}) exhausted before contacting Gemini."
            ),
        )

    return call_number, LLMCallContext(
        workflow_id=workflow_id,
        agent_name=agent_name,
        purpose=purpose,
        call_number=call_number,
    )


def grounded_context(state: dict, tool_names: set[str] | None = None) -> str:
    """Format shared state for agents without letting them discard evidence."""
    tools = state.get("tool_results", [])
    if tool_names:
        tools = [item for item in tools if item.get("tool_name") in tool_names]
    results = [item.model_dump() if hasattr(item, "model_dump") else item for item in state.get("agent_results", [])]
    return f"""
STUDENT PROFILE: {json.dumps(state.get('profile', {}), default=str)}
PREVIOUS AGENT RESULTS: {json.dumps(results, default=str)}
AGENT MESSAGES: {json.dumps([item.model_dump() if hasattr(item, 'model_dump') else item for item in state.get('agent_messages', [])], default=str)}
AVAILABLE TOOL RESULTS: {json.dumps(tools, default=str)}
Use supplied tool results as the factual source. Do not invent scholarships, professors,
universities, deadlines, funding amounts, or eligibility requirements. If evidence is
insufficient, say verification is required.
"""
