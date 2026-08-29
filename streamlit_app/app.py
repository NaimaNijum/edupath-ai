from __future__ import annotations

from pathlib import Path

import streamlit as st

# Ensure page config is set as the very first command
st.set_page_config(
    page_title="EduPath AI – Your AI-Powered Path to Studying Abroad",
    page_icon=":material/school:",
    layout="wide",
    initial_sidebar_state="expanded",
)

from components.auth import ensure_current_user, handle_oauth_redirect, render_login_gate, require_auth
from components.sidebar import render_sidebar_brand, render_sidebar_footer
from utils.session import init_session_state


def _load_css() -> None:
    css_path = Path(__file__).resolve().parent / "styles" / "main.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)


def main() -> None:
    init_session_state()
    _load_css()
    handle_oauth_redirect()

    is_authenticated = ensure_current_user()

    if not is_authenticated:
        page = st.query_params.get("page", "landing")

        if page == "login":
            render_login_gate()
        else:
            nav = st.navigation(
                {
                    "": [
                        st.Page("pages/landing.py", title="Home", icon=":material/home:", default=True, url_path=""),
                    ],
                }
            )
            nav.run()
        return

    require_auth()
    render_sidebar_brand()

    nav = st.navigation(
        {
            "Home": [
                st.Page("pages/dashboard.py", title="Dashboard", icon=":material/dashboard:", default=True, url_path="dashboard"),
            ],
            "Counseling": [
                st.Page("pages/counseling.py", title="New Session", icon=":material/add_circle:", url_path="counseling"),
                st.Page("pages/discover.py", title="History & Analysis", icon=":material/history:", url_path="history"),
            ],
            "Explore": [
                st.Page("pages/discover.py", title="Universities & Programs", icon=":material/school:", url_path="universities"),
                st.Page("pages/saved.py", title="Saved Matches", icon=":material/bookmark:", url_path="saved"),
            ],
            "Application": [
                st.Page("pages/sop.py", title="Document Workspace", icon=":material/edit_note:", url_path="documents"),
                st.Page("pages/tracker.py", title="Application Tracker", icon=":material/checklist:", url_path="tracker"),
                st.Page("pages/profile.py", title="Student Profile", icon=":material/person:", url_path="profile"),
            ],
            "Workforce": [
                st.Page("pages/agent_trace.py", title="Live Agent Trace", icon=":material/timeline:", url_path="agent-trace"),
                st.Page("pages/execution_graph.py", title="Execution Graph", icon=":material/hub:", url_path="execution-graph"),
                st.Page("pages/memory.py", title="AI Memory", icon=":material/psychology:", url_path="memory"),
                st.Page("pages/usage.py", title="Usage & Tokens", icon=":material/bar_chart:", url_path="usage"),
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
