from __future__ import annotations

import streamlit as st

# Central registry of all session_state keys this app uses, with defaults.
# `saved_opportunities` and `application_stage` are UI-only, browser-session
# state -- the backend has no persistence endpoint for either, so nothing
# here survives a Streamlit restart. This is called out in the UI itself.
_DEFAULTS: dict[str, object] = {
    "profile_id": None,
    "profile": None,
    "current_workflow_id": None,
    "workflow_result": None,
    "workflow_error": None,
    "opportunities": None,
    "opportunities_error": None,
    "saved_opportunities": {},
    "application_stage": {},
    "last_user_request": "",
}

# Auth state is tracked separately from _DEFAULTS so "Clear Session" on the
# Settings page (reset_session_state) can wipe app data without logging the
# user out -- logging out is its own explicit action.
_AUTH_DEFAULTS: dict[str, object] = {
    "auth_token": None,
    "current_user": None,
}

APPLICATION_STAGES = ["Saved", "Preparing", "Applied", "Interview", "Accepted", "Rejected"]


def init_session_state() -> None:
    """Ensure every key this app relies on exists before any page renders."""
    for key, default in {**_DEFAULTS, **_AUTH_DEFAULTS}.items():
        st.session_state.setdefault(key, default)


def reset_session_state() -> None:
    """Clear EduPath AI app data (used by the Settings page) -- does not log the user out."""
    for key, default in _DEFAULTS.items():
        st.session_state[key] = default


def is_authenticated() -> bool:
    return bool(st.session_state.get("auth_token"))


def has_profile() -> bool:
    return bool(st.session_state.get("profile_id"))


def is_saved(opportunity_id: str) -> bool:
    return opportunity_id in st.session_state.get("saved_opportunities", {})


def toggle_saved(opportunity: dict) -> bool:
    """Add/remove an opportunity from the session-only saved list.

    Returns the new saved state (True if now saved).
    """
    saved = st.session_state.setdefault("saved_opportunities", {})
    opportunity_id = opportunity.get("id")
    if opportunity_id in saved:
        del saved[opportunity_id]
        st.session_state.get("application_stage", {}).pop(opportunity_id, None)
        return False
    saved[opportunity_id] = opportunity
    st.session_state.setdefault("application_stage", {})[opportunity_id] = APPLICATION_STAGES[0]
    return True


def set_application_stage(opportunity_id: str, stage: str) -> None:
    st.session_state.setdefault("application_stage", {})[opportunity_id] = stage
