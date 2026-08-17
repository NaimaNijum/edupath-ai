from __future__ import annotations

from typing import Final


ALL_AGENTS: Final[set[str]] = {
    "profile_agent",
    "professor_agent",
    "university_agent",
    "scholarship_agent",
    "eligibility_agent",
    "sop_agent",
    "verification_agent",
}


def route_from_supervisor(state: dict) -> str:
    return state.get("next_agent", "__end__")


def build_execution_plan(user_request: str) -> list[str]:
    """
    Build a lightweight deterministic execution plan from the user's request.

    The LLM Supervisor will eventually replace this rule-based planner.
    For now, this gives us predictable and testable workflow behavior.
    """

    request = user_request.lower()

    plan: list[str] = ["profile_agent"]

    phd_or_research_request = any(
        keyword in request
        for keyword in (
            "phd",
            "doctorate",
            "research",
            "ai",
            "ml",
            "machine learning",
            "supervisor",
            "advisor",
            "professor",
            "faculty",
        )
    )

    # Scholarship / funding search
    if any(
        keyword in request
        for keyword in (
            "scholarship",
            "funded",
            "funding",
            "fully funded",
            "financial aid",
            "stipend",
        )
    ):
        plan.extend(
            [
                "professor_agent",
                "university_agent",
                "scholarship_agent",
                "eligibility_agent",
            ]
        )

    if phd_or_research_request and "professor_agent" not in plan:
        plan.append("professor_agent")

    # Professor / supervisor search
    if any(
        keyword in request
        for keyword in (
            "professor",
            "supervisor",
            "advisor",
            "faculty",
            "research group",
        )
    ):
        plan.extend(
            [
                "professor_agent",
                "university_agent",
                "eligibility_agent",
            ]
        )

    # University / program discovery
    if any(
        keyword in request
        for keyword in (
            "university",
            "universities",
            "program",
            "ms",
            "master",
            "masters",
            "phd",
            "undergraduate",
            "bachelor",
        )
    ):
        if "university_agent" not in plan:
            plan.append("university_agent")

    if phd_or_research_request and "university_agent" not in plan:
        plan.append("university_agent")

    if phd_or_research_request and "scholarship_agent" not in plan:
        plan.append("scholarship_agent")

    if phd_or_research_request and "eligibility_agent" not in plan:
        plan.append("eligibility_agent")

    # SOP generation
    if any(
        keyword in request
        for keyword in (
            "sop",
            "statement of purpose",
            "personal statement",
        )
    ):
        plan.append("sop_agent")

    if phd_or_research_request and "sop_agent" not in plan:
        plan.append("sop_agent")

    # Verification should happen after research-oriented agents.
    if len(plan) > 1:
        plan.append("verification_agent")

    # Remove duplicates while preserving execution order.
    plan = list(dict.fromkeys(plan))

    return [agent for agent in plan if agent in ALL_AGENTS]


def synthesize_final_response(agent_results: list[dict]) -> str:
    if not agent_results:
        return "No agent results were produced."

    lines = ["EduPath AI workflow summary:"]

    for result in agent_results:
        agent_name = result.get("agent_name", "agent")
        summary = result.get("summary", "")

        if summary:
            lines.append(f"- {agent_name}: {summary}")

    return "\n".join(lines)
