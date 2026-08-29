"""
Document Workspace — Statement of Purpose, Research Statements & Outreach Emails.
"""
from __future__ import annotations

import streamlit as st

from api.client import BackendError, generate_sop, list_sops, revise_sop
from components.common import render_backend_error, section_header
from components.empty_state import render_empty_state
from components.header import render_page_header

_DOC_TYPES = [
    "Statement of Purpose (SOP)",
    "Professor Outreach Email",
    "Research Statement",
    "LOR Guidance",
]


def render() -> None:
    render_page_header(
        "Document Workspace",
        "Generate, iterate, and export customized application materials grounded in your profile.",
        eyebrow="Application Documents",
    )

    profile_id = st.session_state.get("profile_id")
    if not profile_id:
        render_empty_state(
            "No student profile yet",
            "Complete your profile first so EduPath AI has authentic experiences to ground your drafts in.",
            icon="📝",
            cta_label="Complete Profile",
            cta_page="pages/profile.py",
            key="sop-no-profile",
        )
        return

    # Document Type Selector Tabs
    doc_type = st.radio(
        "Select Document Type",
        _DOC_TYPES,
        horizontal=True,
        label_visibility="collapsed",
    )

    st.write("")

    if doc_type == "Statement of Purpose (SOP)":
        _render_sop_workspace(profile_id)
    elif doc_type == "Professor Outreach Email":
        _render_email_workspace(profile_id)
    elif doc_type == "Research Statement":
        _render_research_statement_workspace(profile_id)
    else:
        _render_lor_guidance_workspace()


def _render_sop_workspace(profile_id: str) -> None:
    # --- Generate New Draft Panel ---
    with st.container(key="sop-generate-panel", border=True):
        section_header("Generate a New SOP Draft", "Grounded in your profile, CV, and target university program.")
        with st.form("sop_generate_form", border=False):
            cols = st.columns(2)
            with cols[0]:
                target_program = st.text_input("Target Degree Program", placeholder="PhD in Computer Science")
            with cols[1]:
                target_university = st.text_input("Target University", placeholder="Stanford University / MIT CSAIL")
            custom_prompt = st.text_area(
                "Custom Emphases & Instructions (optional)",
                placeholder='e.g. "Highlight my Edge AI publication, mention my GPA growth, and express interest in Prof. Dawn Song\'s lab."',
                height=85,
            )
            submitted = st.form_submit_button(
                "✦ Generate Tailored SOP Draft",
                type="primary",
                icon=":material/auto_awesome:",
                use_container_width=True,
            )

        if submitted:
            with st.status("Drafting tailored Statement of Purpose...", expanded=True) as status:
                st.write("Synthesizing your academic background, research publications, and program alignment...")
                try:
                    generate_sop(
                        profile_id,
                        target_program or None,
                        target_university or None,
                        custom_prompt or None,
                    )
                except BackendError as error:
                    render_backend_error(error, key="sop-generate")
                    status.update(label="Draft generation failed", state="error")
                else:
                    status.update(label="SOP draft ready!", state="complete")
                    st.rerun()

    # --- Drafts List ---
    st.write("")
    section_header("Saved SOP Drafts & Version History", "Review and refine your iterations.")

    try:
        drafts = list_sops(profile_id)
    except BackendError as error:
        render_backend_error(error, key="sop-list")
        return

    if not drafts:
        render_empty_state(
            "No SOP drafts on record",
            "Generate your first draft above to begin refining your statement.",
            icon="📄",
            key="sop-empty",
        )
        return

    for draft in drafts:
        _render_draft_card(profile_id, draft)


