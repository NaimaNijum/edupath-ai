"""
Dashboard — Student Personal Command Center (Notion-style Workspace).
"""
from __future__ import annotations

import streamlit as st

from api.client import BackendError, list_opportunities_cached, list_workflows
from components.common import render_html, section_header
from components.empty_state import render_empty_state
from components.header import render_page_header
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

    _render_command_banner(profile, completion, workflows)
    st.write("")
    _render_student_metrics(profile, completion, opportunities, workflows)
    st.write("")

    left_col, right_col = st.columns([1.32, 0.92], gap="large")

    with left_col:
        section_header("Active Counseling Pipeline", "Live multi-agent execution & matching.")
        _render_current_counseling_card(workflows)

        st.write("")
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
        section_header("Academic Portfolio Strength", "Credentials available for AI matching.")
        _render_profile_breakdown_card(profile)

        st.write("")
        section_header("AI Agent Workforce", "Specialist agents ready to deploy.")
        _render_workforce_status_widget()

        st.write("")
        section_header("Workspace Shortcuts")
        _render_quick_actions()

    st.write("")
    section_header(
        "Recommended Opportunities",
        "Curated from the EduPath AI database with upcoming deadlines.",
    )
    _render_opportunities_grid(opportunities, catalog_error)

    workflow_result = st.session_state.get("workflow_result")
    if workflow_result:
        st.write("")
        section_header("Latest AI Counseling Report", "Detailed findings from your most recent session.")
        st.caption(f"Showing session {workflow_result.get('workflow_id', 'unknown')}")
        render_workflow_status(workflow_result)


def _render_command_banner(profile: dict | None, completion: int, workflows: list[dict]) -> None:
    name = (profile or {}).get("name") or "Student"
    field_of_study = (profile or {}).get("field_of_study") or "Academic Profile"
    current_degree = (profile or {}).get("current_degree") or (profile or {}).get("academic_level") or "Student Record"
    gpa = (profile or {}).get("gpa")
    gpa_text = f"GPA {gpa}/4.0" if gpa else "GPA not set"
    is_profile_ready = bool(profile and profile.get("gpa") and profile.get("field_of_study"))

    summary_items = [
        ("Verified Record", gpa_text),
        ("Major", field_of_study),
        ("Degree", current_degree),
        ("Portfolio Score", f"{completion}%"),
    ]

    button_label = "Start AI Counseling" if is_profile_ready else "Complete Profile to Unlock"
    button_page = "pages/counseling.py" if is_profile_ready else "pages/profile.py"
    button_help = "Launch the multi-agent counseling wizard" if is_profile_ready else "Complete the profile before counseling can run"

    render_html(
        f"""
        <div class="ep-dashboard-hero">
            <div class="ep-dashboard-hero-top">
                <div class="ep-dashboard-profile-meta">
                    <div class="ep-dashboard-avatar">{name[:1].upper()}</div>
                    <div>
                        <div class="ep-dashboard-eyebrow">Student Workspace</div>
                        <div class="ep-dashboard-name">{name}</div>
                    </div>
                </div>
                <div class="ep-dashboard-stat-pill">{completion}% Portfolio Complete</div>
            </div>

            <div class="ep-dashboard-hero-grid">
                <div class="ep-dashboard-hero-copy">
                    <div class="ep-dashboard-subhead">Academic Command Center</div>
                    <div class="ep-dashboard-text">{field_of_study} • {current_degree}</div>
                    <div class="ep-dashboard-meta">Verified academic record, funding intelligence, and faculty alignment are ready for review.</div>
                </div>
                <div class="ep-dashboard-cta-panel">
                    <div class="ep-dashboard-cta-label">Primary Action</div>
                    <div class="ep-dashboard-cta-value">{button_label}</div>
                </div>
            </div>

            <div class="ep-dashboard-mini-grid">
                {''.join(f'<div class="ep-dashboard-mini-card"><div class="ep-dashboard-mini-label">{label}</div><div class="ep-dashboard-mini-value">{value}</div></div>' for label, value in summary_items)}
            </div>
        </div>
        """
    )

    if is_profile_ready:
        st.page_link("pages/counseling.py", label=button_label, icon=":material/auto_awesome:", use_container_width=True)
    else:
        st.page_link("pages/profile.py", label=button_label, icon=":material/assignment_turned_in:", use_container_width=True)


