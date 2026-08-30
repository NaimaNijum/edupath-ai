"""
New Counseling Session — Adaptive Multi-Step AI Intake Wizard & Workforce Execution.

Steps:
  1. Profile      (Basic background)
  2. Academic     (GPA, test scores, graduation)
  3. Experience   (Conditional: UG=Activities/Goals, Masters=Projects/Skills, PhD=Research/Publications)
  4. Preferences  (Target countries, degree level, funding, intake)
  5. Review       (Structured pre-flight confirmation)
  6. AI Analysis  (Live multi-agent workforce orchestration screen)
"""
from __future__ import annotations

import textwrap
import streamlit as st

from api.client import BackendError, analyze_counseling
from components.common import render_backend_error, render_html, section_header
from components.empty_state import render_empty_state
from components.header import render_page_header
from components.workflow_status import render_workflow_status

_STEPS = ["Profile", "Academic", "Experience", "Preferences", "Review", "AI Analysis"]

_DEGREE_LEVELS = ["Undergraduate", "Masters", "PhD", "Postdoctoral"]
_FUNDING_OPTIONS = ["Fully Funded (RA/TA/Fellowship)", "Partial Funding / Tuition Waiver", "Self-Funded", "Any Funding Available"]
_INTAKE_OPTIONS = ["Fall 2026", "Spring 2027", "Fall 2027", "Spring 2028", "Flexible"]
_UNIVERSITY_TYPE_OPTIONS = ["Top Research University (R1 / Russell Group)", "Technical Institute / STEM Focus", "Global Comprehensive University", "Liberal Arts / Teaching Focused", "Any"]
_COUNTRY_OPTIONS = [
    "USA", "Canada", "UK", "Germany", "Australia", "Netherlands",
    "Sweden", "Switzerland", "Singapore", "Japan", "France", "Denmark",
    "Finland", "Norway", "Ireland", "South Korea",
]
_RESEARCH_DOMAIN_OPTIONS = [
    "Artificial Intelligence", "Machine Learning", "Deep Learning",
    "Natural Language Processing", "Computer Vision", "Robotics",
    "Computer Security / Cybersecurity", "Edge Computing & IoT", "AI Hardware Security",
    "Bioinformatics & Computational Biology", "Data Science & Big Data Analytics",
    "Human-Computer Interaction (HCI)", "Distributed Systems & Cloud", "Quantum Computing",
    "Renewable Energy & Climate Tech", "Materials Science", "Computational Neuroscience",
    "Quantitative Economics & Finance", "Public Policy & Global Affairs",
]


def _html(content: str) -> None:
    """Render HTML safely via st.html without markdown code block artifacts."""
    render_html(content)


def _init_wizard() -> None:
    if "counseling_step" not in st.session_state:
        st.session_state["counseling_step"] = 0
    if "counseling_data" not in st.session_state:
        profile = st.session_state.get("profile") or {}
        st.session_state["counseling_data"] = {
            "name": profile.get("name", ""),
            "current_degree": profile.get("current_degree") or "Undergraduate",
            "major": profile.get("field_of_study", ""),
            "university": profile.get("university", ""),
            "country": profile.get("country_of_residence") or "United States",
            "cgpa": str(profile.get("gpa") or ""),
            "gpa_scale": "4.0",
            "ielts": "",
            "toefl": "",
            "gre": "",
            "sat_act": "",
            "graduation_year": str(profile.get("graduation_year") or "2026"),
            "achievements": "",
            "research_experience": profile.get("work_experience", ""),
            "publications": str(profile.get("publications") or ""),
            "projects": profile.get("projects", ""),
            "skills": profile.get("skills", ""),
            "research_interests": profile.get("research_interests", ""),
            "research_domains": [],
            "preferred_faculty": "",
            "target_countries": profile.get("target_countries") or ["USA", "Canada"],
            "target_degree": profile.get("target_degree") or "PhD",
            "funding_requirement": profile.get("preferred_funding") or "Fully Funded (RA/TA/Fellowship)",
            "target_intake": "Fall 2027",
            "university_type": "Top Research University (R1 / Russell Group)",
        }


