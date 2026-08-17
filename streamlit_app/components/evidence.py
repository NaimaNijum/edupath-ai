from __future__ import annotations

import streamlit as st


def render_evidence_list(evidence: list[dict]) -> None:
    """Renders Evidence entries (app.schemas.opportunity_candidate.Evidence).
    Only shows what the backend actually attached -- an empty list renders
    an honest "no evidence" note rather than nothing at all."""
    if not evidence:
        st.caption("No evidence attached to this claim.")
        return

    for item in evidence:
        verified = item.get("verified")
        badge_style = "success" if verified else "warning"
        badge_text = "Verified" if verified else "Unverified"
        source_type = (item.get("source_type") or "").replace("_", " ").title()

        st.markdown(
            f'<div class="ep-badge-row">'
            f'<span class="ep-badge {badge_style}">{badge_text}</span>'
            f'<span class="ep-badge neutral">{source_type}</span>'
            f"</div>",
            unsafe_allow_html=True,
        )
        if item.get("claim"):
            st.caption(item["claim"])
        if item.get("source_url"):
            st.markdown(f"[{item.get('source_title') or item['source_url']}]({item['source_url']})")
