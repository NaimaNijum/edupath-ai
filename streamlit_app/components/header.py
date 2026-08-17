from __future__ import annotations

import streamlit as st


def render_page_header(title: str, subtitle: str | None = None, *, eyebrow: str | None = None) -> None:
    """Standard page header: optional eyebrow badge, title, subtitle."""
    eyebrow_html = f'<div class="ep-eyebrow">{eyebrow}</div>' if eyebrow else ""
    subtitle_html = f'<div class="ep-page-subtitle">{subtitle}</div>' if subtitle else ""
    st.markdown(
        f"""
        <div class="ep-page-header">
            {eyebrow_html}
            <div class="ep-page-title">{title}</div>
            {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hero(title: str, subtitle: str | None = None, *, key: str = "main") -> None:
    """Gradient hero banner used on the discover page."""
    with st.container(key=f"hero-{key}", border=False):
        render_page_header(title, subtitle)
