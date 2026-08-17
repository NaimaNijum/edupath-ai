from __future__ import annotations

import streamlit as st

from components.evidence import render_evidence_list

_ELIGIBILITY_STYLE = {
    "verified_eligible": "success",
    "likely_eligible": "success",
    "verified_ineligible": "danger",
    "unknown": "neutral",
}


def render_ranked_opportunity_card(
    candidate: dict,
    *,
    key: str,
    ranked: dict | None = None,
    eligibility: dict | None = None,
    research_match: dict | None = None,
    selectable: bool = False,
) -> bool:
    """Renders one CandidateOpportunity enriched with its real verdicts.
    Returns True if `selectable` and the user picked this one (radio)."""
    selected = False
    with st.container(key=f"ranked-card-{key}", border=False):
        title = candidate.get("title") or "Untitled opportunity"
        if ranked:
            title = f"#{ranked['rank']} {title}"
        st.markdown(f'<div class="ep-opp-title">{title}</div>', unsafe_allow_html=True)

        meta = [bit for bit in (candidate.get("university"), candidate.get("professor_name")) if bit]
        if meta:
            st.markdown(f'<div class="ep-opp-meta">{" · ".join(meta)}</div>', unsafe_allow_html=True)

        badges = []
        if candidate.get("country"):
            badges.append(f'<span class="ep-badge indigo">{candidate["country"]}</span>')
        if candidate.get("degree_level"):
            badges.append(f'<span class="ep-badge purple">{candidate["degree_level"]}</span>')
        if candidate.get("funding_type"):
            badges.append(f'<span class="ep-badge success">{candidate["funding_type"]}</span>')
        if ranked is not None:
            badges.append(f'<span class="ep-badge indigo">{round(ranked["overall_score"] * 100)}% Overall</span>')
        if eligibility is not None:
            style = _ELIGIBILITY_STYLE.get(eligibility.get("eligible"), "neutral")
            badges.append(f'<span class="ep-badge {style}">{(eligibility.get("eligible") or "").replace("_", " ").title()}</span>')
        if badges:
            st.markdown(f'<div class="ep-badge-row">{"".join(badges)}</div>', unsafe_allow_html=True)

        if research_match and research_match.get("explanation"):
            st.caption(research_match["explanation"])

        with st.expander("Evidence & details", icon=":material/fact_check:"):
            if ranked and ranked.get("score_breakdown"):
                st.markdown("**Score breakdown**")
                for component, score in ranked["score_breakdown"].items():
                    st.caption(f"{component.replace('_', ' ').title()}: {score:.2f}")
            if eligibility and eligibility.get("explanation"):
                st.markdown(f"**Eligibility:** {eligibility['explanation']}")
            st.markdown("**Evidence**")
            render_evidence_list(candidate.get("evidence") or [])
            if candidate.get("official_url"):
                st.link_button("Official Link", candidate["official_url"], use_container_width=True)

        if selectable:
            selected = st.checkbox("Select for approval", key=f"select-{key}")

    return selected
