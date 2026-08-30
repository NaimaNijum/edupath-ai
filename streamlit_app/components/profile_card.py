from __future__ import annotations

import streamlit as st
from components.common import render_html


def _html(content: str) -> None:
    render_html(content)


def render_profile_summary(profile: dict | None) -> None:
    """Academic profile summary as a badge/field grid. Only renders fields
    the backend actually returned."""
    profile = profile or {}
    with st.container(key="profile-summary-card", border=True):
        row1 = st.columns(3)
        _field(row1[0], "Current Degree", profile.get("current_degree"))
        _field(row1[1], "Field of Study", profile.get("field_of_study"))
        _field(row1[2], "University", profile.get("university"))

        row2 = st.columns(3)
        _field(row2[0], "GPA", profile.get("gpa"))
        _field(row2[1], "Target Degree", profile.get("target_degree"))
        _field(row2[2], "Preferred Funding", profile.get("preferred_funding"))

        countries = profile.get("target_countries") or []
        interests = profile.get("research_interests") or []

        if countries:
            _html('<div class="ep-field-label" style="margin-top: 0.5rem;">Target Countries</div>')
            _badge_row(countries, style="indigo")

        if interests:
            _html('<div class="ep-field-label" style="margin-top: 0.5rem;">Research Interests</div>')
            _badge_row(interests, style="purple")


def _field(column, label: str, value: object) -> None:
    with column:
        _html(f'<div class="ep-field-label">{label}</div>')
        display = value if value not in (None, "") else "—"
        _html(f'<div class="ep-field-value">{display}</div>')


def _badge_row(items: list[str], *, style: str = "indigo", limit: int = 8) -> None:
    shown = items[:limit]
    extra = len(items) - len(shown)
    badges = "".join(f'<span class="ep-badge {style}">{item}</span>' for item in shown)
    if extra > 0:
        badges += f'<span class="ep-badge neutral">+{extra} more</span>'
    _html(f'<div class="ep-badge-row">{badges}</div>')


def render_completion_bar(completion: int) -> None:
    _html(
        f"""
        <div class="ep-metric-caption" style="margin-bottom:0;">Profile completion: {completion}%</div>
        <div class="ep-progress-track"><div class="ep-progress-fill" style="width:{completion}%"></div></div>
        """
    )
