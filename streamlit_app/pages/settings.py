from __future__ import annotations

from datetime import datetime

import streamlit as st

from api.client import BackendError, check_health, list_memory, list_workflows
from components.common import render_backend_error, section_header
from components.empty_state import render_empty_state
from components.header import render_page_header
from components.metrics import metric_grid
from utils.config import BACKEND_URL
from utils.session import reset_session_state


def _format_date(raw: str | None) -> str:
    if not raw:
        return "Unknown date"
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).strftime("%B %d, %Y")
    except ValueError:
        return raw[:10] if raw else "—"


def _extract_interests(entries: list[dict]) -> list[str]:
    interests: set[str] = set()
    for entry in entries:
        content = entry.get("content") or {}
        signals = content.get("profile_signals") or {}
        for field in ("research_interests", "preferred_domains", "research_domains"):
            val = signals.get(field)
            if isinstance(val, list):
                interests.update(str(v) for v in val if v)
            elif isinstance(val, str) and val:
                for part in val.split(","):
                    p = part.strip()
                    if p:
                        interests.add(p)
    return sorted(interests)


def render() -> None:
    render_page_header(
        "AI Insights & System Settings",
        "Inspect AI long-term memory, track token spend across agents, and manage backend connectivity.",
        eyebrow="System & Insights",
    )

    tab_memory, tab_usage, tab_system = st.tabs([
        ":material/psychology: AI Persistent Memory",
        ":material/bar_chart: Token & Cost Analytics",
        ":material/tune: Backend & Settings",
    ])

    with tab_memory:
        _render_memory_tab()

    with tab_usage:
        _render_usage_tab()

    with tab_system:
        _render_system_tab()


def _render_memory_tab() -> None:
    profile_id = st.session_state.get("profile_id")
    if not profile_id:
        render_empty_state(
            "No profile yet",
            "Complete your profile first -- AI memory is tied to your student profile.",
            icon="🧠",
            cta_label="Complete Profile",
            cta_page="pages/profile.py",
            key="memory-no-profile",
        )
        return

    try:
        entries = list_memory(profile_id)
    except BackendError as error:
        render_backend_error(error, key="memory-list")
        return

    if not entries:
        render_empty_state(
            "No AI memory history yet",
            "Run a counseling session to start building your persistent profile memory.",
            icon="🧠",
            cta_label="Start Counseling",
            cta_page="pages/counseling.py",
            key="memory-empty",
        )
        return

    current = [e for e in entries if e.get("scope") == "current_preferences"]
    history = [e for e in entries if e.get("memory_type") == "workflow_history"]
    interests = _extract_interests(entries)

    if interests:
        section_header("Extracted Research Interests", "Signals gathered from counseling workflows.")
        tags = "".join(f'<span class="ep-badge indigo" style="margin-right:0.4rem; margin-bottom:0.4rem;">{i}</span>' for i in interests)
        st.markdown(f'<div style="display:flex; flex-wrap:wrap; margin-bottom:1.5rem;">{tags}</div>', unsafe_allow_html=True)

    if current:
        section_header("Current Preference Snapshot")
        for entry in current:
            content = entry.get("content") or {}
            with st.container(key=f"memory-curr-{entry.get('id')}", border=True):
                st.markdown(f"**Last Request:** {content.get('last_request', 'N/A')}")
                signals = content.get("profile_signals") or {}
                if signals:
                    st.json(signals, expanded=False)
                st.caption(f"Recorded: {_format_date(entry.get('created_at'))}")

    if history:
        st.write("")
        section_header("Session Workflow History", f"{len(history)} counseling event(s) recorded.")
        for entry in history[:5]:
            content = entry.get("content") or {}
            with st.container(key=f"memory-hist-{entry.get('id')}", border=True):
                cols = st.columns([3, 1])
                with cols[0]:
                    st.markdown(f"**{content.get('user_request', 'Workflow Run')}**")
                    if content.get("target_degree") or content.get("target_countries"):
                        st.caption(f"Degree: {content.get('target_degree', '—')} | Countries: {content.get('target_countries', '—')}")
                with cols[1]:
                    st.caption(f"Date: {_format_date(entry.get('created_at'))}")


