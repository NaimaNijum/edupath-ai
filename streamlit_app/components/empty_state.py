from __future__ import annotations

import streamlit as st


def render_empty_state(
    title: str,
    description: str | None = None,
    *,
    icon: str = "🔍",
    cta_label: str | None = None,
    cta_page: str | None = None,
    key: str = "default",
) -> None:
    """A polished empty state card, optionally with a call-to-action that
    navigates to another page via st.page_link."""
    with st.container(key=f"ep-empty-{key}", border=False):
        st.markdown(f'<div class="ep-empty-icon">{icon}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="ep-empty-title">{title}</div>', unsafe_allow_html=True)
        if description:
            st.markdown(f'<div class="ep-empty-desc">{description}</div>', unsafe_allow_html=True)
        if cta_label and cta_page:
            st.write("")
            _, center, _ = st.columns([1, 1.2, 1])
            with center:
                st.page_link(cta_page, label=cta_label, icon=":material/arrow_forward:", use_container_width=True)


def render_error_card(title: str, description: str, *, retry_key: str | None = None) -> bool:
    """Returns True if the user clicked Retry."""
    retried = False
    with st.container(key=f"ep-error-{retry_key or title}", border=False):
        st.markdown(f'<div class="ep-empty-title">{title}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="ep-empty-desc" style="margin:0">{description}</div>', unsafe_allow_html=True)
        if retry_key:
            st.write("")
            retried = st.button("Retry", key=f"retry-{retry_key}", icon=":material/refresh:")
    return retried