def _render_step_indicator(current: int) -> None:
    steps_html = '<div class="ep-wizard-steps">'
    for i, label in enumerate(_STEPS):
        if i < current:
            cls = "completed"
            icon = "✓"
        elif i == current:
            cls = "active"
            icon = str(i + 1)
        else:
            cls = ""
            icon = str(i + 1)
        steps_html += f'<div class="ep-wizard-step {cls}"><div class="ep-wizard-step-num">{icon}</div><div class="ep-wizard-step-label">{label}</div></div>'
        if i < len(_STEPS) - 1:
            connector_cls = "completed" if i < current else ""
            steps_html += f'<div class="ep-wizard-step-connector {connector_cls}"></div>'
    steps_html += "</div>"
    _html(steps_html)


def _nav_buttons(step: int, total: int = len(_STEPS) - 1) -> tuple[bool, bool]:
    cols = st.columns([1, 3, 1])
    back = False
    nxt = False
    with cols[0]:
        if step > 0:
            back = st.button("← Back", key=f"wizard-back-{step}", use_container_width=True)
    with cols[2]:
        label = "Review Profile →" if step == total - 1 else ("Start AI Analysis →" if step == total else "Continue →")
        nxt = st.button(label, key=f"wizard-next-{step}", type="primary", use_container_width=True)
    return back, nxt


def render_step_profile() -> None:
    data = st.session_state["counseling_data"]
    section_header("Personal & Academic Identity", "Tell us about your background so we can calibrate admission requirements.")

    cols = st.columns(2)
    with cols[0]:
        data["name"] = st.text_input("Full Name", value=data["name"], placeholder="Alex Rahman")
    with cols[1]:
        data["target_degree"] = st.selectbox(
            "Degree Level You Are Applying For",
            _DEGREE_LEVELS,
            index=_DEGREE_LEVELS.index(data["target_degree"]) if data["target_degree"] in _DEGREE_LEVELS else 2,
            help="Your form fields will adapt based on whether you are applying for Undergraduate, Masters, or PhD.",
        )

    cols2 = st.columns(2)
    with cols2[0]:
        data["major"] = st.text_input("Current Major / Field of Study", value=data["major"], placeholder="Computer Science")
    with cols2[1]:
        data["university"] = st.text_input("Current Institution / University", value=data["university"], placeholder="University of Washington")

    data["country"] = st.text_input("Citizenship / Country of Residence", value=data["country"], placeholder="United States")

    back, nxt = _nav_buttons(0)
    if back:
        st.session_state["counseling_step"] = max(0, st.session_state["counseling_step"] - 1)
        st.rerun()
    if nxt:
        if not data["name"].strip():
            st.warning("Please enter your name.", icon=":material/warning:")
        elif not data["major"].strip():
            st.warning("Please enter your field of study.", icon=":material/warning:")
        else:
            st.session_state["counseling_step"] = 1
            st.rerun()


def render_step_academic() -> None:
    data = st.session_state["counseling_data"]
    is_ug = data.get("target_degree") == "Undergraduate"

    section_header("Academic Credentials & Test Scores", "Scores are verified against university admission cutoffs.")

    cols = st.columns(2)
    with cols[0]:
        data["cgpa"] = st.text_input("Cumulative GPA", value=data["cgpa"], placeholder="3.82")
    with cols[1]:
        data["gpa_scale"] = st.selectbox("GPA Scale", ["4.0 Scale", "5.0 Scale", "10.0 Scale", "Percentage (100%)"], index=0)

    if is_ug:
        cols_tests = st.columns(2)
        with cols_tests[0]:
            data["sat_act"] = st.text_input("SAT / ACT Score (optional)", value=data.get("sat_act", ""), placeholder="SAT 1480 / ACT 33")
        with cols_tests[1]:
            data["ielts"] = st.text_input("IELTS / TOEFL Score (optional)", value=data["ielts"], placeholder="IELTS 7.5 / TOEFL 105")
    else:
        cols_tests = st.columns(3)
        with cols_tests[0]:
            data["ielts"] = st.text_input("IELTS Score (optional)", value=data["ielts"], placeholder="7.5")
        with cols_tests[1]:
            data["toefl"] = st.text_input("TOEFL Score (optional)", value=data["toefl"], placeholder="105")
        with cols_tests[2]:
            data["gre"] = st.text_input("GRE Score (optional)", value=data["gre"], placeholder="326 (Q: 168, V: 158)")

    cols_grad = st.columns(2)
    with cols_grad[0]:
        data["graduation_year"] = st.text_input("Expected / Actual Graduation Year", value=data["graduation_year"], placeholder="2026")
    with cols_grad[1]:
        data["achievements"] = st.text_input("Academic Honors (optional)", value=data["achievements"], placeholder="Dean's Honor List, Merit Scholar")

    back, nxt = _nav_buttons(1)
    if back:
        st.session_state["counseling_step"] = 0
        st.rerun()
    if nxt:
        st.session_state["counseling_step"] = 2
        st.rerun()


