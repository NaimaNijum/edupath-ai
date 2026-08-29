from __future__ import annotations

import streamlit as st

from api.client import check_health_cached
from api.exceptions import BackendError
from components.auth import render_logout_button
from components.common import render_html
from utils.config import BACKEND_URL
from utils.formatting import initials


def render_sidebar_brand() -> None:
    """Brand mark, shown at the top of the sidebar above the navigation items."""
    with st.sidebar:
        render_html(
            """
            <div class="ep-sidebar-brand-wrapper">
                <div class="ep-brand">
                    <div class="ep-brand-mark">E</div>
                    <div class="ep-brand-text">
                        <div class="ep-brand-title">EduPath AI</div>
                        <div class="ep-brand-subtitle">AI Academic Workforce</div>
                    </div>
                </div>
                <div class="ep-sidebar-divider"></div>
            </div>
            """
        )


def render_sidebar_footer() -> None:
    """Integrated student account card + live backend status pill at the sidebar bottom."""
    with st.sidebar:
        user = st.session_state.get("current_user")
        profile = st.session_state.get("profile")

        render_html('<div class="ep-sidebar-divider" style="margin-top: 1rem; margin-bottom: 0.85rem;"></div>')

        if user:
            name = user.get("name") or user.get("email", "Student Account")
            sub = profile.get("target_degree") or profile.get("field_of_study") or "Active Student"
            avatar_url = user.get("avatar_url")
            avatar_html = (
                f'<img class="ep-avatar-img" src="{avatar_url}" alt="" />'
                if avatar_url
                else f'<div class="ep-avatar">{initials(user.get("name") or user.get("email"))}</div>'
            )
        else:
            name, sub, avatar_html = "Guest Student", "Not signed in", '<div class="ep-avatar">?</div>'

        render_html(
            f"""
            <div class="ep-sidebar-card">
                <div class="ep-user-row">
                    {avatar_html}
                    <div style="flex: 1; min-width: 0;">
                        <div class="ep-user-name">{name}</div>
                        <div class="ep-user-sub">{sub}</div>
                    </div>
                </div>
            </div>
            """
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
    text = "AI Core Online" if online else "AI Core Offline"
    port_text = "FastAPI :8000" if online else "Offline"

    render_html(
        f"""
        <div class="ep-sidebar-status-pill">
            <span class="ep-status-dot {dot_class}"></span>
            <span class="ep-sidebar-status-text">{text}</span>
            <span style="color: #64748B; font-size: 0.68rem; margin-left: auto;">{port_text}</span>
        </div>
        """
    )
