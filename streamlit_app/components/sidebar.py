from __future__ import annotations

import streamlit as st

from api.client import check_health_cached
from api.exceptions import BackendError
from components.auth import render_logout_button
from utils.config import BACKEND_URL
from utils.formatting import initials


def render_sidebar_brand() -> None:
    """Brand mark, shown above the auto-generated st.navigation link list."""
    with st.sidebar:
        st.markdown(
            """
            <div class="ep-brand">
                <div class="ep-brand-mark">E</div>
                <div class="ep-brand-text">
                    <div class="ep-brand-title">EduPath AI</div>
                    <div class="ep-brand-subtitle">AI Academic Navigator</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_sidebar_footer() -> None:
    """Signed-in user card + backend status, shown below the nav link list."""
    with st.sidebar:
        st.write("")
        user = st.session_state.get("current_user")
        profile = st.session_state.get("profile")

        with st.container(key="sidebar-user-card", border=False):
            if user:
                name = user.get("name") or user.get("email", "Account")
                sub = profile.get("target_degree") if profile else "No academic profile yet"
                avatar_url = user.get("avatar_url")
                avatar_html = (
                    f'<img class="ep-avatar-img" src="{avatar_url}" alt="" />'
                    if avatar_url
                    else f'<div class="ep-avatar">{initials(user.get("name") or user.get("email"))}</div>'
                )
            else:
                name, sub, avatar_html = "Guest", "Not signed in", '<div class="ep-avatar">?</div>'

            st.markdown(
                f"""
                <div class="ep-sidebar-card">
                    <div class="ep-user-row">
                        {avatar_html}
                        <div>
                            <div class="ep-user-name">{name}</div>
                            <div class="ep-user-sub">{sub}</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        if user:
            render_logout_button()

        _render_backend_status()


def _render_backend_status() -> None:
    try:
        check_health_cached()
        online = True
    except BackendError:
        online = False

    dot_class = "online" if online else "offline"
    text = "Backend online" if online else "Backend offline"
    st.markdown(
        f"""
        <div style="padding: 0.6rem 0.2rem 0 0.2rem;">
            <span class="ep-status-dot {dot_class}"></span>
            <span class="ep-sidebar-status-text">{text}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption(BACKEND_URL)
