# EduPath AI — System Architecture

## Overview

```
┌──────────────────┐      HTTP/JSON       ┌──────────────────┐      asyncio.to_thread     ┌──────────────────┐
│ Streamlit         │ ───────────────────▶ │ FastAPI            │ ─────────────────────────▶ │ LangGraph          │
│ (streamlit_app/)   │ ◀─────────────────── │ (backend/app/api)   │ ◀───────────────────────── │ (backend/app/graph) │
└──────────────────┘                       └────────┬─────────┘                             └────────┬─────────┘
                                                       │                                                │
                                                       ▼                                                ▼
                                            ┌──────────────────┐                              ┌──────────────────┐
                                            │ PostgreSQL +       │◀─────────────────────────────│ 9 Agents           │
                                            │ pgvector, Redis     │                              │ (backend/app/agents) │
                                            └──────────────────┘                              └────────┬─────────┘
                                                                                                          │
                                                                                                          ▼
                                                                                                ┌──────────────────┐
                                                                                                │ Gemini              │
                                                                                                │ (google-genai)       │
                                                                                                └──────────────────┘
```

The Streamlit frontend is a thin client: it holds no business logic and never talks to Gemini
directly. Every AI action, every database write, and every piece of ranking logic lives in the
FastAPI backend.

## Frontend/Backend Communication

`streamlit_app/api/client.py` is the single point of contact with the backend. Every function
mirrors a backend Pydantic schema by name (e.g. `create_profile` ↔ `StudentProfileCreate`). A
bearer JWT (from `st.session_state["auth_token"]`) is attached to every request automatically once
the user is signed in. Errors are normalized into a `BackendError` with a pre-computed, user-safe
message — raw tracebacks and provider payloads never reach the UI (see `_friendly_error_for_response`).

## Multi-Agent Architecture

Each agent lives in its own package under `backend/app/agents/<name>/agent.py`, following an
identical shape: `build_<name>_agent(provider=None) -> Callable[[dict], dict]`, a closure over an
`GeminiProvider` (or an injected fake, for tests). Every agent:

1. Reads whatever it needs from the shared `EduPathState` dict.
2. Calls `ensure_llm_budget()` (`app/agents/context.py`) to reserve a Gemini call slot — this is a
   hard, workflow-level circuit breaker (`settings.max_llm_calls_per_workflow`) independent of
   Gemini's own quota, so a misbehaving plan can never loop forever.
3. Calls `provider.generate_structured(...)` with a Pydantic response model — every agent's
   output is structured JSON, never free narrative text.
4. Wraps the call in `try/except LLMError` (all agents as of this build) so one agent's Gemini
   failure degrades to a soft `{"errors": [...]}` state patch instead of crashing the workflow;
   `LLMQuotaError` still propagates, since a fallback would just burn the remaining quota.
5. Returns a **state patch** — a partial dict merged into `EduPathState` by LangGraph's reducers.

### Anti-Hallucination Design

This is the architectural throughline, not an afterthought:

- **Discovery agents never invent structured data.** `candidates_from_tool_results()`
  (`app/agents/context.py`) builds `CandidateOpportunity` entries deterministically, in Python,
  straight from already-fetched tool results (real DB rows or search hits). The LLM only narrates
  what was found — it cannot fabricate an id, URL, or metadata field, because it's never asked to
  produce them.
- **Every non-trivial claim carries `Evidence`** (`app/schemas/opportunity_candidate.py`):
  `source_url`, `source_type`, `verified: bool`, `retrieved_at`. The frontend renders a
  verified/unverified badge, never a bare assertion.
- **Eligibility/Verification agents distinguish confidence levels explicitly** — `eligible` is one
  of `verified_eligible | likely_eligible | verified_ineligible | unknown`, never a bare boolean
  that hides whether something was actually confirmed.
- **Ranking is deterministic Python**, not an LLM guess (`app/graph/ranking.py`) — configurable
  weights (`settings.ranking_weight_*`), reproducible given the same verdicts.
- **No individual professor records were seeded.** `scripts/seed_catalog.py` deliberately seeds
  only universities/programs and major, well-known funding programs (real, stable, verifiable
  organizations) — named-person bios/emails are the highest-risk hallucination surface and
  weren't live-verifiable at build time.
- **No fabricated deadlines.** Seeded opportunities carry `deadline: null` with a note to check
  the official site, rather than a plausible-looking but potentially wrong date.