def render_step_experience() -> None:
    data = st.session_state["counseling_data"]
    degree = data.get("target_degree", "PhD")

    if degree == "Undergraduate":
        section_header("Extracurriculars & Career Interests", "Undergraduate profile signals.")
        data["skills"] = st.text_area(
            "Extracurricular Activities, Competitions & Clubs",
            value=data.get("skills", ""),
            placeholder="Robotics Club President, Math Olympiad, Volunteering...",
            height=100,
        )
        data["research_interests"] = st.text_area(
            "Academic Interests & Prospective Majors",
            value=data.get("research_interests", ""),
            placeholder="Interested in Computer Engineering and Renewable Energy...",
            height=90,
        )
    elif degree == "Masters":
        section_header("Technical Projects & Domain Focus", "Graduate application qualifications.")
        data["projects"] = st.text_area(
            "Key Technical Projects / Capstone",
            value=data.get("projects", ""),
            placeholder="Developed an automated distributed pipeline in Python & PyTorch...",
            height=100,
        )
        data["skills"] = st.text_input(
            "Technical Skills & Tooling",
            value=data.get("skills", ""),
            placeholder="Python, C++, PyTorch, Docker, Kubernetes, AWS",
        )
        data["research_domains"] = st.multiselect(
            "Specialization Domains",
            _RESEARCH_DOMAIN_OPTIONS,
            default=[d for d in (data.get("research_domains") or []) if d in _RESEARCH_DOMAIN_OPTIONS],
            placeholder="Select one or more specialization domains...",
        )
    else:  # PhD / Postdoc
        section_header("Research Track Record & Faculty Alignment", "PhD candidate research qualifications.")
        data["research_experience"] = st.text_area(
            "Research Background & Lab Experience",
            value=data.get("research_experience", ""),
            placeholder="2 years as Graduate Research Assistant in Embedded Systems & AI Lab...",
            height=110,
        )
        cols_phd = st.columns(2)
        with cols_phd[0]:
            data["publications"] = st.text_input("Publications / Preprints Count", value=data.get("publications", ""), placeholder="1 Conference paper (IEEE)")
        with cols_phd[1]:
            data["skills"] = st.text_input("Core Technical & Experimental Skills", value=data.get("skills", ""), placeholder="PyTorch, FPGA, Verilog, RISC-V, CUDA")

        data["research_interests"] = st.text_area(
            "Specific Research Focus (Thesis Ideas)",
            value=data.get("research_interests", ""),
            placeholder="Interested in Hardware-Efficient Transformer architectures and Edge AI security...",
            height=85,
        )
        data["research_domains"] = st.multiselect(
            "Primary Research Domains",
            _RESEARCH_DOMAIN_OPTIONS,
            default=[d for d in (data.get("research_domains") or []) if d in _RESEARCH_DOMAIN_OPTIONS],
            placeholder="Select research fields...",
        )
        data["preferred_faculty"] = st.text_input(
            "Target Faculty or Labs (optional)",
            value=data.get("preferred_faculty", ""),
            placeholder="Prof. Dawn Song (UC Berkeley), CyLab (CMU)",
        )

    back, nxt = _nav_buttons(2)
    if back:
        st.session_state["counseling_step"] = 1
        st.rerun()
    if nxt:
        st.session_state["counseling_step"] = 3
        st.rerun()


