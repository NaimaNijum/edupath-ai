from __future__ import annotations

import streamlit as st

from api.client import BackendError, get_workflow_agents
from components.header import render_page_header

_AGENT_NODES = [
    "profile_agent", "professor_agent", "university_agent", "scholarship_agent",
    "eligibility_agent", "research_match_agent", "verification_agent",
    "ranking_agent", "approval_gate", "sop_agent",
]
_NOT_RUN_COLOR = "#E2E8F0"
_STATUS_COLORS = {"success": "#16A34A", "needs_human_review": "#F59E0B", "failed": "#DC2626"}


def render() -> None:
    render_page_header(
        "Execution Graph",
        "The actual LangGraph topology behind every EduPath AI workflow run -- a hub-and-spoke graph where the supervisor routes to each specialist agent and gets control back.",
        eyebrow="Graph",
    )

    workflow_id = st.session_state.get("current_workflow_id") or ""
    status_by_agent: dict[str, str] = {}
    if workflow_id:
        try:
            executions = get_workflow_agents(workflow_id)
            status_by_agent = {e["agent_name"]: e["status"] for e in executions}
        except BackendError:
            pass

    st.graphviz_chart(_build_dot(status_by_agent), use_container_width=True)

    if status_by_agent:
        st.caption(f"Node colors reflect the real status of workflow `{workflow_id}`. Gray = not reached yet.")
    else:
        st.caption("Showing the static topology. Run a discovery workflow to see live status colors here.")


def _build_dot(status_by_agent: dict[str, str]) -> str:
    lines = [
        "digraph G {",
        "rankdir=TB;",
        'bgcolor="transparent";',
        'node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=11, margin=0.18, color="#94A3B8"];',
        'edge [color="#94A3B8", arrowsize=0.7];',
        f'supervisor [label="Supervisor", fillcolor="#4F46E5", fontcolor="white"];',
        'START [shape=circle, width=0.3, fillcolor="#0F172A", fontcolor="white", label=""];',
        '"END" [shape=doublecircle, fillcolor="#0F172A", fontcolor="white"];',
        "START -> supervisor;",
    ]
    for node in _AGENT_NODES:
        status = status_by_agent.get(node)
        color = _STATUS_COLORS.get(status, _NOT_RUN_COLOR)
        text_color = "white" if color != _NOT_RUN_COLOR else "#0F172A"
        label = node.replace("_", " ").title()
        lines.append(f'{node} [label="{label}", fillcolor="{color}", fontcolor="{text_color}"];')
        lines.append(f"supervisor -> {node};")
        lines.append(f"{node} -> supervisor;")
    lines.append('supervisor -> "END" [label="  plan complete"];')
    lines.append("}")
    return "\n".join(lines)


render()