def _render_draft_card(profile_id: str, draft: dict) -> None:
    sop_id = draft.get("sop_id") or draft.get("id", "")
    version = draft.get("draft_version", 1)
    status_val = draft.get("status", "draft")
    title = draft.get("title") or f"Statement of Purpose v{version}"
    content = draft.get("content") or ""
    updated = (draft.get("updated_at") or "")[:10]

    status_style = {
        "draft": "neutral",
        "approved": "success",
        "submitted": "indigo",
        "revision_requested": "warning",
    }.get(status_val, "neutral")

    with st.container(key=f"sop-draft-container-{sop_id}", border=True):
        c1, c2 = st.columns([3.8, 1.2])
        with c1:
            st.markdown(
                f"""
                <div style="font-weight: 700; font-size: 1.05rem; color: #0F172A;">{title}</div>
                <div style="display: flex; gap: 0.5rem; margin-top: 0.35rem; align-items: center; flex-wrap: wrap;">
                  <span class="ep-badge indigo ep-doc-version-badge">Version {version}</span>
                  <span class="ep-badge {status_style}">{status_val.replace('_',' ').title()}</span>
                  <span class="ep-badge neutral">Updated {updated}</span>
                  <span style="font-size: 0.75rem; color: #64748B;">{len(content.split())} words</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c2:
            st.download_button(
                "Export Draft (.txt)",
                data=content,
                file_name=f"edupath_sop_v{version}.txt",
                icon=":material/download:",
                key=f"download-{sop_id}",
                use_container_width=True,
            )

        # Document Viewer
        if content:
            with st.expander("Read Statement of Purpose", expanded=True, icon=":material/article:"):
                st.markdown(
                    f"""
                    <div class="ep-doc-viewer">
                      {content.replace(chr(10), '<br>')}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        # Revision & Human Approval Feedback Loop
        with st.expander("Request AI Revision & Provide Feedback", icon=":material/edit:"):
            feedback_key = f"sop-feedback-{sop_id}"
            feedback = st.text_area(
                "What specific edits should the AI make?",
                key=feedback_key,
                placeholder='e.g. "Make the introduction more concise, elaborate on my thesis findings in paragraph 3, and fix the word count to under 800 words."',
                height=90,
            )
            col_r1, col_r2 = st.columns(2)
            with col_r1:
                if st.button(
                    "✦ Submit Revision Request",
                    key=f"revise-{sop_id}",
                    icon=":material/auto_fix_high:",
                    type="primary",
                    use_container_width=True,
                ):
                    if not feedback.strip():
                        st.warning("Please describe what changes you want before submitting.", icon=":material/warning:")
                    else:
                        with st.spinner("Revising draft with your feedback..."):
                            try:
                                revise_sop(profile_id, sop_id, feedback.strip())
                            except BackendError as error:
                                render_backend_error(error, key=f"sop-revise-{sop_id}")
                            else:
                                st.success("Revised draft generated and saved!", icon=":material/check_circle:")
                                st.rerun()
            with col_r2:
                if st.button(
                    "✓ Approve Draft for Application",
                    key=f"approve-{sop_id}",
                    icon=":material/check_circle:",
                    use_container_width=True,
                ):
                    st.success("Draft marked as approved.", icon=":material/check_circle:")


def _render_email_workspace(profile_id: str) -> None:
    prof_name = st.session_state.get("target_prof_name") or "Prof. Dawn Song"
    prof_uni = st.session_state.get("target_prof_uni") or "UC Berkeley / MIT"

    with st.container(key="email-generator-card", border=True):
        section_header("Faculty Outreach Cold Email", "Generate a respectful, personalized outreach email to prospective advisors.")
        c1, c2 = st.columns(2)
        with c1:
            target_prof = st.text_input("Professor Name", value=prof_name)
        with c2:
            target_uni = st.text_input("University / Department", value=prof_uni)

        sample_email = f"""Subject: Prospective PhD Applicant — Fall 2027 (Research Alignment with {target_prof}'s Lab)

Dear {target_prof},

I hope this email finds you well.

My name is Alex Rahman, and I am completing my undergraduate studies in Computer Science at the University of Washington with a 3.82 CGPA. I have been following your lab's recent publications on Hardware Security and Edge AI inference with great admiration.

My background includes 2 years of undergraduate research in embedded machine learning and a published IEEE workshop paper on energy-efficient neural acceleration. Given your ongoing work on secure AI hardware architectures, I am eager to apply for the PhD in Computer Science program at {target_uni} for Fall 2027 and would be thrilled to contribute to your group.

I have attached my CV and transcript for your review. If you have prospective openings for graduate research assistants, I would welcome the opportunity to discuss how my background aligns with your current lab directions.

Thank you for your time and consideration.

Sincerely,
Alex Rahman
LinkedIn: linkedin.com/in/alexrahman | GitHub: github.com/alexrahman"""

        st.markdown(
            f"""
            <div class="ep-doc-viewer" style="font-family: monospace; font-size: 0.9rem;">
                {sample_email.replace(chr(10), '<br>')}
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.download_button(
            "Copy / Export Email Draft (.txt)",
            data=sample_email,
            file_name=f"email_to_{target_prof.replace(' ', '_')}.txt",
            icon=":material/download:",
            use_container_width=True,
            type="primary",
        )


def _render_research_statement_workspace(profile_id: str) -> None:
    with st.container(key="research-stmt-card", border=True):
        section_header("Research Statement Draft", "Outlines your academic research vision and methodologies.")
        sample_stmt = """# Research Statement & Agenda

## 1. Executive Summary
My research focuses on the intersection of Hardware Security, Trusted Execution Environments, and Edge AI Acceleration. Specifically, I investigate how low-power IoT microcontrollers can execute deep neural network inference without leaking side-channel data or sacrificing real-time guarantees.

## 2. Prior Research Contributions
- **Edge Acceleration**: Designed an FPGA-accelerated RISC-V coprocessor for quantized transformer models, achieving 3.4x throughput efficiency.
- **Security Audit**: Identified side-channel vulnerabilities in mobile tensor processing units under electromagnetic profiling.

## 3. Prospective Doctoral Research Directions
1. **Side-Channel Resilient Transformer Architectures**: Designing hardware-native masking protocols for attention computation.
2. **Federated On-Device Continuous Learning**: Ensuring model integrity and privacy during distributed edge model fine-tuning."""

        st.markdown(
            f"""
            <div class="ep-doc-viewer">
                {sample_stmt.replace(chr(10), '<br>')}
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_lor_guidance_workspace() -> None:
    with st.container(key="lor-guidance-card", border=True):
        section_header("Letter of Recommendation (LOR) Strategy", "Guidelines and draft templates for your faculty recommenders.")
        st.markdown(
            """
            ### Recommended Recommender Mix:
            1. **Primary Research Advisor**: Can speak deeply about your research independence, problem solving, and technical publications.
            2. **Senior Course Professor (Major)**: Verifies your academic rigor, mastery of advanced concepts, and classroom engagement.
            3. **Industry / Internship Lead**: Validates your collaborative engineering, code quality, and delivery under constraints.
            """
        )


render()
