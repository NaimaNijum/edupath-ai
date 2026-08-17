from __future__ import annotations

import streamlit as st

from api.client import BackendError, dev_login, get_auth_config, get_current_user, logout
from components.common import render_backend_error
from components.header import render_page_header
from utils.config import BACKEND_URL


def handle_oauth_redirect() -> None:
    """After a real Google login, the backend redirects back to this app
    with ?token=... in the URL. Store it and scrub it from the visible URL
    immediately -- a bearer token doesn't belong sitting in browser history."""
    token = st.query_params.get("token")
    if token:
        st.session_state["auth_token"] = token
        st.session_state["current_user"] = None
        st.query_params.clear()
        st.rerun()


def ensure_current_user() -> dict | None:
    """Loads /auth/me once per session for the stored token. If the token
    turns out to be invalid/expired/revoked, clears it so the login gate
    reappears instead of the app silently misbehaving."""
    if not st.session_state.get("auth_token"):
        return None
    if st.session_state.get("current_user"):
        return st.session_state["current_user"]
    try:
        user = get_current_user()
    except BackendError:
        st.session_state["auth_token"] = None
        st.session_state["current_user"] = None
        return None
    st.session_state["current_user"] = user
    return user


def render_login_gate() -> None:
    """Full-page sign-in UI shown instead of the app when not logged in."""
    render_page_header(
        "Welcome to EduPath AI",
        "Sign in to build your academic profile and let EduPath AI discover opportunities for you.",
        eyebrow="Sign In",
    )

    try:
        config = get_auth_config()
    except BackendError as error:
        render_backend_error(error, key="auth-config")
        return

    _, center, _ = st.columns([1, 1.4, 1])
    with center:
        with st.container(key="login-card", border=True):
            if config["mode"] == "google":
                login_url = f"{BACKEND_URL}{config['google_login_url']}"
                st.link_button("Sign in with Google", login_url, type="primary", use_container_width=True, icon=":material/login:")
            else:
                st.info(
                    "Google OAuth isn't configured on this backend, so dev-mode sign-in is active. "
                    "Any email works -- no password needed.",
                    icon=":material/info:",
                )
                with st.form("dev_login_form", border=False):
                    email = st.text_input("Email")
                    name = st.text_input("Name (optional)")
                    submitted = st.form_submit_button("Continue", type="primary", use_container_width=True)

                if submitted:
                    if not email.strip():
                        st.warning("Enter an email to continue.", icon=":material/warning:")
                    else:
                        try:
                            result = dev_login(email.strip(), name.strip() or None)
                        except BackendError as error:
                            render_backend_error(error, key="dev-login")
                        else:
                            st.session_state["auth_token"] = result["access_token"]
                            st.session_state["current_user"] = result["user"]
                            st.rerun()


def render_logout_button() -> None:
    if st.button("Log out", icon=":material/logout:", use_container_width=True, key="logout-button"):
        try:
            logout()
        except BackendError:
            pass  # token may already be invalid/expired -- still clear local state
        st.session_state["auth_token"] = None
        st.session_state["current_user"] = None
        st.rerun()
