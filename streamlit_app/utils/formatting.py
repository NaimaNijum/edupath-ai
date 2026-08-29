from __future__ import annotations

from datetime import date, datetime

# Fields used to compute profile completion based on historical academic background and portfolio
_PROFILE_COMPLETION_FIELDS = (
    "name",
    "email",
    "academic_level",
    "current_degree",
    "field_of_study",
    "university",
    "gpa",
    "graduation_year",
    "research_interests",
    "skills",
    "projects",
    "work_experience",
)


def profile_completion(profile: dict | None) -> int:
    """Percentage (0-100) of the profile's real fields that are filled in."""
    if not profile:
        return 0
    filled = 0
    for field in _PROFILE_COMPLETION_FIELDS:
        value = profile.get(field)
        if isinstance(value, list):
            filled += 1 if value else 0
        elif isinstance(value, (int, float)):
            filled += 1
        else:
            filled += 1 if value else 0
    return round(filled / len(_PROFILE_COMPLETION_FIELDS) * 100)


def greeting_for_now() -> str:
    hour = datetime.now().hour
    if hour < 12:
        return "Good morning"
    if hour < 18:
        return "Good afternoon"
    return "Good evening"


def initials(name: str | None, fallback: str = "?") -> str:
    if not name or not name.strip():
        return fallback
    parts = [p for p in name.strip().split() if p]
    if not parts:
        return fallback
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def format_deadline(raw: str | None) -> str | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).strftime("%B %d, %Y")
    except ValueError:
        return raw


def days_until(raw: str | None) -> int | None:
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    target = dt.date() if isinstance(dt, datetime) else dt
    return (target - date.today()).days


def deadline_urgency(raw: str | None) -> str | None:
    """Returns 'danger' | 'warning' | 'neutral' based on days remaining, or
    None when there's no deadline to judge."""
    remaining = days_until(raw)
    if remaining is None:
        return None
    if remaining < 0:
        return "neutral"
    if remaining <= 14:
        return "danger"
    if remaining <= 45:
        return "warning"
    return "neutral"


def format_amount(amount: float | None) -> str | None:
    if amount is None:
        return None
    return f"${amount:,.0f}"
