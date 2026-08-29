"""
Memory — AI memory viewer showing what EduPath AI remembers across sessions.

Displays:
- Research interests extracted from memory
- Current preference snapshot
- Past discovery session history
- Timestamps and source info
"""
from __future__ import annotations

from datetime import datetime

import streamlit as st

from api.client import BackendError, list_memory
from components.common import render_backend_error, section_header
from components.empty_state import render_empty_state
from components.header import render_page_header


def _format_date(raw: str | None) -> str:
    if not raw:
        return "Unknown date"
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).strftime("%B %d, %Y")
    except ValueError:
        return raw[:10] if raw else "—"


def _extract_interests(entries: list[dict]) -> list[str]:
    """Extract unique research interests from all memory entries."""
    interests: set[str] = set()
    for entry in entries:
        content = entry.get("content") or {}
        signals = content.get("profile_signals") or {}
        for field in ("research_interests", "preferred_domains", "research_domains"):
            val = signals.get(field)
            if isinstance(val, list):
                interests.update(str(v) for v in val if v)
            elif isinstance(val, str) and val:
                # split on commas
                for part in val.split(","):
                    p = part.strip()
                    if p:
                        interests.add(p)
        # Also from top-level content
        if isinstance(content.get("last_request"), str):
            pass  # just the raw request text, skip
    return sorted(interests)


def render() -> None:
    render_page_header(
        "AI Memory",
        "What EduPath AI remembers about you — your preferences, research interests, and search history across sessions.",
        eyebrow="Memory",
    )

    profile_id = st.session_state.get("profile_id")
    if not profile_id:
        render_empty_state(
            "No profile yet",
            "Complete your profile first — memory is tied to your student profile.",
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
            "Run a counseling session or discovery search to start building your AI memory history.",
            icon="🧠",
            cta_label="Start Counseling",
            cta_page="pages/counseling.py",
            key="memory-empty",
        )
        return

    current = [e for e in entries if e.get("scope") == "current_preferences"]
    history = [e for e in entries if e.get("memory_type") == "workflow_history"]
    other = [e for e in entries if e not in current and e not in history]

    interests = _extract_interests(entries)

    # --- Research Interests Panel ---
    if interests:
        section_header("Research Interests", "Extracted from your memory across all sessions.")
        interest_tags = "".join(
            f'<span class="ep-memory-interest-tag">{i}</span>' for i in interests
        )
        st.markdown(
            f'<div class="ep-memory-interests">{interest_tags}</div>',
            unsafe_allow_html=True,
        )
        if current:
            last_updated = _format_date(current[0].get("updated_at") or current[0].get("created_at"))
            st.caption(f"Last updated: {last_updated}")
        st.write("")

    # --- Current Preferences ---
    if current:
        section_header("Current Preferences", "The most recent snapshot of your search context.")
        for entry in current:
            _render_entry(entry, expanded=True)
        st.write("")

    # --- Search History ---
    section_header("Search History", f"{len(history)} past session(s) remembered.")
    if not history:
        st.caption("No past search history yet — run a discovery search to build history.")
    else:
        for entry in sorted(history, key=lambda e: e.get("created_at") or "", reverse=True):
            _render_entry(entry, expanded=False)

    # --- Other ---
    if other:
        st.write("")
        section_header("Other Memory", "Additional memory entries.")
        for entry in other:
            _render_entry(entry, expanded=False)


def _render_entry(entry: dict, *, expanded: bool = False) -> None:
    content = entry.get("content") or {}
    memory_type = entry.get("memory_type") or "memory"
    scope = entry.get("scope") or ""
    entry_id = entry.get("id") or "unknown"
    source = entry.get("source") or "unknown"
    date_str = _format_date(entry.get("updated_at") or entry.get("created_at"))

    badge_style = "indigo" if memory_type == "workflow_history" else "purple"
    label = memory_type.replace("_", " ").title()
    if scope and scope != memory_type:
        label += f" · {scope.replace('_', ' ').title()}"

    display_title = content.get("last_request") or label
    if len(display_title) > 80:
        display_title = display_title[:80] + "..."

    with st.container(key=f"memory-entry-{entry_id}", border=True):
        c1, c2 = st.columns([5, 1])
        with c1:
            st.markdown(
                f"""
                <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.3rem;">
                  <span class="ep-badge {badge_style} ep-memory-type-pill">{label}</span>
                  <span class="ep-memory-timestamp">Updated {date_str}</span>
                </div>
                <div style="font-size:0.9rem;color:#0F172A;font-weight:500;">{display_title}</div>
                """,
                unsafe_allow_html=True,
            )
        with c2:
            wf_id = content.get("workflow_id")
            if wf_id:
                if st.button("Trace →", key=f"trace-link-{entry_id}", use_container_width=True):
                    st.session_state["current_workflow_id"] = wf_id
                    st.switch_page("pages/agent_trace.py")

        profile_signals = content.get("profile_signals")
        if profile_signals:
            with st.expander("Profile signals at this point", icon=":material/psychology:"):
                sig_cols = st.columns(2)
                sig_items = list(profile_signals.items())
                for i, (k, v) in enumerate(sig_items):
                    with sig_cols[i % 2]:
                        if isinstance(v, list):
                            val_str = ", ".join(str(x) for x in v) if v else "—"
                        else:
                            val_str = str(v) if v else "—"
                        st.markdown(
                            f'<div class="ep-field-label">{k.replace("_", " ").title()}</div>'
                            f'<div class="ep-field-value">{val_str[:80]}</div>',
                            unsafe_allow_html=True,
                        )

        st.caption(f"Source: {source}")


render()
