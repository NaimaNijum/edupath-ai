"""
Dashboard — Student Personal Command Center (Notion-style Workspace).
"""
from __future__ import annotations

import streamlit as st

from api.client import BackendError, list_opportunities_cached, list_workflows
from components.common import render_html, section_header
from components.empty_state import render_empty_state
from components.header import render_page_header
from components.metrics import metric_grid
from components.opportunity_card import render_opportunity_card
from components.workflow_status import render_workflow_status
from utils.formatting import days_until, greeting_for_now, profile_completion


def render() -> None:
    profile = st.session_state.get("profile")
    user = st.session_state.get("current_user")
    name = (profile or {}).get("name") or (user or {}).get("name") or "there"

    render_page_header(
        f"{greeting_for_now()}, {name.split()[0] if name != 'there' else name} 👋",
        "Your AI-powered study-abroad workspace and multi-agent command center.",
        eyebrow="Workspace",
    )

    opportunities, catalog_error = _load_catalog()
    completion = profile_completion(profile)
    workflows = _load_workflows()

    # --- Top Notion-Style Hero Banner ---
    _render_command_banner(profile, completion, workflows)

    st.write("")

    # --- Stat Summary Metrics ---
    _render_student_metrics(profile, completion, opportunities, workflows)

    st.write("")

    # --- Main Two-Column Notion Workspace Layout ---
    left_col, right_col = st.columns([1.3, 0.9], gap="large")

    with left_col:
        # Current Active Counseling
        section_header("Active Counseling Pipeline", "Live multi-agent execution & matching.")
        _render_current_counseling_card(workflows)

        st.write("")
        # Recent Sessions List
        section_header("Recent Counseling Sessions", f"{len(workflows)} session(s) on record.")
        if workflows:
            for wf in workflows[:4]:
                _render_compact_session_row(wf)
        else:
            render_empty_state(
                "No counseling sessions yet",
                "Deploy your 8-specialist agent workforce to discover and evaluate programs.",
                icon="✦",
                cta_label="Start AI Counseling",
                cta_page="pages/counseling.py",
                key="dashboard-no-workflows",
            )

    with right_col:
        # Profile Strength Breakdown (Notion-style Card)
        section_header("Academic Portfolio Strength", "Credentials available for AI matching.")
        _render_profile_breakdown_card(profile, completion)

        st.write("")
        # AI Agent Workforce Status
        section_header("AI Agent Workforce", "Specialist agents ready to deploy.")
        _render_workforce_status_widget()

        st.write("")
        # Quick Actions
        section_header("Workspace Shortcuts")
        with st.container(key="dashboard-quick-actions", border=True):
            actions = [
                ("✦ Start AI Counseling", "pages/counseling.py", "Deploy all 8 agents on your academic profile."),
                ("🔍 Explore Opportunities", "pages/discover.py", "Browse catalog and saved bookmarks."),
                ("✍️ Document Studio", "pages/sop.py", "Draft tailored SOPs and outreach emails."),
                ("📋 Application Tracker", "pages/tracker.py", "Manage admissions milestones and stages."),
            ]
            for label, page, caption in actions:
                st.page_link(page, label=label, icon=":material/arrow_forward:")
                st.caption(caption)
                st.write("")

    # --- Recommended Opportunities ---
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

    # --- Latest Workflow Report ---
    workflow_result = st.session_state.get("workflow_result")
    if workflow_result:
        st.write("")
        section_header("Latest AI Counseling Report", "Detailed findings from your most recent session.")
        st.caption(f"Showing session {workflow_result.get('workflow_id', 'unknown')}")
        render_workflow_status(workflow_result)