def _render_student_metrics(profile: dict | None, completion: int, opportunities: list[dict], workflows: list[dict]) -> None:
    saved = st.session_state.get("saved_opportunities", {})
    funding_count = sum(1 for opp in opportunities if "fund" in (opp.get("funding_type") or "").lower())
    verified_matches = len(opportunities)

    cards = [
        {"label": "Portfolio Strength", "value": f"{completion}%", "progress": completion / 100, "caption": "Completion signal", "tone": "indigo"},
        {"label": "Counseling Sessions", "value": max(len(workflows), 1 if st.session_state.get("workflow_result") else 0), "caption": "AI analyses on record", "progress": min(len(workflows) / 6, 1), "tone": "purple"},
        {"label": "Verified Matches", "value": verified_matches, "caption": "Programs in shortlist", "progress": min(verified_matches / 8, 1), "tone": "success"},
        {"label": "Funding & Waivers", "value": funding_count or len(saved), "caption": "Assistantships & grants", "progress": min((funding_count or len(saved)) / 5, 1), "tone": "warning"},
    ]

    columns = st.columns(len(cards))
    for column, card in zip(columns, cards, strict=True):
        with column:
            render_html(
                f"""
                <div class="ep-dashboard-metric-card ep-dashboard-metric-{card['tone']}">
                    <div class="ep-metric-top-row">
                        <div class="ep-metric-label">{card['label']}</div>
                        <span class="ep-metric-dot ep-metric-dot-{card['tone']}"></span>
                    </div>
                    <div class="ep-metric-value">{card['value']}</div>
                    <div class="ep-metric-caption">{card['caption']}</div>
                    <div class="ep-progress-track"><div class="ep-progress-fill" style="width: {max(8, min(100, (card['progress'] or 0) * 100))}%"></div></div>
                </div>
                """
            )


def _render_current_counseling_card(workflows: list[dict]) -> None:
    latest_wf = workflows[0] if workflows else None
    latest_result = st.session_state.get("workflow_result")
    target = "AI Multi-Agent Counseling Pipeline"
    if latest_wf and latest_wf.get("user_request"):
        target = latest_wf.get("user_request")[:52] + ("..." if len(latest_wf.get("user_request", "")) > 52 else "")

    status = (latest_result or {}).get("workflow_status") or (latest_wf or {}).get("status") or "ready"
    is_done = status == "completed"
    state_label = "Completed" if is_done else "Ready"
    state_style = "success" if is_done else "indigo"

    stage_rows = [
        ("Profile Academic Signal Analysis", "✓ Active"),
        ("University & Program Matching", "✓ Active"),
        ("Scholarship & Assistantship Discovery", "✓ Completed" if is_done else "● Ready"),
        ("Faculty & Research Alignment", "✓ Completed" if is_done else "● Ready"),
    ]

    stages_html = "".join(
        f'<div class="ep-pipeline-row"><span>{label}</span><span class="ep-pipeline-state">{value}</span></div>'
        for label, value in stage_rows
    )

    render_html(
        f"""
        <div class="ep-surface-card ep-pipeline-card">
            <div class="ep-card-header-row">
                <div>
                    <div class="ep-card-title">{target}</div>
                    <div class="ep-card-caption">Automated 8-agent execution pipeline</div>
                </div>
                <span class="ep-badge {state_style}">{state_label}</span>
            </div>
            <div class="ep-pipeline-list">{stages_html}</div>
        </div>
        """
    )

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Launch Counseling →", type="primary", use_container_width=True, key="current-counseling-continue"):
            st.switch_page("pages/counseling.py")
    with c2:
        if st.button("AI Insights & Memory", use_container_width=True, key="current-counseling-trace"):
            st.switch_page("pages/settings.py")


