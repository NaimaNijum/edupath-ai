from __future__ import annotations

import re
from datetime import UTC, datetime

import streamlit as st

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

_ACADEMIC_LEVELS = ["", "Undergraduate", "Master's", "PhD", "Postdoctoral", "Other"]
_DEGREES = ["", "BSc", "BA", "MSc", "MA", "MBA", "PhD", "Other"]
_FUNDING_OPTIONS = ["", "Fully Funded", "Partially Funded", "Self-Funded", "Any"]

_COMMON_COUNTRIES = [
    "USA", "Canada", "UK", "Germany", "Australia", "Netherlands", "Sweden",
    "Switzerland", "France", "Singapore", "Japan", "South Korea", "Ireland",
    "New Zealand", "Denmark", "Finland", "Norway",
]
_COMMON_RESEARCH_AREAS = [
    "Artificial Intelligence", "Machine Learning", "Deep Learning",
    "Natural Language Processing", "Computer Vision", "Robotics",
    "Data Science", "Human-Computer Interaction", "Cybersecurity",
    "Distributed Systems", "Bioinformatics", "Quantum Computing",
    "Software Engineering", "Computer Networks", "Theoretical Computer Science",
]
_COMMON_SKILLS = [
    "Python", "Java", "C++", "TensorFlow", "PyTorch", "SQL", "R",
    "JavaScript", "AWS", "Docker", "Kubernetes", "Git", "Linux", "MATLAB",
    "Research Writing",
]


def _split_list(raw: str) -> list[str]:
    if not raw or not raw.strip():
        return []
    parts = re.split(r"[,\n]", raw)
    return [part.strip() for part in parts if part.strip()]


def _join_list(items: list[str] | None) -> str:
    return ", ".join(items or [])


def _merged_options(base: list[str], existing: list[str] | None) -> list[str]:
    """Base option list plus any existing values not already in it, so a
    loaded profile with custom tags doesn't lose them in the widget."""
    existing = existing or []
    merged = list(base)
    for value in existing:
        if value not in merged:
            merged.append(value)
    return merged


def render_profile_form(existing: dict | None = None) -> dict | None:
    """Render the sectioned student profile form.

    Returns the validated payload dict (matching StudentProfileCreate /
    StudentProfileUpdate) when the user submits a valid form, otherwise None.
    """
    existing = existing or {}
    current_year = datetime.now(UTC).year

    with st.form("profile_form", clear_on_submit=False, border=False):
        st.markdown('<div class="ep-section-title">Personal Information</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Name", value=existing.get("name") or "", placeholder="e.g. Alex Johnson")
        with col2:
            email = st.text_input("Email *", value=existing.get("email") or "", placeholder="alex@example.com")

        st.divider()
        st.markdown('<div class="ep-section-title">Academic Background (Completed & Current Education)</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            academic_level = st.selectbox(
                "Current / Highest Academic Level", _ACADEMIC_LEVELS,
                index=_index_of(_ACADEMIC_LEVELS, existing.get("academic_level")),
            )
            field_of_study = st.text_input("Field of Study / Major", value=existing.get("field_of_study") or "", placeholder="e.g. Computer Science, Mechanical Engineering")
            existing_gpa = existing.get("gpa")
            gpa_value = min(max(float(existing_gpa), 0.0), 4.0) if existing_gpa is not None else 0.0
            gpa = st.number_input("Cumulative GPA (0.0 - 4.0 scale)", min_value=0.0, max_value=4.0, step=0.01, value=gpa_value)
        with col2:
            current_degree = st.selectbox(
                "Current / Completed Degree", _DEGREES,
                index=_index_of(_DEGREES, existing.get("current_degree")),
            )
            university = st.text_input("University / Institution Attended", value=existing.get("university") or "", placeholder="e.g. University of Dhaka, MIT")
            year_min, year_max = current_year - 15, current_year + 5
            existing_year = existing.get("graduation_year")
            year_value = min(max(int(existing_year), year_min), year_max) if existing_year else current_year
            graduation_year = st.number_input("Graduation Year (Completed or Expected)", min_value=year_min, max_value=year_max, step=1, value=year_value)

        st.divider()
        st.markdown('<div class="ep-section-title">Research, Skills & Academic Portfolio</div>', unsafe_allow_html=True)
        research_interests = st.multiselect(
            "Research Background & Focus Domains",
            options=_merged_options(_COMMON_RESEARCH_AREAS, existing.get("research_interests")),
            default=existing.get("research_interests") or [],
            accept_new_options=True,
            placeholder="Choose or type research areas you have worked on",
        )
        skills = st.multiselect(
            "Technical & Academic Skills",
            options=_merged_options(_COMMON_SKILLS, existing.get("skills")),
            default=existing.get("skills") or [],
            accept_new_options=True,
            placeholder="Choose or type your skills",
        )
        st.caption("For the fields below, separate multiple items with commas or line breaks:")
        publications = st.text_area("Publications & Papers (Titles, Conferences, Journals)", value=_join_list(existing.get("publications")), placeholder="e.g. Fast Neural Inference on Edge Devices, IEEE Access 2025")
        projects = st.text_area("Key Academic / Capstone Projects", value=_join_list(existing.get("projects")), placeholder="e.g. Autonomous Drone Navigation with ROS and PyTorch")
        work_experience = st.text_area("Research & Work Experience (Labs, Internships, Teaching)", value=_join_list(existing.get("work_experience")), placeholder="e.g. Undergraduate Research Assistant at AI Lab (2024-2025)")

        submitted = st.form_submit_button("Save Student Profile", use_container_width=True, type="primary")

    if not submitted:
        return None

    errors: list[str] = []
    if not email.strip():
        errors.append("Email is required.")
    elif not _EMAIL_RE.match(email.strip()):
        errors.append("Please enter a valid email address.")

    if errors:
        for error in errors:
            st.error(error, icon=":material/warning:")
        return None

    return {
        "name": name.strip() or None,
        "email": email.strip(),
        "academic_level": academic_level or None,
        "current_degree": current_degree or None,
        "field_of_study": field_of_study.strip() or None,
        "university": university.strip() or None,
        "gpa": gpa or None,
        "graduation_year": int(graduation_year),
        "target_degree": existing.get("target_degree") or None,
        "target_countries": existing.get("target_countries") or [],
        "research_interests": research_interests,
        "skills": skills,
        "publications": _split_list(publications),
        "projects": _split_list(projects),
        "work_experience": _split_list(work_experience),
        "preferred_funding": existing.get("preferred_funding") or None,
    }


def _index_of(options: list[str], value: object) -> int:
    if value and value in options:
        return options.index(value)
    return 0