def render_step_preferences() -> None:
    data = st.session_state["counseling_data"]
    section_header("Geographic & Funding Preferences", "Define your boundary constraints for the AI agents.")

    data["target_countries"] = st.multiselect(
        "Target Countries / Regions",
        _COUNTRY_OPTIONS,
        default=[c for c in (data["target_countries"] or []) if c in _COUNTRY_OPTIONS],
        placeholder="Select target countries...",
    )
    cols = st.columns(2)
    with cols[0]:
        data["funding_requirement"] = st.selectbox(
            "Funding Requirement",
            _FUNDING_OPTIONS,
            index=_FUNDING_OPTIONS.index(data["funding_requirement"]) if data["funding_requirement"] in _FUNDING_OPTIONS else 0,
        )
    with cols[1]:
        data["target_intake"] = st.selectbox(
            "Target Academic Intake",
            _INTAKE_OPTIONS,
            index=_INTAKE_OPTIONS.index(data["target_intake"]) if data["target_intake"] in _INTAKE_OPTIONS else 2,
        )

    data["university_type"] = st.selectbox(
        "Preferred Institution Tier",
        _UNIVERSITY_TYPE_OPTIONS,
        index=_UNIVERSITY_TYPE_OPTIONS.index(data["university_type"]) if data["university_type"] in _UNIVERSITY_TYPE_OPTIONS else 0,
    )

    back, nxt = _nav_buttons(3)
    if back:
        st.session_state["counseling_step"] = 2
        st.rerun()
    if nxt:
        if not data["target_countries"]:
            st.warning("Please select at least one target country.", icon=":material/warning:")
        else:
            st.session_state["counseling_step"] = 4
            st.rerun()


def render_step_review() -> None:
    data = st.session_state["counseling_data"]
    section_header("Pre-Flight Profile Review", "Review your profile inputs before deploying the 9-agent workforce.")

    c1, c2 = st.columns(2)
    with c1:
        with st.container(key="review-academic-box", border=True):
            st.markdown("**Academic Identity**")
            st.markdown(f"- Name: **{data['name']}**")
            st.markdown(f"- Applying For: **{data['target_degree']}** in **{data['major']}**")
            st.markdown(f"- Current Institution: {data['university']} ({data['country']})")
            st.markdown(f"- GPA: **{data['cgpa']}** / {data['gpa_scale']}")
            if data.get("ielts"):
                st.markdown(f"- IELTS: **{data['ielts']}**")
            if data.get("gre"):
                st.markdown(f"- GRE: **{data['gre']}**")
            if data.get("sat_act"):
                st.markdown(f"- SAT/ACT: **{data['sat_act']}**")
    with c2:
        with st.container(key="review-pref-box", border=True):
            st.markdown("**Preferences & Funding**")
            st.markdown(f"- Target Countries: **{', '.join(data['target_countries'])}**")
            st.markdown(f"- Funding: **{data['funding_requirement']}**")
            st.markdown(f"- Target Intake: **{data['target_intake']}**")
            st.markdown(f"- Institution Type: **{data['university_type']}**")

    if data.get("research_domains") or data.get("research_interests") or data.get("projects"):
        with st.container(key="review-research-box", border=True):
            st.markdown("**Domain & Research Focus**")
            if data.get("research_domains"):
                st.markdown(f"- Specialization Domains: **{', '.join(data['research_domains'])}**")
            if data.get("research_interests"):
                st.markdown(f"- Focus Summary: {data['research_interests'][:250]}")
            if data.get("publications"):
                st.markdown(f"- Publications: **{data['publications']}**")

    st.success("Ready to begin. Click **Start AI Analysis** to deploy the multi-agent team.", icon=":material/check_circle:")

    back, nxt = _nav_buttons(4)
    if back:
        st.session_state["counseling_step"] = 3
        st.rerun()
    if nxt:
        st.session_state["counseling_step"] = 5
        st.rerun()