def _render_command_banner(profile: dict | None, completion: int, workflows: list[dict]) -> None:
    profile_name = (profile or {}).get("name") or "Student"
    field_of_study = (profile or {}).get("field_of_study") or "Academic Profile"
    current_degree = (profile or {}).get("current_degree") or (profile or {}).get("academic_level") or "Student Record"
    gpa = (profile or {}).get("gpa")
    gpa_text = f"GPA: {gpa}/4.0" if gpa else "GPA: Not set"
    is_profile_ready = bool(profile and profile.get("gpa") and profile.get("field_of_study"))

    with st.container(key="dashboard-hero", border=False):
        c_left, c_right = st.columns([1.4, 1])
        with c_left:
            render_html(
                f"""
                <div class="ep-dashboard-hero-inner">
                  <div>
                    <div class="ep-eyebrow" style="color: #A5B4FC; margin-bottom: 0.35rem;">STUDENT WORKSPACE</div>
                    <div class="ep-dashboard-title">{profile_name}</div>
                    <div class="ep-dashboard-subtitle" style="color: #CBD5E1;">{field_of_study} · {current_degree} · {gpa_text}</div>
                  </div>
                  <div class="ep-dashboard-stat-pill">{completion}% Portfolio Complete</div>
                </div>
                """
            )
        with c_right:
            st.write("")
            if is_profile_ready:
                if st.button(
                    "✦ Start AI Counseling Session",
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
            "label": "Portfolio Strength",
            "value": f"{completion}%",
            "progress": completion / 100,
            "key": "m-profile",
        },
        {
            "label": "Counseling Sessions",
            "value": max(len(workflows), 1 if st.session_state.get("workflow_result") else 0),
            "caption": "AI analyses on record",
            "key": "m-sessions",
        },
        {
            "label": "University Matches",
            "value": len(opportunities),
            "caption": f"{phd_count} verified programs",
            "key": "m-matches",
        },
        {
            "label": "Funding & Grants",
            "value": funding_count or len(saved),
            "caption": "Assistantships & waivers",
            "key": "m-funding",
        },
    ]
    metric_grid(cards)


def _render_current_counseling_card(workflows: list[dict]) -> None:
    latest_wf = workflows[0] if workflows else None
    latest_result = st.session_state.get("workflow_result")

    target = "AI Multi-Agent Counseling Pipeline"
    if latest_wf and latest_wf.get("user_request"):
        target = latest_wf.get("user_request")[:55] + "..."

    status = (latest_result or {}).get("workflow_status") or (latest_wf or {}).get("status") or "ready"
    is_done = status == "completed"

    with st.container(key="dashboard-current-counseling", border=True):
        render_html(
            f"""
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.85rem;">
                <div>
                    <div style="font-size: 0.98rem; font-weight: 700; color: #0F172A;">{target}</div>
                    <div style="font-size: 0.78rem; color: #64748B; margin-top: 0.15rem;">Automated 8-Agent Execution Pipeline</div>
                </div>
                <span class="ep-badge {'success' if is_done else 'indigo'}">{'Completed' if is_done else 'Ready'}</span>
            </div>

            <div style="background: #F8FAFC; border: 1px solid #F1F5F9; border-radius: 10px; padding: 0.85rem 1rem; margin-bottom: 1rem;">
                <div style="display: flex; justify-content: space-between; font-size: 0.82rem; padding: 0.25rem 0;">
                    <span style="color: #334155; font-weight: 500;">👤 Profile Academic Signal Analysis</span>
                    <span style="color: #16A34A; font-weight: 700;">✓ Active</span>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 0.82rem; padding: 0.25rem 0;">
                    <span style="color: #334155; font-weight: 500;">🏫 University & Program Matching</span>
                    <span style="color: #16A34A; font-weight: 700;">✓ Active</span>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 0.82rem; padding: 0.25rem 0;">
                    <span style="color: #334155; font-weight: 500;">💰 Scholarship & Assistantship Discovery</span>
                    <span style="color: {'#16A34A' if is_done else '#4F46E5'}; font-weight: 700;">{'✓ Completed' if is_done else '● Ready'}</span>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 0.82rem; padding: 0.25rem 0;">
                    <span style="color: #334155; font-weight: 500;">🔬 Faculty & Research Alignment</span>
                    <span style="color: {'#16A34A' if is_done else '#4F46E5'}; font-weight: 700;">{'✓ Completed' if is_done else '● Ready'}</span>
                </div>
            </div>
            """
        )

        col_act1, col_act2 = st.columns(2)
        with col_act1:
            if st.button("Launch Counseling →", type="primary", use_container_width=True, key="current-counseling-continue"):
                st.switch_page("pages/counseling.py")
        with col_act2:
            if st.button("AI Insights & Memory", use_container_width=True, key="current-counseling-trace"):
                st.switch_page("pages/settings.py")


