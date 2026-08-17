from __future__ import annotations

import streamlit as st

from api.client import BackendError, get_workflow, get_workflow_agents, get_workflow_messages
from components.common import render_backend_error, section_header
from components.empty_state import render_empty_state
from components.header import render_page_header

_STATUS_STYLE = {"success": "success", "needs_human_review": "warning", "failed": "danger"}


def render() -> None:
    render_page_header(
        "Agent Execution Trace",
        "Real per-agent status and inter-agent communication for a workflow run -- not a simulated animation.",
        eyebrow="Trace",
    )

    default_id = st.session_state.get("current_workflow_id") or ""
    workflow_id = st.text_input("Workflow ID", value=default_id)

    if not workflow_id.strip():
        render_empty_state(
            "No workflow selected",
            "Run a discovery search, then come back here to inspect exactly what each agent did.",
            icon="🔬",
            cta_label="Discover Opportunities",
            cta_page="pages/discover.py",
            key="trace-empty",
        )
        return

    try:
        workflow = get_workflow(workflow_id.strip())
        agent_executions = get_workflow_agents(workflow_id.strip())
        messages = get_workflow_messages(workflow_id.strip())
    except BackendError as error:
        render_backend_error(error, key="trace-load")
        return

    status = workflow.get("status", "unknown")
    style = {"completed": "success", "failed": "danger", "awaiting_approval": "warning", "running": "indigo"}.get(status, "neutral")
    st.markdown(f'<span class="ep-badge {style}">Workflow: {status}</span>', unsafe_allow_html=True)
    st.write("")

    section_header("Agent Executions", f"{len(agent_executions)} agent(s) have run so far in this workflow.")
    if not agent_executions:
        st.caption("No agents have executed yet.")
    for execution in agent_executions:
        _render_agent_execution(execution)

    st.write("")
    section_header("Agent Communication", f"{len(messages)} message(s) exchanged.")
    if not messages:
        st.caption("No messages recorded yet.")
    for message in messages:
        _render_message(message)


def _render_agent_execution(execution: dict) -> None:
    style = _STATUS_STYLE.get(execution.get("status", "success"), "neutral")
    label = (execution.get("agent_name") or "agent").replace("_", " ").title()
    with st.expander(f"{label} -- {execution.get('status', 'unknown')}", icon=":material/smart_toy:"):
        st.markdown(f'<span class="ep-badge {style}">{execution.get("status")}</span>', unsafe_allow_html=True)
        output = execution.get("output") or {}
        if output.get("summary"):
            st.write(output["summary"])
        for finding in output.get("key_findings") or []:
            st.markdown(f"- {finding}")
        if execution.get("error"):
            st.error(execution["error"], icon=":material/error:")
        usage = execution.get("token_usage") or {}
        cost = execution.get("estimated_cost")
        if usage.get("total_tokens") is not None or cost is not None:
            metric_cols = st.columns(2)
            with metric_cols[0]:
                st.caption(f"Tokens: {usage.get('total_tokens', '—')}")
            with metric_cols[1]:
                st.caption(f"Cost: ${cost:.5f}" if cost is not None else "Cost: —")


def _render_message(message: dict) -> None:
    with st.container(key=f"trace-message-{message['id']}", border=True):
        st.markdown(f"**{message['sender']}** → **{message['receiver']}**")
        st.caption(message.get("message_type", ""))
        st.write(message.get("content", ""))


render()