def _compose_request(data: dict) -> str:
    parts = [
        f"I am {data['name']}, an applicant targeting {data['target_degree']} programs in {data['major']} from {data['university']} ({data['country']}).",
    ]
    if data.get("cgpa"):
        parts.append(f"My cumulative GPA is {data['cgpa']} on a {data['gpa_scale']}.")
    scores = []
    if data.get("ielts"):
        scores.append(f"IELTS {data['ielts']}")
    if data.get("toefl"):
        scores.append(f"TOEFL {data['toefl']}")
    if data.get("gre"):
        scores.append(f"GRE {data['gre']}")
    if data.get("sat_act"):
        scores.append(f"SAT/ACT {data['sat_act']}")
    if scores:
        parts.append(f"Test scores: {', '.join(scores)}.")

    if data.get("research_interests"):
        parts.append(f"Research focus: {data['research_interests']}.")
    if data.get("research_domains"):
        parts.append(f"Preferred domains: {', '.join(data['research_domains'])}.")
    if data.get("publications"):
        parts.append(f"Publications: {data['publications']}.")
    if data.get("research_experience"):
        parts.append(f"Experience: {data['research_experience'][:250]}.")
    if data.get("skills"):
        parts.append(f"Technical skills: {data['skills']}.")

    parts.append(f"Target countries: {', '.join(data['target_countries'])}.")
    parts.append(f"Funding requirements: {data['funding_requirement']}.")
    parts.append(f"Intake: {data['target_intake']}.")
    return " ".join(parts)


def render_step_analysis() -> None:
    data = st.session_state["counseling_data"]
    profile_id = st.session_state.get("profile_id")
    session_title = f"{data.get('target_degree', 'Graduate')} in {data.get('major', 'General')} · {', '.join(data.get('target_countries', ['Global']))}"

    # Header
    _html(
        f"""
        <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 1rem 1.25rem; margin-bottom: 1.5rem;">
            <div style="font-size: 0.75rem; color: #6366F1; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;">Active AI Counseling Session</div>
            <div style="font-size: 1.15rem; font-weight: 800; color: #0F172A; margin-top: 0.15rem;">{session_title}</div>
        </div>
        """
    )

    if st.session_state.get("counseling_result"):
        result = st.session_state["counseling_result"]
        render_workflow_status(result)

        st.write("")
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            if st.button("✦ Start New Counseling Session", type="primary", use_container_width=True, icon=":material/refresh:"):
                del st.session_state["counseling_result"]
                del st.session_state["counseling_step"]
                del st.session_state["counseling_data"]
                st.rerun()
        with col_r2:
            st.page_link("pages/discover.py", label="Explore Full Opportunity Catalog →", icon=":material/school:")
        return

    if st.session_state.get("counseling_error"):
        render_backend_error(st.session_state["counseling_error"], key="counseling-analysis")
        if st.button("← Modify Profile & Retry", key="counseling-retry"):
            del st.session_state["counseling_error"]
            st.session_state["counseling_step"] = 4
            st.rerun()
        return

    # --- Pre-Execution Multi-Agent Grid ---
    agents_info = [
        ("Profile Analyst", "👤", "Extracting academic strengths & test signals", "● Running"),
        ("University Matcher", "🏫", "Discovering global programs aligned with criteria", "○ Waiting"),
        ("Scholarship Engine", "💰", "Identifying assistantships & merit funding", "○ Waiting"),
        ("Eligibility Verifier", "✅", "Validating minimum GPA & prerequisite criteria", "○ Waiting"),
        ("Research Alignment", "🔬", "Semantic mapping of thesis & faculty research", "○ Waiting"),
        ("Verification Agent", "🔍", "Grounding deadlines & tuition in official sources", "○ Waiting"),
        ("Ranking Engine", "⭐", "Computing multi-criteria Reach/Target/Safe scores", "○ Waiting"),
        ("SOP Generator", "📄", "Application document drafting checkpoint", "○ Waiting"),
    ]

    _html(
        """
        <div class="ep-supervisor-card">
          <div class="ep-supervisor-icon">✦</div>
          <div class="ep-supervisor-info">
            <div class="ep-supervisor-name">Supervisor Agent (Active Orchestrator)</div>
            <div class="ep-supervisor-desc">Coordinating your 8 specialist agents. Planning execution graph and evaluating data grounding.</div>
          </div>
        </div>
        """
    )

    cols = st.columns(2)
    for i, (name, icon, desc, status_text) in enumerate(agents_info):
        with cols[i % 2]:
            _html(
                f"""
                <div class="ep-agent-status-card {'running' if i == 0 else 'waiting'}">
                  <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                      <span style="font-size: 1.1rem;">{icon}</span>
                      <strong style="font-size: 0.92rem; color: #0F172A;">{name}</strong>
                    </div>
                    <span class="ep-badge {'indigo' if i == 0 else 'neutral'}" style="font-size: 0.68rem;">{status_text}</span>
                  </div>
                  <div style="font-size: 0.8rem; color: #64748B;">{desc}</div>
                </div>
                """
            )

    # --- Run Workflow ---
    request_text = _compose_request(data)
    payload = {
        "user_request": request_text,
        "workflow_type": "opportunity_discovery",
    }
    if profile_id:
        payload["student_profile_id"] = profile_id

    with st.status("Deploying AI workforce on your application...", expanded=True) as status:
        st.write("👤 Profile Analyst: Evaluating academic profile and language scores...")
        st.write("🏫 University Matcher: Querying university catalog across target countries...")
        st.write("💰 Scholarship Engine: Filtering graduate assistantships and fellowships...")
        st.write("🔬 Research Matcher: Aligning domain interests with faculty labs...")
        st.write("⭐ Ranking Engine: Sorting verified opportunities into Reach, Target, and Safe tiers...")
        try:
            result = analyze_counseling(payload)
        except BackendError as error:
            st.session_state["counseling_error"] = error
            status.update(label="Counseling workflow encountered an issue", state="error")
            st.rerun()
            return
        status.update(label="Counseling analysis complete! ✦", state="complete")

    st.session_state["counseling_result"] = result
    st.session_state["current_workflow_id"] = result.get("workflow_id")
    st.session_state["workflow_result"] = result
    from api.client import list_opportunities_cached
    list_opportunities_cached.clear()
    st.rerun()