def _render_usage_tab() -> None:
    profile_id = st.session_state.get("profile_id")
    if not profile_id:
        render_empty_state(
            "No profile yet",
            "Complete your profile first to view token analytics across your workflows.",
            icon="📊",
            cta_label="Complete Profile",
            cta_page="pages/profile.py",
            key="usage-no-profile",
        )
        return

    try:
        workflows = list_workflows(profile_id)
    except BackendError as error:
        render_backend_error(error, key="usage-list")
        return

    if not workflows:
        render_empty_state(
            "No workflows recorded yet",
            "Run a counseling session to see token consumption and cost figures here.",
            icon="📊",
            cta_label="Start Counseling",
            cta_page="pages/counseling.py",
            key="usage-empty",
        )
        return

    total_tokens = sum(w.get("token_usage", {}).get("total_tokens", 0) or 0 for w in workflows)
    total_cost = sum(w.get("estimated_cost_usd", 0) or 0 for w in workflows)
    completed = [w for w in workflows if w.get("status") == "completed"]

    metric_grid([
        {"label": "Total Workflows", "value": len(workflows), "key": "workflows"},
        {"label": "Completed", "value": len(completed), "key": "completed"},
        {"label": "Total Tokens", "value": f"{total_tokens:,}", "key": "tokens"},
        {"label": "Total Estimated Cost", "value": f"${total_cost:.4f}", "key": "cost"},
    ])

    st.write("")
    section_header("Per-Workflow Breakdown")
    for workflow in workflows:
        usage = workflow.get("token_usage") or {}
        with st.container(key=f"usage-row-{workflow['id']}", border=True):
            cols = st.columns([3, 1.5, 1, 1])
            with cols[0]:
                st.markdown(f"**{workflow.get('user_request', '')[:80]}**")
                st.caption(workflow.get("started_at", "—"))
            with cols[1]:
                status = workflow.get("status", "unknown")
                style = {"completed": "success", "failed": "danger", "awaiting_approval": "warning"}.get(status, "neutral")
                st.markdown(f'<span class="ep-badge {style}">{status}</span>', unsafe_allow_html=True)
            with cols[2]:
                if usage.get("total_tokens") is not None:
                    st.metric("Tokens", usage["total_tokens"])
                else:
                    st.caption("Usage unavailable")
            with cols[3]:
                cost = workflow.get("estimated_cost_usd")
                st.metric("Cost", f"${cost:.4f}" if cost is not None else "—")


def _render_system_tab() -> None:
    with st.container(key="settings-backend", border=True):
        section_header("Backend Connection")
        st.write(f"**FastAPI Backend URL:** `{BACKEND_URL}`")
        st.caption("Configured via streamlit_app/.env (BACKEND_URL). OpenRouter is used for multi-agent reasoning.")

        if st.button("Test Connection", icon=":material/wifi_tethering:"):
            try:
                health = check_health()
            except BackendError as error:
                render_backend_error(error, key="settings-health")
            else:
                st.success(f"Backend reachable: {health.get('status', 'healthy')}", icon=":material/check_circle:")

    st.write("")
    with st.container(key="settings-session", border=True):
        section_header("Session State Diagnostics", "Data stored in your browser session.")
        st.write(
            {
                "profile_id": st.session_state.get("profile_id"),
                "current_workflow_id": st.session_state.get("current_workflow_id"),
                "saved_opportunities": len(st.session_state.get("saved_opportunities", {})),
            }
        )
        if st.button("Clear Local Session", type="secondary", icon=":material/restart_alt:"):
            reset_session_state()
            st.success("Session cleared.", icon=":material/check_circle:")
            st.rerun()


render()
