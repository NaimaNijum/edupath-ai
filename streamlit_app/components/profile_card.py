from __future__ import annotations

import streamlit as st


def render_profile_summary(profile: dict) -> None:
    """Academic profile summary as a badge/field grid. Only renders fields
    the backend actually returned."""
    row1 = st.columns(3)
    _field(row1[0], "Current degree", profile.get("current_degree"))
    _field(row1[1], "Field of study", profile.get("field_of_study"))
    _field(row1[2], "University", profile.get("university"))

    row2 = st.columns(3)
    _field(row2[0], "GPA", profile.get("gpa"))
    _field(row2[1], "Target degree", profile.get("target_degree"))
    _field(row2[2], "Preferred funding", profile.get("preferred_funding"))

    countries = profile.get("target_countries") or []
    interests = profile.get("research_interests") or []

    if countries:
        st.markdown('<div class="ep-field-label">Target countries</div>', unsafe_allow_html=True)
        _badge_row(countries, style="indigo")

    if interests:
        st.markdown('<div class="ep-field-label">Research interests</div>', unsafe_allow_html=True)
        _badge_row(interests, style="purple")


def _field(column, label: str, value: object) -> None:
    with column:
        st.markdown(f'<div class="ep-field-label">{label}</div>', unsafe_allow_html=True)
        display = value if value not in (None, "") else "—"
        st.markdown(f'<div class="ep-field-value">{display}</div>', unsafe_allow_html=True)


def _badge_row(items: list[str], *, style: str = "indigo", limit: int = 8) -> None:
    shown = items[:limit]
    extra = len(items) - len(shown)
    badges = "".join(f'<span class="ep-badge {style}">{item}</span>' for item in shown)
    if extra > 0:
        badges += f'<span class="ep-badge neutral">+{extra} more</span>'
    st.markdown(f'<div class="ep-badge-row">{badges}</div>', unsafe_allow_html=True)


def render_completion_bar(completion: int) -> None:
    st.markdown(
        f"""
        <div class="ep-metric-caption" style="margin-bottom:0;">Profile completion: {completion}%</div>
        <div class="ep-progress-track"><div class="ep-progress-fill" style="width:{completion}%"></div></div>
        """,
        unsafe_allow_html=True,
    )
