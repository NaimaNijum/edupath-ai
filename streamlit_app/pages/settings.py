from __future__ import annotations

import streamlit as st

from api.client import BackendError, check_health
from components.common import render_backend_error, section_header
from components.header import render_page_header
from utils.config import BACKEND_URL
from utils.session import reset_session_state


def render() -> None:
    render_page_header("Settings", "Backend connection, session data, and app info.", eyebrow="Settings")

    with st.container(key="settings-backend", border=True):
        section_header("Backend Connection")
        st.write(f"**Backend URL:** `{BACKEND_URL}`")
        st.caption("Configured via streamlit_app/.env (BACKEND_URL). No AI credentials are stored in this frontend.")

        if st.button("Test Connection", icon=":material/wifi_tethering:"):
            try:
                health = check_health()
            except BackendError as error:
                render_backend_error(error, key="settings-health")
            else:
                st.success(f"Backend reachable: {health.get('status', 'unknown')}", icon=":material/check_circle:")

    st.write("")
    with st.container(key="settings-session", border=True):
        section_header("Session Data", "Data stored only in this browser session (not the backend database).")
        st.write(
            {
                "profile_id": st.session_state.get("profile_id"),
                "current_workflow_id": st.session_state.get("current_workflow_id"),
                "saved_opportunities": len(st.session_state.get("saved_opportunities", {})),
            }
        )
        if st.button("Clear Session", type="secondary", icon=":material/restart_alt:"):
            reset_session_state()
            st.success("Session cleared.", icon=":material/check_circle:")
            st.rerun()


render()