def _render_profile_breakdown_card(profile: dict | None) -> None:
    gpa_filled = bool(profile and profile.get("gpa") and profile.get("field_of_study"))
    research_filled = bool(profile and (profile.get("research_interests") or profile.get("publications")))
    skills_filled = bool(profile and (profile.get("skills") or profile.get("projects") or profile.get("work_experience")))

    academic_pct = 100 if gpa_filled else 30
    research_pct = 95 if research_filled else 25
    skills_pct = 90 if skills_filled else 35

    bars = [
        ("Academic Records", academic_pct),
        ("Research & Publications", research_pct),
        ("Skills & Project Experience", skills_pct),
    ]
    content = "".join(
        f'<div class="ep-progress-block"><div class="ep-progress-row"><span>{label}</span><span>{pct}%</span></div><div class="ep-progress-track"><div class="ep-progress-fill" style="width: {pct}%;"></div></div></div>'
        for label, pct in bars
    )

    render_html(
        f"""
        <div class="ep-surface-card">
            {content}
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

    rows = "".join(
        f'<div class="ep-agent-row"><div class="ep-agent-left"><span class="ep-agent-icon">{icon}</span><div><div class="ep-agent-name">{name}</div><div class="ep-agent-meta">{desc}</div></div></div><span class="ep-badge {badge_style}">Ready</span></div>'
        for name, icon, desc, badge_style in agents
    )

    render_html(f'<div class="ep-surface-card">{rows}</div>')


def _render_quick_actions() -> None:
    actions = [
        ("Start AI Counseling", "pages/counseling.py", "Deploy all 8 agents on your academic profile."),
        ("Explore Opportunities", "pages/discover.py", "Browse catalog and saved bookmarks."),
        ("Document Studio", "pages/sop.py", "Draft tailored SOPs and outreach emails."),
        ("Application Tracker", "pages/tracker.py", "Manage admissions milestones and stages."),
    ]

    cards = "".join(
        f'<div class="ep-shortcut-card"><div class="ep-shortcut-title">{label}</div><div class="ep-shortcut-body">{caption}</div><a href="{page}" class="ep-shortcut-link">Open →</a></div>'
        for label, page, caption in actions
    )
    render_html(f'<div class="ep-shortcut-grid">{cards}</div>')

    for label, page, _ in actions:
        st.page_link(page, label=label, icon=":material/arrow_forward:")


def _render_opportunities_grid(opportunities: list[dict], catalog_error: bool) -> None:
    if catalog_error:
        st.caption("Couldn't connect to the opportunity catalog right now.")
        return
    if not opportunities:
        render_empty_state(
            "No opportunities in the catalog yet",
            "Run a counseling session to populate the catalog with verified programs.",
            icon="🧭",
            cta_label="Start Counseling",
            cta_page="pages/counseling.py",
            key="dashboard-opps",
        )
        return

    upcoming = sorted(
        opportunities,
        key=lambda opp: (days_until(opp.get("deadline")) is None, days_until(opp.get("deadline")) or 0),
    )[:3]

    cards = []
    for opp in upcoming:
        deadline = opp.get("deadline") or "TBD"
        days_left = days_until(deadline)
        urgency = "Due soon" if days_left is not None and days_left <= 30 else "Open"
        rows = [
            opp.get("program_name") or opp.get("title") or "Program",
            opp.get("university_name") or opp.get("institution") or "University",
            opp.get("degree_level") or "Program",
            opp.get("funding_type") or "Funding",
        ]
        cards.append(
            f"""
            <div class="ep-opportunity-card">
                <div class="ep-opportunity-top">
                    <div class="ep-opportunity-logo">{(rows[1][:2] if rows[1] else 'ED').upper()}</div>
                    <span class="ep-badge {'warning' if urgency == 'Due soon' else 'success'}">{urgency}</span>
                </div>
                <div class="ep-opportunity-title">{rows[0]}</div>
                <div class="ep-opportunity-school">{rows[1]}</div>
                <div class="ep-opportunity-tags">
                    <span class="ep-chip">{rows[2]}</span>
                    <span class="ep-chip ep-chip-soft">{rows[3]}</span>
                </div>
                <div class="ep-opportunity-meta">Deadline: {deadline}</div>
            </div>
            """
        )

    render_html(f'<div class="ep-opportunity-grid">{"".join(cards)}</div>')


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
    request_preview = (wf.get("user_request") or "Counseling session")[:64]

    render_html(
        f"""
        <div class="ep-session-row">
            <div class="ep-session-main">
                <div class="ep-session-title">{request_preview}{'...' if len(wf.get('user_request', '')) > 64 else ''}</div>
                <div class="ep-session-meta">Session: {short_id} • Date: {created}</div>
            </div>
            <div class="ep-session-actions">
                <span class="ep-badge {status_style}">{status.replace('_', ' ').title()}</span>
            </div>
        </div>
        """
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
