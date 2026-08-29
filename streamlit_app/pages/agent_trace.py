"""
Agent Trace — Enhanced timeline view of workflow execution.

Shows:
- Workflow summary (status, timing, cost)
- Per-agent execution timeline with details
- Agent-to-agent communication log
- Link to execution graph
"""
from __future__ import annotations

from datetime import datetime

import streamlit as st

from api.client import BackendError, get_workflow, get_workflow_agents, get_workflow_messages
from components.common import render_backend_error, section_header
from components.empty_state import render_empty_state
from components.header import render_page_header

_STATUS_STYLE = {
    "success": "success",
    "needs_human_review": "warning",
    "failed": "danger",
    "completed": "success",
}

_AGENT_ICONS = {
    "profile_agent": "👤",
    "university_agent": "🏫",
    "scholarship_agent": "💰",
    "eligibility_agent": "✅",
    "research_match_agent": "🔬",
    "verification_agent": "🔍",
    "ranking_agent": "⭐",
    "approval_gate": "🛡️",
    "sop_agent": "📄",
    "supervisor": "✦",
}


def _format_ts(raw: str | None) -> str:
    if not raw:
        return "—"
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return dt.strftime("%H:%M:%S")
    except ValueError:
        return raw[:8] if raw else "—"


def _format_duration(started: str | None, completed: str | None) -> str:
    if not started or not completed:
        return ""
    try:
        s = datetime.fromisoformat(started.replace("Z", "+00:00"))
        c = datetime.fromisoformat(completed.replace("Z", "+00:00"))
        secs = (c - s).total_seconds()
        return f"{secs:.1f}s"
    except (ValueError, TypeError):
        return ""


