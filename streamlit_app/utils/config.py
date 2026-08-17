from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Load streamlit_app/.env regardless of the process's current working directory.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
REQUEST_TIMEOUT_SECONDS = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))
# The opportunity_discovery workflow runs several sequential Gemini calls
# synchronously on the backend, so it needs a much longer client timeout.
WORKFLOW_TIMEOUT_SECONDS = float(os.getenv("WORKFLOW_TIMEOUT_SECONDS", "180"))
