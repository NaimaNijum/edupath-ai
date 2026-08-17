from __future__ import annotations

import streamlit as st

from api.client import BackendError, generate_sop, list_sops, revise_sop
from components.common import render_backend_error, section_header
from components.empty_state import render_empty_state
from components.header import render_page_header


def render() -> None:
    render_page_header(
        "Statement of Purpose",
        "Generate and iterate on your SOP -- grounded in your profile and any documents you've uploaded.",
        eyebrow="SOP",
    )

    profile_id = st.session_state.get("profile_id")
    if not profile_id:
        render_empty_state(
            "No profile yet",
            "Complete your profile first so EduPath AI has something real to draft from.",
            icon="📝",
            cta_label="Complete Profile",
            cta_page="pages/profile.py",
            key="sop-no-profile",
        )
        return

    with st.container(key="sop-generate-panel", border=True):
        section_header("Generate a New Draft")
        with st.form("sop_generate_form", border=False):
            cols = st.columns(2)
            with cols[0]:
                target_program = st.text_input("Target Program", placeholder="PhD in Computer Science")
            with cols[1]:
                target_university = st.text_input("Target University", placeholder="Stanford University")
            custom_prompt = st.text_area("Custom instructions (optional)", placeholder="Leave blank to use a standard SOP prompt.")
            submitted = st.form_submit_button("Generate SOP", type="primary", icon=":material/auto_awesome:", use_container_width=True)

        if submitted:
            with st.spinner("Drafting your SOP..."):
                try:
                    generate_sop(profile_id, target_program or None, target_university or None, custom_prompt or None)
                except BackendError as error:
                    render_backend_error(error, key="sop-generate")
                else:
                    st.success("SOP draft generated.", icon=":material/check_circle:")
                    st.rerun()

    st.write("")
    section_header("Your Drafts")
    try:
        drafts = list_sops(profile_id)
    except BackendError as error:
        render_backend_error(error, key="sop-list")
        return

    if not drafts:
        st.caption("No SOP drafts yet -- generate one above.")
        return

    for draft in drafts:
        _render_draft(profile_id, draft)


def _render_draft(profile_id: str, draft: dict) -> None:
    with st.container(key=f"sop-draft-{draft['sop_id']}", border=True):
        st.markdown(f"**{draft['title']}** &nbsp; <span class=\"ep-badge indigo\">v{draft['draft_version']}</span>", unsafe_allow_html=True)
        st.caption(f"Status: {draft['status']} · Updated {draft.get('updated_at', '')}")

        with st.expander("View draft", expanded=False):
            st.write(draft["content"])
            st.download_button(
                "Download as .txt",
                data=draft["content"],
                file_name=f"sop_v{draft['draft_version']}.txt",
                icon=":material/download:",
                key=f"download-{draft['sop_id']}",
            )

        with st.expander("Request a revision"):
            feedback_key = f"sop-feedback-{draft['sop_id']}"
            feedback = st.text_area("What should change?", key=feedback_key)
            if st.button("Revise", key=f"revise-{draft['sop_id']}", icon=":material/edit:"):
                if not feedback.strip():
                    st.warning("Describe what should change first.", icon=":material/warning:")
                else:
                    try:
                        revise_sop(profile_id, draft["sop_id"], feedback.strip())
                    except BackendError as error:
                        render_backend_error(error, key=f"sop-revise-{draft['sop_id']}")
                    else:
                        st.success("Revised.", icon=":material/check_circle:")
                        st.rerun()


render()