def render() -> None:
    profile_id = st.session_state.get("profile_id")
    profile = st.session_state.get("profile")

    # Gate: Student must complete their previous academic background profile first
    if not profile_id or not profile or not profile.get("gpa") or not profile.get("field_of_study"):
        render_page_header(
            "AI Counseling Session",
            "Multi-agent academic matching, faculty discovery, and strategy planning.",
            eyebrow="Profile Required",
        )
        render_empty_state(
            "Complete Your Academic Background First",
            "EduPath AI requires your existing academic records (GPA, major/field of study, completed degree, and skills) to match you with appropriate future programs, scholarships, and faculty advisors.",
            icon="🧑‍🎓",
            cta_label="Set Up Academic Profile Now →",
            cta_page="pages/profile.py",
            key="counseling-profile-gate",
        )
        return

    _init_wizard()
    step = st.session_state.get("counseling_step", 0)

    render_page_header(
        "New AI Counseling Session",
        "Guided multi-agent intake tailored to your academic background.",
        eyebrow="AI Counseling",
    )

    # Connected Student Profile Summary Banner
    student_name = profile.get("name") or "Student"
    gpa = profile.get("gpa") or "N/A"
    major = profile.get("field_of_study") or "General"
    current_deg = profile.get("current_degree") or profile.get("academic_level") or "Undergraduate"
    _html(
        f"""
        <div style="background: linear-gradient(135deg, #EEF2FF 0%, #F8FAFC 100%); border: 1px solid #C7D2FE; border-radius: 12px; padding: 0.85rem 1.25rem; margin-bottom: 1.25rem; display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div style="font-size: 0.72rem; color: #4F46E5; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;">Student Academic Background</div>
                <div style="font-size: 0.95rem; font-weight: 700; color: #0F172A; margin-top: 0.15rem;">{student_name} · GPA: {gpa}/4.0 · Major: {major} · Background: {current_deg}</div>
            </div>
            <span class="ep-badge success" style="font-size: 0.72rem;">Academic Record Verified ✓</span>
        </div>
        """
    )

    _render_step_indicator(step)
    st.write("")

    with st.container(key="counseling-wizard-content", border=False):
        if step == 0:
            render_step_profile()
        elif step == 1:
            render_step_academic()
        elif step == 2:
            render_step_experience()
        elif step == 3:
            render_step_preferences()
        elif step == 4:
            render_step_review()
        elif step == 5:
            render_step_analysis()


render()
