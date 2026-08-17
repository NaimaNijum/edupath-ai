from __future__ import annotations

from datetime import datetime

import streamlit as st

from api.client import BackendError, list_memory
from components.common import render_backend_error, section_header
from components.empty_state import render_empty_state
from components.header import render_page_header


def _format_timestamp(raw: str | None) -> str:
    if not raw:
        return "Unknown time"
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).strftime("%B %d, %Y at %H:%M")
    except ValueError:
        return raw


def render() -> None:
    render_page_header(
        "Memory",
        "What EduPath AI remembers about you across sessions -- your current preferences and your search history.",
        eyebrow="Memory",
    )

    profile_id = st.session_state.get("profile_id")
    if not profile_id:
        render_empty_state(
            "No profile yet",
            "Complete your profile first -- memory is tied to your student profile.",
            icon="🧠",
            cta_label="Complete Profile",
            cta_page="pages/profile.py",
            key="memory-no-profile",
        )
        return

    try:
        entries = list_memory(profile_id)
    except BackendError as error:
        render_backend_error(error, key="memory-list")
        return

    if not entries:
        render_empty_state(
            "No memory yet",
            "Run a discovery search to start building your history -- EduPath AI remembers each search so future results can build on it.",
            icon="🧠",
            cta_label="Discover Opportunities",
            cta_page="pages/discover.py",
            key="memory-empty",
        )
        return

    current = [e for e in entries if e.get("scope") == "current_preferences"]
    history = [e for e in entries if e.get("memory_type") == "workflow_history"]
    other = [e for e in entries if e not in current and e not in history]

    if current:
        section_header("Current Preferences", "The most recent snapshot of your search context.")
        for entry in current:
            _render_entry(entry)
        st.write("")

    section_header("Search History", f"{len(history)} past discovery run(s) remembered.")
    if not history:
        st.caption("No past search history yet.")
    for entry in sorted(history, key=lambda e: e.get("content", {}).get("workflow_id", ""), reverse=True):
        _render_entry(entry)

    if other:
        st.write("")
        section_header("Other Memory", "")
        for entry in other:
            _render_entry(entry)


def _render_entry(entry: dict) -> None:
    content = entry.get("content") or {}
    with st.container(key=f"memory-entry-{entry['id']}", border=True):
        badge_style = "indigo" if entry.get("memory_type") == "workflow_history" else "purple"
        st.markdown(
            f'<span class="ep-badge {badge_style}">{(entry.get("memory_type") or "memory").replace("_", " ").title()}</span>',
            unsafe_allow_html=True,
        )
        if content.get("last_request"):
            st.write(content["last_request"])
        profile_signals = content.get("profile_signals")
        if profile_signals:
            with st.expander("Profile signals captured at this point"):
                st.json(profile_signals)
        st.caption(f"Source: {entry.get('source', 'unknown')}")


render()
