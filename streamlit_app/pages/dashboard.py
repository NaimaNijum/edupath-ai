"""
Dashboard — Student Personal Command Center.
"""
from __future__ import annotations

import textwrap
import streamlit as st

from api.client import BackendError, list_opportunities_cached, list_workflows
from components.common import section_header
from components.empty_state import render_empty_state
from components.header import render_page_header
from components.metrics import metric_grid
from components.opportunity_card import render_opportunity_card
from components.workflow_status import render_workflow_status
from utils.formatting import days_until, greeting_for_now, profile_completion


def _html(content: str) -> None:
    """Render HTML safely without markdown 4-space code block formatting."""
    st.markdown(textwrap.dedent(content).strip(), unsafe_allow_html=True)


def render() -> None:
    profile = st.session_state.get("profile")
    user = st.session_state.get("current_user")
    name = (profile or {}).get("name") or (user or {}).get("name") or "there"

    render_page_header(
        f"{greeting_for_now()}, {name.split()[0] if name != 'there' else name}",
        "Your personal AI study-abroad command center.",
        eyebrow="Dashboard",
    )

    opportunities, catalog_error = _load_catalog()
    completion = profile_completion(profile)
    workflows = _load_workflows()

    # --- Top Banner with Primary Action ---
    _render_command_banner(profile, completion, workflows)

    st.write("")

    # --- Compact Student Metric Cards ---
    _render_student_metrics(profile, completion, opportunities, workflows)

    st.write("")

    # --- Main Two-Column Layout ---
    left_col, right_col = st.columns([1.25, 0.85], gap="large")

    with left_col:
        # Current Active Counseling
        section_header("Current Counseling Progress", "Active multi-agent pipeline.")
        _render_current_counseling_card(workflows)

        st.write("")
        # Recent Sessions List
        section_header("Recent Counseling Sessions", f"{len(workflows)} session(s) recorded.")
        if workflows:
            for wf in workflows[:4]:
                _render_compact_session_row(wf)
        else:
            render_empty_state(
                "No counseling runs yet",
                "Start a new session to deploy the 9-agent team for your academic goals.",
                icon="✦",
                cta_label="Start New Counseling",
                cta_page="pages/counseling.py",
                key="dashboard-no-workflows",
            )

    with right_col:
        # Profile Strength Breakdown
        section_header("Profile Strength Breakdown", "Data completeness for AI matching.")
        _render_profile_breakdown_card(profile, completion)

        st.write("")
        # AI Agent Workforce Status
        section_header("AI Counseling Workforce", "Specialist agents ready to deploy.")
        _render_workforce_status_widget()

        st.write("")
        # Quick Actions
        section_header("Quick Actions")
        with st.container(key="dashboard-quick-actions", border=True):
            actions = [
                ("✦ Start New Counseling", "pages/counseling.py", "Deploy all 9 agents on your profile."),
                ("Explore Universities", "pages/discover.py", "Browse program recommendations."),
                ("Document Workspace", "pages/sop.py", "Draft tailored SOPs and outreach emails."),
                ("Application Tracker", "pages/tracker.py", "Manage admissions milestones."),
            ]
            for label, page, caption in actions:
                st.page_link(page, label=label, icon=":material/arrow_forward:")
                st.caption(caption)
                st.write("")

    # --- Upcoming Opportunities ---
    st.write("")
    section_header(
        "Recommended Opportunities",
        "Curated from the EduPath AI database with upcoming deadlines.",
    )
    if catalog_error:
        st.caption("Couldn't connect to the opportunity catalog right now.")
    elif not opportunities:
        render_empty_state(
            "No opportunities in the catalog yet",
            "Run a counseling session to populate the catalog with verified programs.",
            icon="🧭",
            cta_label="Start Counseling",
            cta_page="pages/counseling.py",
            key="dashboard-opps",
        )
    else:
        upcoming = sorted(
            opportunities,
            key=lambda opp: (days_until(opp.get("deadline")) is None, days_until(opp.get("deadline")) or 0),
        )[:3]
        columns = st.columns(len(upcoming))
        for column, opportunity in zip(columns, upcoming, strict=True):
            with column:
                render_opportunity_card(opportunity, key=f"dash-{opportunity.get('id')}")

    # --- Latest Workflow Result ---
    st.write("")
    section_header("Latest AI Counseling Report", "Detailed findings from your most recent session.")
    workflow_result = st.session_state.get("workflow_result")
    if not workflow_result:
        render_empty_state(
            "No active analysis in session",
            "Launch a counseling session to see live agent findings, fit scores, and SOP drafting.",
            icon="✦",
            cta_label="Start New Counseling",
            cta_page="pages/counseling.py",
            key="dashboard-workflow",
        )
    else:
        st.caption(f"Showing session {workflow_result.get('workflow_id', 'unknown')} (most recent in this session)")
        render_workflow_status(workflow_result)


