from __future__ import annotations

import streamlit as st

from components.empty_state import render_empty_state
from components.header import render_page_header
from components.opportunity_list import render_opportunity_grid, render_opportunity_toolbar


def render() -> None:
    render_page_header(
        "Saved Opportunities",
        "Opportunities you've bookmarked to review or apply to later.",
        eyebrow="Saved",
    )
    st.caption(
        "Saved opportunities live in this browser session only -- the backend doesn't "
        "yet support persisting them, so this list resets if you restart the app."
    )

    saved = st.session_state.get("saved_opportunities", {})
    if not saved:
        render_empty_state(
            "No saved opportunities",
            "Save opportunities you're interested in to keep them here.",
            icon="🔖",
            cta_label="Discover Opportunities",
            cta_page="pages/discover.py",
            key="saved-empty",
        )
        return

    opportunities = list(saved.values())

    header_cols = st.columns([5, 1])
    with header_cols[1]:
        if st.button("Clear all", icon=":material/delete_sweep:", use_container_width=True):
            st.session_state["saved_opportunities"] = {}
            st.session_state["application_stage"] = {}
            st.rerun()

    filtered = render_opportunity_toolbar(opportunities, state_prefix="saved")
    render_opportunity_grid(filtered, state_prefix="saved")


render()
