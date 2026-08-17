from __future__ import annotations

import streamlit as st


def metric_card(label: str, value: object, *, caption: str | None = None, progress: float | None = None, key: str) -> None:
    """A single premium metric card. `progress` is 0.0-1.0, optional."""
    with st.container(key=f"metric-card-{key}", border=False):
        st.markdown(f'<div class="ep-metric-label">{label}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="ep-metric-value">{value}</div>', unsafe_allow_html=True)
        if caption:
            st.markdown(f'<div class="ep-metric-caption">{caption}</div>', unsafe_allow_html=True)
        if progress is not None:
            pct = max(0.0, min(1.0, progress)) * 100
            st.markdown(
                f'<div class="ep-progress-track"><div class="ep-progress-fill" style="width:{pct:.0f}%"></div></div>',
                unsafe_allow_html=True,
            )


def metric_grid(cards: list[dict]) -> None:
    """Render a row of metric_card() dicts, e.g.
    {"label": "...", "value": "...", "caption": "...", "progress": 0.5, "key": "profile"}
    """
    if not cards:
        return
    columns = st.columns(len(cards))
    for column, card in zip(columns, cards, strict=True):
        with column:
            metric_card(
                card["label"],
                card["value"],
                caption=card.get("caption"),
                progress=card.get("progress"),
                key=card["key"],
            )
