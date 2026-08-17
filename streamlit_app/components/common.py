from __future__ import annotations

import streamlit as st

from api.exceptions import BackendError
from components.empty_state import render_error_card
from utils.config import BACKEND_URL


def render_backend_error(error: BackendError, *, key: str = "generic") -> bool:
    """Render a user-friendly error card for a BackendError. Never shows raw
    tracebacks or provider payloads. Returns True if the user clicked Retry."""
    if error.is_connection_error:
        return render_error_card(
            "Unable to connect to EduPath AI",
            f"Make sure the FastAPI backend is running at `{BACKEND_URL}`.",
            retry_key=key,
        )
    if error.is_quota_error:
        return render_error_card(
            "AI service is temporarily busy",
            error.message,
            retry_key=key,
        )
    return render_error_card("Something went wrong", error.message, retry_key=key)


def section_header(title: str, subtitle: str | None = None) -> None:
    st.markdown(f'<div class="ep-section-title">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="ep-section-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def confidence_label(confidence: float | None) -> str | None:
    if confidence is None:
        return None
    return f"{round(confidence * 100)}%"
