from __future__ import annotations

import textwrap
import streamlit as st

from components.evidence import render_evidence_list

_ELIGIBILITY_STYLE = {
    "verified_eligible": "success",
    "likely_eligible": "success",
    "verified_ineligible": "danger",
    "unknown": "neutral",
}

_SCORE_LABELS = {
    "research_match": "Research Match",
    "eligibility": "Eligibility",
    "funding": "Funding",
    "professor_match": "Professor Match",
    "university_tier": "University Tier",
    "deadline_urgency": "Deadline Urgency",
}


def _html(content: str) -> None:
    st.markdown(textwrap.dedent(content).strip(), unsafe_allow_html=True)


def _tier_label(overall_score: float | None) -> tuple[str, str]:
    """Returns (tier_name, tier_css_class)."""
    if overall_score is None:
        return ("—", "neutral")
    pct = overall_score * 100
    if pct >= 82:
        return ("Reach", "reach")
    if pct >= 62:
        return ("Target", "target")
    return ("Safe", "safe")


def _score_bars_html(score_breakdown: dict) -> str:
    rows = ""
    for key, label in _SCORE_LABELS.items():
        score = score_breakdown.get(key)
        if score is None:
            continue
        pct = round(score * 100)
        color = "#16A34A" if pct >= 75 else "#4F46E5" if pct >= 50 else "#F59E0B"
        rows += f"""
        <div class="ep-score-bar-row">
          <span class="ep-score-bar-label">{label}</span>
          <div class="ep-score-bar-track">
            <div class="ep-score-bar-fill" style="width:{pct}%;background:{color};"></div>
          </div>
          <span class="ep-score-bar-value">{pct}%</span>
        </div>
        """
    return rows


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
    Returns True if `selectable` and the user picked this one (checkbox).
    """
    selected = False
    with st.container(key=f"ranked-card-{key}", border=True):
        title = candidate.get("title") or "Untitled opportunity"
        rank_str = f"#{ranked['rank']} " if ranked else ""

        # Title row with tier badge
        overall_score = (ranked or {}).get("overall_score")
        tier_name, tier_cls = _tier_label(overall_score)
        overall_pct = round(overall_score * 100) if overall_score is not None else None
        overall_str = f"{overall_pct}%" if overall_pct is not None else ""

        col_title, col_score = st.columns([4, 1])
        with col_title:
            _html(f'<div class="ep-opp-title">{rank_str}{title}</div>')
        with col_score:
            if overall_str:
                _html(
                    f"""
                    <div style="text-align:right;">
                      <div class="ep-score-big">{overall_str}</div>
                      <span class="ep-tier-badge {tier_cls}">{tier_name}</span>
                    </div>
                    """
                )

        # University / professor meta
        meta = [bit for bit in (candidate.get("university"), candidate.get("professor_name")) if bit]
        if meta:
            _html(f'<div class="ep-opp-meta">{" · ".join(meta)}</div>')

        # Badges
        badges = []
        if candidate.get("country"):
            badges.append(f'<span class="ep-badge indigo">{candidate["country"]}</span>')
        if candidate.get("degree_level"):
            badges.append(f'<span class="ep-badge purple">{candidate["degree_level"]}</span>')
        if candidate.get("funding_type"):
            funding = candidate["funding_type"]
            funding_style = "success" if "full" in funding.lower() else "warning"
            badges.append(f'<span class="ep-badge {funding_style}">{funding}</span>')
        if eligibility is not None:
            elig_key = eligibility.get("eligible") or eligibility.get("verdict") or "unknown"
            style = _ELIGIBILITY_STYLE.get(elig_key, "neutral")
            badges.append(
                f'<span class="ep-badge {style}">{elig_key.replace("_", " ").title()}</span>'
            )
        if badges:
            _html(f'<div class="ep-badge-row">{"".join(badges)}</div>')

        # Research match explanation
        if research_match and research_match.get("explanation"):
            st.caption(research_match["explanation"][:150])

        # Score breakdown
        score_breakdown = (ranked or {}).get("component_scores") or (ranked or {}).get("score_breakdown") or {}
        if score_breakdown:
            with st.expander("Score breakdown & evidence", icon=":material/bar_chart:"):
                bars_html = _score_bars_html(score_breakdown)
                if bars_html:
                    _html(f'<div class="ep-score-breakdown">{bars_html}</div>')

                if eligibility and eligibility.get("explanation"):
                    st.markdown(f"**Eligibility:** {eligibility['explanation']}")
                if eligibility and eligibility.get("reasoning"):
                    st.caption(eligibility["reasoning"][:200])

                evidence = candidate.get("evidence") or []
                if evidence:
                    st.markdown("**Sources**")
                    render_evidence_list(evidence)
                if candidate.get("official_url") or candidate.get("application_url"):
                    url = candidate.get("official_url") or candidate.get("application_url")
                    st.link_button("Official Page ↗", url, use_container_width=True)
        else:
            with st.expander("Evidence & details", icon=":material/fact_check:"):
                if eligibility and eligibility.get("explanation"):
                    st.markdown(f"**Eligibility:** {eligibility['explanation']}")
                render_evidence_list(candidate.get("evidence") or [])
                if candidate.get("official_url"):
                    st.link_button("Official Link ↗", candidate["official_url"], use_container_width=True)

        if selectable:
            selected = st.checkbox("Select for SOP generation", key=f"select-{key}")

    return selected
