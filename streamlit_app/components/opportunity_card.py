from __future__ import annotations

import streamlit as st

from utils.formatting import deadline_urgency, format_amount, format_deadline
from utils.session import is_saved, toggle_saved

_URGENCY_BADGE = {"danger": "danger", "warning": "warning", "neutral": "neutral"}


def _badges(opportunity: dict) -> str:
    chips = []
    if opportunity.get("country"):
        chips.append(f'<span class="ep-badge indigo">{opportunity["country"]}</span>')
    if opportunity.get("degree_level"):
        chips.append(f'<span class="ep-badge purple">{opportunity["degree_level"]}</span>')
    if opportunity.get("funding_type"):
        chips.append(f'<span class="ep-badge success">{opportunity["funding_type"]}</span>')
    deadline = opportunity.get("deadline")
    if deadline:
        urgency = _URGENCY_BADGE.get(deadline_urgency(deadline), "neutral")
        chips.append(f'<span class="ep-badge {urgency}">Due {format_deadline(deadline)}</span>')
    # Match score is only rendered if a future backend version returns one --
    # never fabricated client-side.
    if opportunity.get("match_score") is not None:
        chips.append(f'<span class="ep-badge indigo">{round(opportunity["match_score"] * 100)}% Match</span>')
    return f'<div class="ep-badge-row">{"".join(chips)}</div>' if chips else ""


def render_opportunity_card(opportunity: dict, *, key: str) -> None:
    """Render a single opportunity as a premium card. Only shows fields the
    backend actually returned -- unavailable fields are simply omitted."""
    opportunity_id = opportunity.get("id")
    with st.container(key=f"opp-card-{key}", border=False):
        st.markdown(f'<div class="ep-opp-title">{opportunity.get("title") or "Untitled opportunity"}</div>', unsafe_allow_html=True)

        meta_bits = [value for value in (opportunity.get("university"), opportunity.get("field")) if value]
        if meta_bits:
            st.markdown(f'<div class="ep-opp-meta">{" · ".join(meta_bits)}</div>', unsafe_allow_html=True)

        badges_html = _badges(opportunity)
        if badges_html:
            st.markdown(badges_html, unsafe_allow_html=True)

        amount = format_amount(opportunity.get("amount"))
        if amount:
            st.markdown(f'<div class="ep-metric-caption">Funding amount: {amount}</div>', unsafe_allow_html=True)

        st.write("")
        action_cols = st.columns([1, 1])
        with action_cols[0]:
            if st.button("View Details", key=f"details-{key}", use_container_width=True):
                _render_details_dialog(opportunity)
        with action_cols[1]:
            saved = is_saved(opportunity_id)
            label = "Saved" if saved else "Save"
            icon = ":material/bookmark:" if saved else ":material/bookmark_border:"
            if st.button(label, key=f"save-{key}", icon=icon, use_container_width=True, type="secondary"):
                toggle_saved(opportunity)
                st.rerun()


@st.dialog("Opportunity Details", width="large")
def _render_details_dialog(opportunity: dict) -> None:
    st.markdown(f"### {opportunity.get('title') or 'Untitled opportunity'}")
    badges_html = _badges(opportunity)
    if badges_html:
        st.markdown(badges_html, unsafe_allow_html=True)

    top_cols = st.columns(3)
    with top_cols[0]:
        if opportunity.get("university"):
            st.markdown(f'<div class="ep-field-label">University</div><div class="ep-field-value">{opportunity["university"]}</div>', unsafe_allow_html=True)
    with top_cols[1]:
        if opportunity.get("provider"):
            st.markdown(f'<div class="ep-field-label">Provider</div><div class="ep-field-value">{opportunity["provider"]}</div>', unsafe_allow_html=True)
    with top_cols[2]:
        amount = format_amount(opportunity.get("amount"))
        if amount:
            st.markdown(f'<div class="ep-field-label">Funding amount</div><div class="ep-field-value">{amount}</div>', unsafe_allow_html=True)

    if opportunity.get("description"):
        with st.expander("Description", expanded=True):
            st.write(opportunity["description"])

    eligibility = opportunity.get("eligibility") or {}
    if eligibility:
        with st.expander("Eligibility"):
            for field_key, value in eligibility.items():
                st.markdown(f"- **{field_key.replace('_', ' ').title()}:** {value}")

    st.write("")
    button_cols = st.columns(2)
    with button_cols[0]:
        if opportunity.get("application_url"):
            st.link_button("Apply Now", opportunity["application_url"], use_container_width=True, type="primary")
        else:
            st.button("Apply Now", disabled=True, use_container_width=True, help="No application URL provided by the backend.")
    with button_cols[1]:
        opportunity_id = opportunity.get("id")
        saved = is_saved(opportunity_id)
        label = "Saved to your list" if saved else "Save Opportunity"
        icon = ":material/bookmark:" if saved else ":material/bookmark_border:"
        if st.button(label, key=f"dialog-save-{opportunity_id}", icon=icon, use_container_width=True):
            toggle_saved(opportunity)
            st.rerun()

    if opportunity.get("source_url"):
        st.caption(f"Source: {opportunity['source_url']}")