def _render_command_banner(profile: dict | None, completion: int, workflows: list[dict]) -> None:
    profile_name = (profile or {}).get("name") or "Student"
    field_of_study = (profile or {}).get("field_of_study") or "Academic Record"
    current_degree = (profile or {}).get("current_degree") or (profile or {}).get("academic_level") or "Student Profile"
    is_profile_ready = bool(profile and profile.get("gpa") and profile.get("field_of_study"))

    with st.container(key="dashboard-hero", border=False):
        c_left, c_right = st.columns([1.4, 1])
        with c_left:
            _html(
                f"""
                <div class="ep-dashboard-hero-inner">
                  <div>
                    <div class="ep-eyebrow" style="color: #A5B4FC; margin-bottom: 0.35rem;">STUDENT COMMAND CENTER</div>
                    <div class="ep-dashboard-title">{profile_name}</div>
                    <div class="ep-dashboard-subtitle" style="color: #CBD5E1;">{field_of_study} · {current_degree}</div>
                  </div>
                  <div class="ep-dashboard-stat-pill">{completion}% Portfolio Strength</div>
                </div>
                """
            )
        with c_right:
            st.write("")
            if is_profile_ready:
                if st.button(
                    "+ Start AI Counseling",
                    type="primary",
                    use_container_width=True,
                    key="hero-start-counseling-btn",
                    help="Launch the multi-agent counseling wizard",
                ):
                    st.switch_page("pages/counseling.py")
            else:
                if st.button(
                    "⚠️ Complete Profile to Unlock Counseling",
                    type="primary",
                    use_container_width=True,
                    key="hero-complete-profile-btn",
                    help="You must complete your profile first before counseling can run",
                ):
                    st.switch_page("pages/profile.py")


def _render_student_metrics(profile: dict | None, completion: int, opportunities: list[dict], workflows: list[dict]) -> None:
    saved = st.session_state.get("saved_opportunities", {})
    phd_count = sum(1 for o in opportunities if "phd" in (o.get("degree_level") or "").lower())
    funding_count = sum(1 for o in opportunities if "fund" in (o.get("funding_type") or "").lower())

    cards = [
        {
            "label": "Profile Strength",
            "value": f"{completion}%",
            "progress": completion / 100,
            "key": "m-profile",
        },
        {
            "label": "Active Sessions",
            "value": max(len(workflows), 1 if st.session_state.get("workflow_result") else 0),
            "caption": "AI analyses on record",
            "key": "m-sessions",
        },
        {
            "label": "University Matches",
            "value": len(opportunities),
            "caption": f"{phd_count} advanced programs",
            "key": "m-matches",
        },
        {
            "label": "Funding Matches",
            "value": funding_count or len(saved),
            "caption": "Scholarships & assistantships",
            "key": "m-funding",
        },
    ]
    metric_grid(cards)


def _render_current_counseling_card(workflows: list[dict]) -> None:
    latest_wf = workflows[0] if workflows else None
    latest_result = st.session_state.get("workflow_result")

    target = "PhD in Computer Science · United States"
    if latest_wf and latest_wf.get("user_request"):
        target = latest_wf.get("user_request")[:50] + "..."

    status = (latest_result or {}).get("workflow_status") or (latest_wf or {}).get("status") or "ready"
    is_done = status == "completed"

    with st.container(key="dashboard-current-counseling", border=True):
        _html(
            f"""
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.8rem;">
                <div>
                    <div style="font-size: 1rem; font-weight: 700; color: #0F172A;">{target}</div>
                    <div style="font-size: 0.8rem; color: #64748B; margin-top: 0.15rem;">Multi-Agent Pipeline Execution</div>
                </div>
                <span class="ep-badge {'success' if is_done else 'indigo'}">{'Completed' if is_done else 'Active'}</span>
            </div>

            <div style="background: #F8FAFC; border-radius: 10px; padding: 0.75rem 1rem; margin-bottom: 1rem;">
                <div style="display: flex; justify-content: space-between; font-size: 0.82rem; padding: 0.25rem 0;">
                    <span style="color: #475569;">Profile Analysis</span>
                    <span style="color: #16A34A; font-weight: 700;">✓ Completed</span>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 0.82rem; padding: 0.25rem 0;">
                    <span style="color: #475569;">University Research</span>
                    <span style="color: #16A34A; font-weight: 700;">✓ Completed</span>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 0.82rem; padding: 0.25rem 0;">
                    <span style="color: #475569;">Funding & Scholarships</span>
                    <span style="color: {'#16A34A' if is_done else '#4F46E5'}; font-weight: 700;">{'✓ Completed' if is_done else '● In Progress'}</span>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 0.82rem; padding: 0.25rem 0;">
                    <span style="color: #475569;">Faculty Alignment</span>
                    <span style="color: {'#16A34A' if is_done else '#94A3B8'}; font-weight: 700;">{'✓ Completed' if is_done else '○ Ready'}</span>
                </div>
            </div>
            """
        )

        col_act1, col_act2 = st.columns(2)
        with col_act1:
            if st.button("Continue Counseling →", type="primary", use_container_width=True, key="current-counseling-continue"):
                st.switch_page("pages/counseling.py")
        with col_act2:
            if st.button("View AI Insights", use_container_width=True, key="current-counseling-trace"):
                st.switch_page("pages/settings.py")


