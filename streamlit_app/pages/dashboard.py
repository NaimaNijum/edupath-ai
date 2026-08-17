from __future__ import annotations

import streamlit as st

from api.client import BackendError, list_opportunities_cached
from components.common import section_header
from components.empty_state import render_empty_state
from components.header import render_page_header
from components.metrics import metric_grid
from components.opportunity_card import render_opportunity_card
from components.profile_card import render_profile_summary
from components.workflow_status import render_workflow_status
from utils.formatting import days_until, greeting_for_now, profile_completion


def render() -> None:
    profile = st.session_state.get("profile")
    name = (profile or {}).get("name") or "there"

    render_page_header(
        f"{greeting_for_now()}, {name.split()[0] if name != 'there' else name}",
        "Your AI-powered academic journey starts here.",
        eyebrow="Dashboard",
    )

    opportunities, catalog_error = _load_catalog()
    _render_metrics(profile, opportunities)

    st.write("")
    section_header("Your Academic Profile")
    if profile:
        render_profile_summary(profile)
    else:
        render_empty_state(
            "Build your academic profile",
            "Tell EduPath AI about your background, goals, and research interests so it can find opportunities that truly fit.",
            icon="🧑‍🎓",
            cta_label="Complete Profile",
            cta_page="pages/profile.py",
            key="dashboard-profile",
        )

    st.write("")
    section_header(
        "Opportunities Worth Exploring",
        "From the EduPath AI opportunity catalog, sorted by the soonest upcoming deadline.",
    )
    if catalog_error:
        st.caption("Couldn't load the opportunity catalog right now.")
    elif not opportunities:
        render_empty_state(
            "No opportunities in the catalog yet",
            "Run a discovery search to help populate opportunities, or check back soon.",
            icon="🧭",
            cta_label="Discover Opportunities",
            cta_page="pages/discover.py",
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

    st.write("")
    section_header("Recent Discovery Run")
    workflow_result = st.session_state.get("workflow_result")
    if not workflow_result:
        render_empty_state(
            "No discovery workflow run yet",
            "Start a search and EduPath AI's agents will analyze your profile and surface matching opportunities.",
            icon="✦",
            cta_label="Discover Opportunities",
            cta_page="pages/discover.py",
            key="dashboard-workflow",
        )
    else:
        render_workflow_status(workflow_result)


def _load_catalog() -> tuple[list[dict], bool]:
    try:
        return list_opportunities_cached(), False
    except BackendError:
        return [], True


def _render_metrics(profile: dict | None, opportunities: list[dict]) -> None:
    saved = st.session_state.get("saved_opportunities", {})
    stages = st.session_state.get("application_stage", {})
    in_progress = sum(1 for stage in stages.values() if stage not in ("Saved", "Accepted", "Rejected"))

    completion = profile_completion(profile)
    cards = [
        {
            "label": "Profile Completion",
            "value": f"{completion}%",
            "progress": completion / 100,
            "key": "completion",
        },
        {
            "label": "Opportunities Found",
            "value": len(opportunities),
            "caption": "In the EduPath AI catalog",
            "key": "opportunities",
        },
        {
            "label": "Saved Opportunities",
            "value": len(saved),
            "caption": "This browser session",
            "key": "saved",
        },
        {
            "label": "Application Progress",
            "value": f"{in_progress} in progress",
            "caption": f"{len(saved)} saved total",
            "key": "applications",
        },
    ]
    metric_grid(cards)


render()
