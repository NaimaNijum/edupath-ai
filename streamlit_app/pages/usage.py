from __future__ import annotations

import streamlit as st

from api.client import BackendError, list_workflows
from components.common import render_backend_error, section_header
from components.empty_state import render_empty_state
from components.header import render_page_header
from components.metrics import metric_grid


def render() -> None:
    render_page_header(
        "Usage & Cost",
        "Real token and cost figures across your discovery workflows -- nothing here is estimated or invented.",
        eyebrow="Usage",
    )

    profile_id = st.session_state.get("profile_id")
    if not profile_id:
        render_empty_state(
            "No profile yet",
            "Complete your profile first to see usage across your workflows.",
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
            "No workflows yet",
            "Run a discovery search to see token usage and cost here.",
            icon="📊",
            cta_label="Discover Opportunities",
            cta_page="pages/discover.py",
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
            cols = st.columns([3, 1.5, 1, 1, 1])
            with cols[0]:
                st.markdown(f"**{workflow.get('user_request', '')[:80]}**")
                st.caption(workflow["started_at"])
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
            with cols[4]:
                if st.button("Trace", key=f"usage-trace-{workflow['id']}", icon=":material/arrow_forward:"):
                    st.session_state["current_workflow_id"] = workflow["id"]
                    st.switch_page("pages/agent_trace.py")


render()