def _render_profile_breakdown_card(profile: dict | None, completion: int) -> None:
    gpa_filled = bool(profile and profile.get("gpa"))
    research_filled = bool(profile and (profile.get("research_interests") or profile.get("publications")))
    pref_filled = bool(profile and profile.get("target_countries"))

    academic_pct = 95 if gpa_filled else 40
    research_pct = 90 if research_filled else 35
    pref_pct = 85 if pref_filled else 30

    with st.container(key="dashboard-profile-breakdown", border=True):
        _html(
            f"""
            <div style="margin-bottom: 0.75rem;">
                <div style="display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 0.2rem;">
                    <span style="color: #475569; font-weight: 500;">Academic Background</span>
                    <span style="color: #0F172A; font-weight: 700;">{academic_pct}%</span>
                </div>
                <div class="ep-progress-track" style="margin-top: 0; margin-bottom: 0.65rem; height: 6px;">
                    <div class="ep-progress-fill" style="width: {academic_pct}%;"></div>
                </div>

                <div style="display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 0.2rem;">
                    <span style="color: #475569; font-weight: 500;">Research Experience</span>
                    <span style="color: #0F172A; font-weight: 700;">{research_pct}%</span>
                </div>
                <div class="ep-progress-track" style="margin-top: 0; margin-bottom: 0.65rem; height: 6px;">
                    <div class="ep-progress-fill" style="width: {research_pct}%;"></div>
                </div>

                <div style="display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 0.2rem;">
                    <span style="color: #475569; font-weight: 500;">Preferences & Goals</span>
                    <span style="color: #0F172A; font-weight: 700;">{pref_pct}%</span>
                </div>
                <div class="ep-progress-track" style="margin-top: 0; margin-bottom: 0.65rem; height: 6px;">
                    <div class="ep-progress-fill" style="width: {pref_pct}%;"></div>
                </div>
            </div>
            """
        )
        if st.button("Complete Profile →", use_container_width=True, key="profile-breakdown-btn"):
            st.switch_page("pages/profile.py")


def _render_workforce_status_widget() -> None:
    agents = [
        ("Supervisor", "✦", "Active Orchestrator", "success"),
        ("Profile Analyst", "👤", "Academic Profiler", "indigo"),
        ("University Matcher", "🏫", "Program Discovery", "indigo"),
        ("Scholarship Engine", "💰", "Funding Search", "indigo"),
        ("Eligibility Verifier", "✅", "Criteria Check", "indigo"),
        ("Research Matcher", "🔬", "Faculty Alignment", "purple"),
        ("Ranking Engine", "⭐", "Weighted Scoring", "indigo"),
        ("SOP Generator", "📄", "Application Docs", "indigo"),
    ]
    with st.container(key="dashboard-agent-widget", border=True):
        for name, icon, desc, badge_style in agents:
            _html(
                f"""
                <div style="display: flex; align-items: center; justify-content: space-between; padding: 0.32rem 0; border-bottom: 1px solid #F8FAFC;">
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <span style="font-size: 0.95rem;">{icon}</span>
                        <div>
                            <div style="font-size: 0.82rem; font-weight: 600; color: #0F172A;">{name}</div>
                            <div style="font-size: 0.72rem; color: #94A3B8;">{desc}</div>
                        </div>
                    </div>
                    <span class="ep-badge {badge_style}" style="font-size: 0.68rem;">Ready</span>
                </div>
                """
            )


def _render_compact_session_row(wf: dict) -> None:
    status = wf.get("status", "unknown")
    status_style = {
        "completed": "success",
        "failed": "danger",
        "awaiting_approval": "warning",
        "running": "indigo",
    }.get(status, "neutral")
    wf_id = wf.get("id", "")
    short_id = wf_id[:8] if wf_id else "—"
    created = (wf.get("created_at") or "")[:10]
    request_preview = (wf.get("user_request") or "Counseling session")[:65]

    with st.container(key=f"dash-wf-{wf_id}", border=True):
        c1, c2 = st.columns([3.8, 1.2])
        with c1:
            _html(
                f"""
                <div style="font-weight: 600; font-size: 0.88rem; color: #0F172A;">{request_preview}{'...' if len(wf.get('user_request',''))>65 else ''}</div>
                <div style="font-size: 0.75rem; color: #64748B; margin-top: 0.2rem;">Session: {short_id} · Date: {created}</div>
                """
            )
        with c2:
            _html(
                f'<span class="ep-badge {status_style}" style="display: block; text-align: center; margin-bottom: 0.35rem;">{status.replace("_", " ").title()}</span>'
            )
            if st.button("Inspect →", key=f"view-wf-{wf_id}", use_container_width=True):
                st.session_state["current_workflow_id"] = wf_id
                st.switch_page("pages/agent_trace.py")


def _load_catalog() -> tuple[list[dict], bool]:
    try:
        return list_opportunities_cached(), False
    except BackendError:
        return [], True


def _load_workflows() -> list[dict]:
    profile_id = st.session_state.get("profile_id")
    if not profile_id:
        return []
    try:
        return list_workflows(profile_id)
    except BackendError:
        return []


render()
