from __future__ import annotations

import streamlit as st

from api.client import BackendError, approve_workflow, download_workflow_export, reject_workflow
from components.common import confidence_label, render_backend_error
from components.ranked_opportunity_card import render_ranked_opportunity_card

_STATUS_BADGE = {
    "success": ("success", "Success"),
    "needs_human_review": ("warning", "Needs review"),
    "failed": ("danger", "Failed"),
}


def render_workflow_status(result: dict) -> None:
    """Render a WorkflowExecutionResponse as returned by POST /api/v1/workflows.

    Every element here reflects data the backend actually returned -- no
    synthetic progress steps or fabricated timings.
    """
    status = result.get("workflow_status", "unknown")

    if status == "awaiting_approval":
        _render_approval_gate(result)
        return

    if status == "completed":
        st.success("Discovery workflow completed", icon=":material/check_circle:")
    elif status == "failed":
        st.error("Discovery workflow failed", icon=":material/error:")
    else:
        st.info(f"Workflow status: {status}", icon=":material/hourglass_top:")

    plan = result.get("execution_plan") or []
    if plan:
        completed_agents = {item.get("agent_name") for item in result.get("agent_results", [])}
        chips = []
        for agent in plan:
            done = agent in completed_agents
            style = "success" if done else "neutral"
            icon = "✓" if done else "○"
            chips.append(f'<span class="ep-badge {style}">{icon} {agent.replace("_", " ").title()}</span>')
        st.markdown(f'<div class="ep-badge-row">{"".join(chips)}</div>', unsafe_allow_html=True)

    if result.get("final_response"):
        with st.container(key="workflow-summary", border=True):
            st.markdown('<div class="ep-section-title">Summary</div>', unsafe_allow_html=True)
            st.write(result["final_response"])

    for error in result.get("errors") or []:
        st.warning(error, icon=":material/warning:")

    ranked = result.get("ranked_opportunities") or []
    if ranked:
        _render_ranked_results(result)

    agent_results = result.get("agent_results") or []
    if agent_results:
        st.markdown('<div class="ep-section-title" style="margin-top:1rem;">Agent Findings</div>', unsafe_allow_html=True)
        for agent_result in agent_results:
            _render_agent_result(agent_result)

    _render_usage_and_export(result)


def _render_ranked_results(result: dict) -> None:
    candidates_by_id = {c["id"]: c for c in result.get("candidate_opportunities") or []}
    eligibility_by_id = {v["opportunity_id"]: v for v in result.get("eligibility_verdicts") or []}
    research_by_id = {v["opportunity_id"]: v for v in result.get("research_match_verdicts") or []}
    ranked = result.get("ranked_opportunities") or []

    st.markdown(
        f'<div class="ep-section-title" style="margin-top:1rem;">Ranked Opportunities ({len(ranked)})</div>',
        unsafe_allow_html=True,
    )
    columns = st.columns(2)
    for index, item in enumerate(ranked):
        candidate = candidates_by_id.get(item["opportunity_id"])
        if candidate is None:
            continue
        with columns[index % 2]:
            render_ranked_opportunity_card(
                candidate,
                key=f"results-{item['opportunity_id']}",
                ranked=item,
                eligibility=eligibility_by_id.get(item["opportunity_id"]),
                research_match=research_by_id.get(item["opportunity_id"]),
            )


def _render_approval_gate(result: dict) -> None:
    """Genuine human-in-the-loop UI: the backend workflow is actually
    paused (via LangGraph's interrupt()) waiting for this decision -- these
    buttons resume it, they don't just update a status label."""
    st.info("EduPath AI found opportunities and is waiting for your approval before drafting an SOP.", icon=":material/pending_actions:")

    pending = result.get("pending_approval") or {}
    candidates = {c["id"]: c for c in pending.get("candidate_opportunities") or []}
    ranked = pending.get("ranked_opportunities") or []

    selected_id: str | None = None
    if ranked:
        st.markdown('<div class="ep-section-title">Choose an opportunity</div>', unsafe_allow_html=True)
        columns = st.columns(2)
        for index, item in enumerate(ranked):
            candidate = candidates.get(item["opportunity_id"])
            if candidate is None:
                continue
            with columns[index % 2]:
                if render_ranked_opportunity_card(candidate, key=f"approval-{item['opportunity_id']}", ranked=item, selectable=True):
                    selected_id = item["opportunity_id"]

    workflow_id = result.get("workflow_id")
    button_cols = st.columns(2)
    with button_cols[0]:
        if st.button("Approve & Generate SOP", type="primary", icon=":material/check_circle:", use_container_width=True):
            _resume(workflow_id, approve=True, opportunity_id=selected_id)
    with button_cols[1]:
        if st.button("Reject", icon=":material/cancel:", use_container_width=True):
            _resume(workflow_id, approve=False, opportunity_id=selected_id)


def _resume(workflow_id: str, *, approve: bool, opportunity_id: str | None) -> None:
    with st.spinner("Resuming the workflow..." + (" Generating your SOP..." if approve else "")):
        try:
            result = approve_workflow(workflow_id, opportunity_id) if approve else reject_workflow(workflow_id, opportunity_id)
        except BackendError as error:
            render_backend_error(error, key="workflow-resume")
            return
    st.session_state["workflow_result"] = result
    st.rerun()


def _render_usage_and_export(result: dict) -> None:
    token_usage = result.get("token_usage") or {}
    metrics = []
    if token_usage.get("total_tokens") is not None:
        metrics.append(("Total Tokens", token_usage["total_tokens"]))
    if result.get("estimated_cost_usd") is not None:
        metrics.append(("Estimated Cost", f"${result['estimated_cost_usd']:.4f}"))

    if metrics:
        cols = st.columns(len(metrics) + 1)
        for column, (label, value) in zip(cols, metrics, strict=False):
            with column:
                st.metric(label, value)
    else:
        cols = st.columns(1)

    if result.get("candidate_opportunities"):
        with cols[-1]:
            workflow_id = result.get("workflow_id")
            cache_key = f"export_bytes_{workflow_id}"
            if st.session_state.get(cache_key) is None:
                if st.button("Prepare Excel Export", icon=":material/table_view:", use_container_width=True, key=f"prepare-export-{workflow_id}"):
                    try:
                        st.session_state[cache_key] = download_workflow_export(workflow_id)
                        st.rerun()
                    except BackendError as error:
                        render_backend_error(error, key="export")
            else:
                st.download_button(
                    "Download Excel Export",
                    data=st.session_state[cache_key],
                    file_name=f"edupath-{workflow_id}.xlsx",
                    icon=":material/download:",
                    use_container_width=True,
                )


def _render_agent_result(agent_result: dict) -> None:
    style, status_text = _STATUS_BADGE.get(agent_result.get("status", "success"), ("neutral", "Unknown"))
    label = confidence_label(agent_result.get("confidence"))
    agent_name = (agent_result.get("agent_name") or "agent").replace("_", " ").title()

    title = f"{agent_name}"
    if label:
        title += f" · {label} confidence"

    with st.expander(title, expanded=False, icon=":material/smart_toy:"):
        st.markdown(f'<span class="ep-badge {style}">{status_text}</span>', unsafe_allow_html=True)
        if agent_result.get("summary"):
            st.write(agent_result["summary"])
        for finding in agent_result.get("key_findings") or []:
            st.markdown(f"- {finding}")
        if agent_result.get("supervisor_message"):
            st.caption(agent_result["supervisor_message"])
