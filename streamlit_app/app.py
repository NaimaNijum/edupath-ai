from __future__ import annotations

from pathlib import Path

import streamlit as st

from components.auth import ensure_current_user, handle_oauth_redirect, render_login_gate
from components.sidebar import render_sidebar_brand, render_sidebar_footer
from utils.session import init_session_state


def _load_css() -> None:
    css_path = Path(__file__).resolve().parent / "styles" / "main.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)


def main() -> None:
    st.set_page_config(page_title="EduPath AI", page_icon=":material/school:", layout="wide")
    init_session_state()
    _load_css()
    handle_oauth_redirect()

    if not ensure_current_user():
        render_login_gate()
        return

    render_sidebar_brand()

    nav = st.navigation(
        {
            "Workspace": [
                st.Page("pages/dashboard.py", title="Dashboard", icon=":material/dashboard:", default=True, url_path="dashboard"),
                st.Page("pages/profile.py", title="My Profile", icon=":material/school:", url_path="profile"),
                st.Page("pages/discover.py", title="Discover Opportunities", icon=":material/travel_explore:", url_path="discover"),
                st.Page("pages/saved.py", title="Saved Opportunities", icon=":material/bookmark:", url_path="saved"),
                st.Page("pages/tracker.py", title="Application Tracker", icon=":material/checklist:", url_path="tracker"),
                st.Page("pages/sop.py", title="Statement of Purpose", icon=":material/edit_note:", url_path="sop"),
            ],
            "Insights": [
                st.Page("pages/agent_trace.py", title="Agent Trace", icon=":material/timeline:", url_path="agent-trace"),
                st.Page("pages/execution_graph.py", title="Execution Graph", icon=":material/hub:", url_path="execution-graph"),
                st.Page("pages/memory.py", title="Memory", icon=":material/psychology:", url_path="memory"),
                st.Page("pages/usage.py", title="Usage & Cost", icon=":material/bar_chart:", url_path="usage"),
            ],
            "": [
                st.Page("pages/settings.py", title="Settings", icon=":material/settings:", url_path="settings"),
            ],
        }
    )

    render_sidebar_footer()
    nav.run()


if __name__ == "__main__":
    main()