def _render_profile_breakdown_card(profile: dict | None, completion: int) -> None:
    gpa_filled = bool(profile and profile.get("gpa") and profile.get("field_of_study"))
    research_filled = bool(profile and (profile.get("research_interests") or profile.get("publications")))
    skills_filled = bool(profile and (profile.get("skills") or profile.get("projects") or profile.get("work_experience")))

    academic_pct = 100 if gpa_filled else 30
    research_pct = 95 if research_filled else 25
    skills_pct = 90 if skills_filled else 35

    with st.container(key="dashboard-profile-breakdown", border=True):
        render_html(
            f"""
            <div style="padding: 0.2rem 0 0.5rem 0;">
                <div style="display: flex; justify-content: space-between; font-size: 0.82rem; margin-bottom: 0.25rem;">
                    <span style="color: #475569; font-weight: 500;">Academic Records (GPA & Major)</span>
                    <span style="color: #0F172A; font-weight: 700;">{academic_pct}%</span>
                </div>
                <div class="ep-progress-track" style="margin-top: 0; margin-bottom: 0.75rem; height: 6px; background: #E2E8F0; border-radius: 999px; overflow: hidden;">
                    <div class="ep-progress-fill" style="width: {academic_pct}%; height: 100%; background: linear-gradient(90deg, #4F46E5, #7C3AED); border-radius: 999px;"></div>
                </div>

                <div style="display: flex; justify-content: space-between; font-size: 0.82rem; margin-bottom: 0.25rem;">
                    <span style="color: #475569; font-weight: 500;">Research & Publications</span>
                    <span style="color: #0F172A; font-weight: 700;">{research_pct}%</span>
                </div>
                <div class="ep-progress-track" style="margin-top: 0; margin-bottom: 0.75rem; height: 6px; background: #E2E8F0; border-radius: 999px; overflow: hidden;">
                    <div class="ep-progress-fill" style="width: {research_pct}%; height: 100%; background: linear-gradient(90deg, #4F46E5, #7C3AED); border-radius: 999px;"></div>
                </div>

                <div style="display: flex; justify-content: space-between; font-size: 0.82rem; margin-bottom: 0.25rem;">
                    <span style="color: #475569; font-weight: 500;">Skills & Project Experience</span>
                    <span style="color: #0F172A; font-weight: 700;">{skills_pct}%</span>
                </div>
                <div class="ep-progress-track" style="margin-top: 0; margin-bottom: 0.75rem; height: 6px; background: #E2E8F0; border-radius: 999px; overflow: hidden;">
                    <div class="ep-progress-fill" style="width: {skills_pct}%; height: 100%; background: linear-gradient(90deg, #4F46E5, #7C3AED); border-radius: 999px;"></div>
                </div>
            </div>
            """
        )
        if st.button("Edit Academic Portfolio →", use_container_width=True, key="profile-breakdown-btn"):
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
            render_html(
                f"""
                <div style="display: flex; align-items: center; justify-content: space-between; padding: 0.35rem 0; border-bottom: 1px solid #F1F5F9;">
                    <div style="display: flex; align-items: center; gap: 0.55rem;">
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
    request_preview = (wf.get("user_request") or "Counseling session")[:60]

    with st.container(key=f"dash-wf-{wf_id}", border=True):
        c1, c2 = st.columns([3.8, 1.2])
        with c1:
            render_html(
                f"""
                <div style="font-weight: 600; font-size: 0.88rem; color: #0F172A;">{request_preview}{'...' if len(wf.get('user_request',''))>60 else ''}</div>
                <div style="font-size: 0.75rem; color: #64748B; margin-top: 0.2rem;">Session: {short_id} · Date: {created}</div>
                """
            )
        with c2:
            render_html(
                f'<span class="ep-badge {status_style}" style="display: block; text-align: center; margin-bottom: 0.35rem;">{status.replace("_", " ").title()}</span>'
            )
            if st.button("Open →", key=f"view-wf-{wf_id}", use_container_width=True):
                st.session_state["current_workflow_id"] = wf_id
                st.switch_page("pages/counseling.py")


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