## Shared State

`EduPathState` (`app/graph/state.py`) is a `TypedDict(total=False)`, not a loose dict — every
field has a declared type. Two reducer families are used:

- `_append`: blind concatenation, for `agent_results`, `agent_messages`, `errors`, etc. — history
  that should only grow.
- `_merge_by_key(field)`: upserts by id, for `candidate_opportunities` (keyed by `.id`) and the
  three verdict lists (keyed by `.opportunity_id`) — so a later turn enriches an existing entry
  rather than duplicating it.

Scalar fields (`profile`, `execution_plan`, `ranked_opportunities`, ...) are plain overwrite-on-set,
matching LangGraph's default behavior for un-annotated fields.

## Tools

`ToolingService.build_context()` runs all four tools **once, up front**, before the graph even
starts — not per-agent, mid-graph. Results are stored in `state["tool_results"]` and read by
agents via `grounded_context()`. Three tools (`university_search`, `professor_search`,
`opportunity_search`) query Postgres directly via keyword-OR `ILIKE` matching
(`app/core/search.py::extract_keywords` — a fix applied during this build: the original
implementation matched an entire free-text sentence as one literal substring, which silently
returned zero results for virtually any realistic query). `web_search` is a generic HTTP adapter
that honestly reports `tool_status: "unavailable"` when no provider is configured, rather than
fabricating results.

## Memory

Two layers:

- **Short-term**: the LangGraph state itself, scoped to one workflow run. (A separate
  `ShortTermMemory` dataclass existed in the codebase but was never wired in anywhere — removed as
  dead code.)
- **Long-term**: the `memory_entries` table, with a real pgvector `embedding` column.
  `MemoryService.record_workflow_context()` writes **two** rows per run: an always-upserted
  `current_preferences` row (fast profile-level context loading) and a new, never-overwritten
  `workflow_history` row scoped by `workflow_id` — this is what makes memory an actual
  accumulating history rather than a single row replaced every time. `load_context()` performs a
  real pgvector cosine-distance similarity search (`MemoryRepository.search_similar`), falling
  back to an unordered listing if embeddings are temporarily unavailable.

## RAG (Documents)

`documents` and `document_chunks` tables (the latter with a pgvector `embedding` column).
`DocumentService.upload()` extracts text (`pypdf` for PDF, `python-docx` for DOCX, plain decode
for TXT), chunks it (~1000 chars, 150-char overlap), and embeds each chunk — gracefully continuing
without embeddings if the provider is temporarily down, since the raw `content_text` is still
useful. `retrieve_relevant_chunks()` is called from `SOPService.generate()` to ground SOP drafts
in the student's actual uploaded documents, not just profile fields.

## Database

11 original tables plus `users`, `documents`, and `document_chunks` added during this build (3
Alembic migrations total). See `backend/app/database/models/entities.py` for the full schema.
Notable relationships: `StudentProfile.user_id` (nullable FK to `users`) links a profile to an
authenticated account when one is present, without requiring auth for anonymous use (profiles,
workflows, and documents all remain creatable without logging in, matching the pre-existing
permission model).

## Human-in-the-Loop

See [`workflow.md`](workflow.md) for the full mechanics. In short: `approval_gate`
(`app/graph/approval_gate.py`) calls LangGraph's real `interrupt()`, which actually suspends graph
execution and returns control to the caller with a `__interrupt__` payload.
`WorkflowService.execute()`/`.resume()` detect this and persist `workflow_status:
"awaiting_approval"` instead of `"completed"`. A later, separate HTTP call
(`POST /workflows/{id}/approve` or `/reject`) resumes the *same paused run* via
`graph.invoke(Command(resume=...), {"configurable": {"thread_id": ...}})` — verified to work
correctly across separate `CompiledGraph` Python objects (a fresh graph is built per request), as
long as they share the process-wide cached `MemorySaver` checkpointer
(`app/graph/checkpoints.py::build_checkpointer`, `@lru_cache`d).

## Observability

Every agent execution and every inter-agent message is persisted (`agent_executions`,
`agent_messages` tables), including token usage and estimated cost per agent. Structured logging
(`structlog`) throughout the LLM provider and workflow layers. `GET /workflows/{id}/agents`,
`/messages`, and `/logs` expose this for the frontend's Agent Trace and Execution Graph pages —
which render only what actually happened, never a simulated animation.
