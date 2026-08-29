from __future__ import annotations

import streamlit as st

from api.client import BackendError, dev_login, get_auth_config, get_current_user, get_my_profile, logout
from components.common import render_backend_error
from utils.config import BACKEND_URL


def _clear_session_auth() -> None:
    st.session_state["auth_token"] = None
    st.session_state["current_user"] = None
    st.session_state["profile_id"] = None
    st.session_state["profile"] = None


def _hydrate_profile_from_backend() -> None:
    """Fetch the user's profile and store it in the app session state.

    This keeps the frontend's profile_id/profile values aligned with the logged-in
    user after login, page refresh, or route changes.
    """
    try:
        profile = get_my_profile()
    except BackendError:
        st.session_state["profile_id"] = None
        st.session_state["profile"] = None
        return

    if profile:
        st.session_state["profile_id"] = profile["id"]
        st.session_state["profile"] = profile
    else:
        st.session_state["profile_id"] = None
        st.session_state["profile"] = None


def handle_oauth_redirect() -> None:
    """After a real Google login, the backend redirects back to this app
    with ?token=... in the URL. Store it and scrub it from the visible URL
    immediately -- a bearer token doesn't belong sitting in browser history."""
    token = st.query_params.get("token")
    if token:
        st.session_state["auth_token"] = token
        st.session_state["current_user"] = None
        st.session_state["profile_id"] = None
        st.session_state["profile"] = None
        st.query_params.clear()
        st.rerun()


def ensure_current_user() -> dict | None:
    """Loads /auth/me once per session for the stored token. If the token
    turns out to be invalid/expired/revoked, clears it so the login gate
    reappears instead of the app silently misbehaving."""
    if not st.session_state.get("auth_token"):
        st.session_state["profile_id"] = None
        st.session_state["profile"] = None
        return None

    if st.session_state.get("current_user"):
        user = st.session_state["current_user"]
        if not st.session_state.get("profile_id") or not st.session_state.get("profile"):
            _hydrate_profile_from_backend()
        return user

    try:
        user = get_current_user()
    except BackendError:
        _clear_session_auth()
        return None

    st.session_state["current_user"] = user
    _hydrate_profile_from_backend()
    return user


def require_auth() -> None:
    """Guard the whole app: no session, no access to any page."""
    if not st.session_state.get("auth_token"):
        render_login_gate()
        st.stop()


