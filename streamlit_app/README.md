# EduPath AI — Streamlit Frontend

A modern, premium Streamlit UI for the existing EduPath AI FastAPI backend.
This app contains **no** business logic, no database access, and never talks
to Gemini directly — every action goes through the backend's REST API.

```
Streamlit UI  ->  api/client.py  ->  FastAPI backend (backend/app)  ->  Agents  ->  Gemini
```

## Structure

```
streamlit_app/
├── app.py                  # Entrypoint: theme, auth gate, sidebar shell, navigation
├── .streamlit/config.toml  # Design system theme (colors, fonts, radii)
├── api/
│   ├── client.py           # Centralized HTTP client (GET/POST/PATCH/DELETE + auth header + error mapping)
│   └── exceptions.py       # BackendError (user-safe error type)
├── components/              # Reusable UI building blocks
│   ├── auth.py                login gate, dev-login form, OAuth redirect handling, logout
│   ├── sidebar.py             brand mark + signed-in user card + backend status
│   ├── header.py               page headers / hero banners
│   ├── metrics.py              metric cards
│   ├── profile_card.py         academic profile summary + completion bar
│   ├── profile_form.py         sectioned profile form (tag-style multiselects)
│   ├── opportunity_card.py     catalog opportunity card + details dialog
│   ├── ranked_opportunity_card.py  a discovered CandidateOpportunity + its real verdicts/score
│   ├── opportunity_list.py     sort/filter toolbar + card grid + pagination
│   ├── workflow_status.py      honest discovery-workflow progress, ranked results, approval UI, export
│   ├── evidence.py             renders Evidence (verified/unverified + source link)
│   ├── empty_state.py          empty & error state cards
│   └── common.py               shared small helpers
├── pages/
│   ├── dashboard.py         Dashboard (profile + catalog + last workflow)
│   ├── profile.py           My Profile (create/update + document upload)
│   ├── discover.py          Discover Opportunities (AI search + ranked results + catalog)
│   ├── saved.py             Saved Opportunities (session-only)
│   ├── tracker.py           Application Tracker (session-only)
│   ├── sop.py                Statement of Purpose (generate/revise/download, versioned)
│   ├── agent_trace.py        Real per-agent execution status + inter-agent messages
│   ├── execution_graph.py    The actual LangGraph topology (Graphviz), colored by live status
│   ├── memory.py              Long-term memory viewer (current preferences + search history)
│   ├── usage.py                Real token/cost usage across your workflows
│   └── settings.py            Backend connection + session tools
├── utils/
│   ├── config.py            env-driven settings (BACKEND_URL, timeouts)
│   ├── session.py           session_state registry + auth/save/tracker helpers
│   └── formatting.py        profile completion, deadlines, greetings, etc.
└── styles/main.css          design-system CSS layered on the theme
```

## Pages

- **Dashboard** — profile completion, catalog size, saved/application metrics, academic profile
  summary, upcoming-deadline opportunities, and the most recent discovery workflow.
- **My Profile** — sectioned profile form (Personal / Academic / PhD Goals / Research) with
  tag-style multiselects, plus CV/transcript/SOP document upload (`POST /api/v1/documents`).
- **Discover Opportunities** — the AI search box + quick filters that run the
  `opportunity_discovery` workflow, real ranked results with match scores and evidence, the
  human-approval gate when the workflow genuinely pauses, an Excel export button, and the
  structured opportunity catalog with sort/filter/save.
- **Saved Opportunities** / **Application Tracker** — session-only (the backend has no
  persistence endpoint for either), clearly labeled as such in the UI.
- **Statement of Purpose** — generate, revise (versioned), and download SOP drafts, grounded in
  your profile and uploaded documents via backend-side RAG.
- **Agent Trace** — real per-agent status and the real inter-agent communication log for a given
  workflow run.
- **Execution Graph** — the actual LangGraph topology, rendered with `st.graphviz_chart`, colored
  by a run's live agent statuses when one is loaded.
- **Memory** — what EduPath AI remembers: your current preferences and full search history.
- **Usage & Cost** — real token/cost totals aggregated across your workflows; never estimated.
- **Settings** — backend connection check and session reset.

## Authentication

`app.py` gates the whole app behind sign-in. `GET /api/v1/auth/config` tells the frontend which
flow to render: a real "Sign in with Google" link/redirect, or (when Google OAuth isn't configured
on the backend) a simple dev-mode email form. After a real Google login, the backend redirects back
here with `?token=...`; `components/auth.py::handle_oauth_redirect()` captures it and scrubs it
from the visible URL immediately. The token is attached as a `Bearer` header on every subsequent
API call automatically (`api/client.py::_auth_headers`).

## Configuration

Copy/edit `streamlit_app/.env`:

```
BACKEND_URL=http://localhost:8000
REQUEST_TIMEOUT_SECONDS=30
WORKFLOW_TIMEOUT_SECONDS=180
```

No API keys or OAuth secrets belong in this app — those stay in `backend/.env` only.

## Run

```bash
# 1. Backend (separate terminal)
cd ~/Projects/dev/edupath-ai
docker compose -f infrastructure/docker/compose.yaml up -d
cd backend
uv run alembic upgrade head
uv run python scripts/seed_catalog.py
uv run fastapi dev app/main.py

# 2. Frontend (another terminal)
cd streamlit_app
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
uv run streamlit run app.py
```

Then open http://localhost:8501.

If you already created the frontend virtual environment, run only:

```bash
cd ~/Projects/dev/edupath-ai/streamlit_app
source .venv/bin/activate
uv pip install -r requirements.txt
uv run streamlit run app.py
```

## Notes

- The `opportunity_discovery` workflow runs several sequential Gemini calls synchronously on the
  backend and can return a `429 LLMQuotaError` if the Gemini free-tier quota is exhausted. The UI
  surfaces this as a friendly "AI service is temporarily busy" message with the backend's
  `retry_after` hint — it does not retry automatically.
- When the workflow's plan includes SOP generation, it genuinely **pauses** (a real LangGraph
  `interrupt()`, not a cosmetic status) until you click Approve or Reject on the Discover page —
  those buttons resume the actual paused backend run.
- Real per-opportunity match scores now come from the backend's Research Match / Eligibility /
  Ranking agents (`ranked_opportunities`, `candidate_opportunities` on the workflow response) —
  nothing here is estimated client-side.
- Saved Opportunities and Application Tracker remain session-only/browser-local by design (see
  Pages above) — the backend intentionally doesn't persist these yet.