def render() -> None:
    render_page_header(
        "Agent Execution Trace",
        "Real per-agent status, timing, and inter-agent communication for a workflow run.",
        eyebrow="Trace",
    )

    default_id = st.session_state.get("current_workflow_id") or ""

    col_id, col_reload = st.columns([5, 1])
    with col_id:
        workflow_id = st.text_input("Workflow ID", value=default_id, placeholder="Paste a workflow ID or run a counseling session first")
    with col_reload:
        st.write("")
        reload = st.button("Reload", icon=":material/refresh:", use_container_width=True)

    if not workflow_id.strip():
        render_empty_state(
            "No workflow selected",
            "Run a counseling session, then come back here to inspect exactly what each agent did.",
            icon="🔬",
            cta_label="Start Counseling",
            cta_page="pages/counseling.py",
            key="trace-empty",
        )
        return

    wf_id = workflow_id.strip()

    if reload or f"trace_data_{wf_id}" not in st.session_state:
        try:
            workflow = get_workflow(wf_id)
            agent_executions = get_workflow_agents(wf_id)
            messages = get_workflow_messages(wf_id)
            st.session_state[f"trace_data_{wf_id}"] = (workflow, agent_executions, messages)
        except BackendError as error:
            render_backend_error(error, key="trace-load")
            return
    else:
        workflow, agent_executions, messages = st.session_state[f"trace_data_{wf_id}"]

    # --- Workflow Header ---
    status = workflow.get("status", "unknown")
    style = {"completed": "success", "failed": "danger", "awaiting_approval": "warning", "running": "indigo"}.get(status, "neutral")
    cost = workflow.get("estimated_cost_usd")
    token_usage = workflow.get("token_usage") or {}

    with st.container(key="trace-header", border=True):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(
                f'<div class="ep-metric-label">Status</div><div><span class="ep-badge {style}">{status.replace("_"," ").title()}</span></div>',
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                f'<div class="ep-metric-label">Agents Run</div><div class="ep-metric-value" style="font-size:1.4rem;">{len(agent_executions)}</div>',
                unsafe_allow_html=True,
            )
        with c3:
            st.markdown(
                f'<div class="ep-metric-label">Messages</div><div class="ep-metric-value" style="font-size:1.4rem;">{len(messages)}</div>',
                unsafe_allow_html=True,
            )
        with c4:
            cost_str = f"${cost:.4f}" if cost is not None else "—"
            tokens_str = str(token_usage.get("total_tokens", "—"))
            st.markdown(
                f'<div class="ep-metric-label">Cost / Tokens</div><div class="ep-metric-value" style="font-size:1.1rem;">{cost_str} / {tokens_str}</div>',
                unsafe_allow_html=True,
            )

    # --- Agent Timeline ---
    st.write("")
    section_header(
        "Agent Execution Timeline",
        f"{len(agent_executions)} agent(s) executed in this workflow.",
    )

    if not agent_executions:
        st.caption("No agent executions recorded yet.")
    else:
        timeline_html = '<div class="ep-timeline">'
        for execution in sorted(agent_executions, key=lambda e: e.get("started_at") or ""):
            agent_name = execution.get("agent_name") or "agent"
            label = agent_name.replace("_", " ").title()
            icon = _AGENT_ICONS.get(agent_name, "🤖")
            exec_status = execution.get("status", "success")
            badge_style = _STATUS_STYLE.get(exec_status, "neutral")
            ts = _format_ts(execution.get("started_at"))
            duration = _format_duration(execution.get("started_at"), execution.get("completed_at"))
            output = execution.get("output") or {}
            summary = (output.get("summary") or execution.get("error") or "")[:120]

            dot_color = {"success": "#16A34A", "completed": "#16A34A", "needs_human_review": "#F59E0B", "failed": "#DC2626"}.get(exec_status, "#94A3B8")

            timeline_html += f"""
            <div class="ep-timeline-item">
              <div class="ep-timeline-dot" style="background:{dot_color};">{icon}</div>
              <div class="ep-timeline-content">
                <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.2rem;">
                  <span class="ep-timeline-time">{ts}</span>
                  <strong style="font-size:0.9rem;">{label}</strong>
                  <span class="ep-badge {badge_style}" style="font-size:0.68rem;">{exec_status.replace("_"," ").title()}</span>
                  {f'<span class="ep-badge neutral" style="font-size:0.65rem;">{duration}</span>' if duration else ''}
                </div>
                <div class="ep-timeline-text">{summary}</div>
              </div>
            </div>
            """
        timeline_html += "</div>"
        st.markdown(timeline_html, unsafe_allow_html=True)

    # --- Agent Execution Details (expandable) ---
    st.write("")
    section_header("Detailed Agent Findings")
    for execution in agent_executions:
        _render_agent_execution(execution)

    # --- Agent Communication ---
    st.write("")
    section_header(
        "Agent Communication Log",
        f"{len(messages)} message(s) exchanged between agents.",
    )
    if not messages:
        st.caption("No inter-agent messages recorded.")
    else:
        activity_items = ""
        for message in sorted(messages, key=lambda m: m.get("timestamp") or ""):
            ts = _format_ts(message.get("timestamp"))
            sender = (message.get("sender") or "?").replace("_", " ").title()
            receiver = (message.get("receiver") or "?").replace("_", " ").title()
            content = str(message.get("content") or "")[:150]
            mtype = message.get("message_type") or ""

            activity_items += f"""
            <div class="ep-activity-item">
              <span class="ep-activity-timestamp">{ts}</span>
              <span class="ep-activity-sender ep-badge indigo">{sender}</span>
              <span style="color:#94A3B8;font-size:0.75rem;">→ {receiver}</span>
              <span class="ep-activity-message">{content}</span>
            </div>
            """

        st.markdown(
            f'<div class="ep-activity-feed">{activity_items}</div>',
            unsafe_allow_html=True,
        )

    # Quick link to execution graph
    st.write("")
    if st.button("View Execution Graph →", icon=":material/hub:", use_container_width=False):
        st.switch_page("pages/execution_graph.py")


def _render_agent_execution(execution: dict) -> None:
    agent_name = execution.get("agent_name") or "agent"
    label = agent_name.replace("_", " ").title()
    exec_status = execution.get("status", "success")
    style = _STATUS_STYLE.get(exec_status, "neutral")
    icon = _AGENT_ICONS.get(agent_name, "🤖")
    duration = _format_duration(execution.get("started_at"), execution.get("completed_at"))

    title = f"{icon} {label}"
    if duration:
        title += f" · {duration}"

    with st.expander(title, expanded=False):
        st.markdown(
            f'<span class="ep-badge {style}">{exec_status.replace("_"," ").title()}</span>',
            unsafe_allow_html=True,
        )
        output = execution.get("output") or {}
        if output.get("summary"):
            st.write(output["summary"])
        findings = output.get("key_findings") or []
        for finding in findings:
            st.markdown(f"- {finding}")
        if execution.get("error"):
            st.error(execution["error"], icon=":material/error:")

        usage = execution.get("token_usage") or {}
        cost = execution.get("estimated_cost")
        if usage.get("total_tokens") is not None or cost is not None:
            metric_cols = st.columns(3)
            with metric_cols[0]:
                st.metric("Input Tokens", usage.get("input_tokens", "—"))
            with metric_cols[1]:
                st.metric("Output Tokens", usage.get("output_tokens", "—"))
            with metric_cols[2]:
                st.metric("Est. Cost", f"${cost:.5f}" if cost is not None else "—")


render()
