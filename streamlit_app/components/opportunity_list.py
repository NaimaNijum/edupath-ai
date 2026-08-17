from __future__ import annotations

import streamlit as st

from components.empty_state import render_empty_state
from components.opportunity_card import render_opportunity_card
from utils.formatting import days_until

_PAGE_SIZE = 12

# label -> (sort key function, reverse)
_SORT_OPTIONS = {
    "Deadline (soonest)": (lambda opp: (days_until(opp.get("deadline")) is None, days_until(opp.get("deadline")) or 0), False),
    "University (A-Z)": (lambda opp: (opp.get("university") or "￿").lower(), False),
    "Funding type": (lambda opp: (opp.get("funding_type") or "￿").lower(), False),
    "Newest added": (lambda opp: opp.get("created_at") or "", True),
}


def _unique_values(opportunities: list[dict], field: str) -> list[str]:
    return sorted({opp[field] for opp in opportunities if opp.get(field)})


def render_opportunity_toolbar(opportunities: list[dict], *, state_prefix: str) -> list[dict]:
    """Renders sort + filter controls and returns the filtered/sorted list.
    Options are derived from the real data present -- nothing hardcoded."""
    countries = _unique_values(opportunities, "country")
    funding_types = _unique_values(opportunities, "funding_type")
    fields = _unique_values(opportunities, "field")

    with st.container(key=f"{state_prefix}-toolbar", border=True):
        toolbar_cols = st.columns([1.2, 1, 1, 1])
        with toolbar_cols[0]:
            sort_label = st.selectbox("Sort by", list(_SORT_OPTIONS.keys()), key=f"{state_prefix}-sort")
        with toolbar_cols[1]:
            country_filter = st.multiselect("Country", countries, key=f"{state_prefix}-country")
        with toolbar_cols[2]:
            funding_filter = st.multiselect("Funding", funding_types, key=f"{state_prefix}-funding")
        with toolbar_cols[3]:
            field_filter = st.multiselect("Research area", fields, key=f"{state_prefix}-field")

    filtered = opportunities
    if country_filter:
        filtered = [o for o in filtered if o.get("country") in country_filter]
    if funding_filter:
        filtered = [o for o in filtered if o.get("funding_type") in funding_filter]
    if field_filter:
        filtered = [o for o in filtered if o.get("field") in field_filter]

    key_func, reverse = _SORT_OPTIONS[sort_label]
    filtered = sorted(filtered, key=key_func, reverse=reverse)
    return filtered


def render_opportunity_grid(opportunities: list[dict], *, state_prefix: str, empty_message: str = "No opportunities match your filters.") -> None:
    if not opportunities:
        render_empty_state("No opportunities found", empty_message, icon="🧭", key=f"{state_prefix}-empty")
        return

    show_key = f"{state_prefix}-show-count"
    show_count = st.session_state.get(show_key, _PAGE_SIZE)
    visible = opportunities[:show_count]

    columns_per_row = 2
    for row_start in range(0, len(visible), columns_per_row):
        row = visible[row_start : row_start + columns_per_row]
        columns = st.columns(columns_per_row)
        for column, opportunity in zip(columns, row, strict=False):
            with column:
                render_opportunity_card(opportunity, key=f"{state_prefix}-{opportunity.get('id')}")

    if show_count < len(opportunities):
        st.write("")
        _, center, _ = st.columns([1, 1, 1])
        with center:
            if st.button(f"Show more ({len(opportunities) - show_count} remaining)", key=f"{state_prefix}-load-more", use_container_width=True):
                st.session_state[show_key] = show_count + _PAGE_SIZE
                st.rerun()