def render_login_gate() -> None:
    """Full-page, modern split sign-in UI."""
    # Hide Streamlit navigation & sidebar when showing the login gate
    st.markdown(
        """
        <style>
            [data-testid="stSidebar"] { display: none !important; }
            [data-testid="stDecoration"] { display: none !important; }
            [data-testid="stStatusWidget"] { display: none !important; }
            header[data-testid="stHeader"] { display: none !important; }
            .block-container {
                max-width: 1040px !important;
                padding-top: 2.5rem !important;
                padding-bottom: 3.5rem !important;
                margin: 0 auto !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Top navigation back button
    col_back, _ = st.columns([1, 4])
    with col_back:
        if st.button("← Back to Home", key="login-back-home", use_container_width=True):
            st.query_params.clear()
            st.rerun()

    st.write("")

    # Split layout: Left = Branding/Value Props, Right = Auth Card
    left_col, right_col = st.columns([1.1, 0.9], gap="large")

    with left_col:
        st.markdown(
            """
            <div class="ep-auth-branding-panel">
                <div class="ep-brand" style="margin-bottom: 1.5rem;">
                    <div class="ep-brand-mark" style="width: 42px; height: 42px; font-size: 1.2rem; border-radius: 11px;">E</div>
                    <div class="ep-brand-text">
                        <div class="ep-brand-title" style="font-size: 1.25rem; color: #0F172A; font-weight: 800;">EduPath AI</div>
                        <div class="ep-brand-subtitle" style="color: #64748B;">AI Academic Navigator</div>
                    </div>
                </div>

                <div class="ep-eyebrow" style="margin-bottom: 0.75rem;">✦ AI ADMISSIONS WORKFORCE</div>
                <h1 style="font-size: 2.1rem; font-weight: 800; color: #0B1220; line-height: 1.2; letter-spacing: -0.04em; margin-bottom: 0.9rem;">
                    Your AI-powered path to <span class="ep-gradient-text">studying abroad.</span>
                </h1>
                <p style="font-size: 0.95rem; color: #64748B; line-height: 1.6; margin-bottom: 1.75rem;">
                    Connect with 9 coordinated AI agents that analyze your academic profile, discover matching programs & scholarships, and build your personalized application strategy.
                </p>

                <div class="ep-auth-feature-list">
                    <div class="ep-auth-feature-item">
                        <div class="ep-auth-feature-icon">🏫</div>
                        <div>
                            <div class="ep-auth-feature-title">University & Program Matching</div>
                            <div class="ep-auth-feature-desc">Deep profile alignment across global graduate and undergraduate programs.</div>
                        </div>
                    </div>
                    <div class="ep-auth-feature-item">
                        <div class="ep-auth-feature-icon">💰</div>
                        <div>
                            <div class="ep-auth-feature-title">Scholarship & Funding Discovery</div>
                            <div class="ep-auth-feature-desc">Track assistantships, fellowships, and full-ride opportunities.</div>
                        </div>
                    </div>
                    <div class="ep-auth-feature-item">
                        <div class="ep-auth-feature-icon">🔬</div>
                        <div>
                            <div class="ep-auth-feature-title">Faculty Advisor Research Match</div>
                            <div class="ep-auth-feature-desc">Identify professors aligned with your specific research domain.</div>
                        </div>
                    </div>
                    <div class="ep-auth-feature-item">
                        <div class="ep-auth-feature-icon">📄</div>
                        <div>
                            <div class="ep-auth-feature-title">Tailored Statement of Purpose</div>
                            <div class="ep-auth-feature-desc">Grounded drafting based on your actual publications, CV, and goals.</div>
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right_col:
        with st.container(key="login-auth-card", border=False):
            st.markdown(
                """
                <div style="margin-bottom: 1.25rem;">
                    <div style="font-size: 1.4rem; font-weight: 800; color: #0F172A; letter-spacing: -0.02em;">Sign In</div>
                    <div style="font-size: 0.85rem; color: #64748B; margin-top: 0.2rem;">Access your personalized counseling dashboard</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            try:
                config = get_auth_config()
            except BackendError as error:
                render_backend_error(error, key="auth-config")
                _render_dev_login_form(show_backend_warning=True)
            else:
                if config.get("mode") == "google":
                    login_url = f"{BACKEND_URL}{config.get('google_login_url', '/api/v1/auth/login/google')}"
                    st.link_button(
                        "Continue with Google",
                        login_url,
                        type="primary",
                        use_container_width=True,
                        icon=":material/login:",
                    )
                    st.markdown(
                        """
                        <div class="ep-auth-divider-isolated">
                            <span>or continue with email</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    _render_dev_login_form()
                else:
                    _render_dev_login_form()

            st.markdown(
                """
                <div style="margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid #F1F5F9; text-align: center;">
                    <span style="font-size: 0.75rem; color: #94A3B8;">
                        🔒 Secure access · Grounded in verified university and scholarship data
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )


def _render_dev_login_form(*, show_backend_warning: bool = False) -> None:
    if show_backend_warning:
        st.warning(
            "The backend auth service is currently unavailable, so dev-mode login is being shown as a fallback.",
            icon=":material/warning:",
        )

    st.markdown(
        """
        <div style="background: #EEF2FF; border: 1px solid #C7D2FE; border-radius: 10px; padding: 0.75rem 1rem; margin-bottom: 1.1rem;">
            <div style="font-size: 0.82rem; color: #3730A3; font-weight: 600; margin-bottom: 0.15rem;">
                ✦ Demo / Dev Access Active
            </div>
            <div style="font-size: 0.75rem; color: #4338CA; line-height: 1.4;">
                Enter any email address to sign in immediately. No password required.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("dev_login_form", border=False):
        email = st.text_input("Email Address", placeholder="alex.student@example.com")
        name = st.text_input("Full Name (optional)", placeholder="Alex Rahman")
        submitted = st.form_submit_button(
            "Continue to Dashboard →",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        if not email.strip():
            st.warning("Please enter your email to continue.", icon=":material/warning:")
        else:
            with st.spinner("Signing in..."):
                try:
                    result = dev_login(email.strip(), name.strip() or None)
                except BackendError as error:
                    render_backend_error(error, key="dev-login")
                else:
                    st.session_state["auth_token"] = result["access_token"]
                    st.session_state["current_user"] = result["user"]
                    st.session_state["profile_id"] = None
                    st.session_state["profile"] = None
                    _hydrate_profile_from_backend()
                    st.query_params.clear()
                    st.rerun()


def render_logout_button() -> None:
    if st.button("Log out", icon=":material/logout:", use_container_width=True, key="logout-button"):
        try:
            logout()
        except BackendError:
            pass  # token may already be invalid/expired -- still clear local state
        _clear_session_auth()
        st.query_params.clear()
        st.rerun()
