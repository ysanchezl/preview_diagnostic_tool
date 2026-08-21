# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

FastAPI backend (`app/`) + Next.js preview frontend (`frontend-preview/`) that turns a short business
diagnostic form into an AI-generated preliminary automation proposal (executive summary, prioritized
automation opportunities, a visual end-to-end workflow, ROI narrative, and implementation phases). It's a
lead-gen / sales-preview tool, not a full product: every proposal is explicitly framed as preliminary and
ends in a call to contact the team.

## Commands

Backend (run from repo root; requires Python >=3.13 — check with `python --version` before creating the
venv, since `app/schemas/diagnostic.py` uses `enum.StrEnum` which needs 3.11+):

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -e ".[dev]"
uvicorn app.main:app --reload   # serves http://127.0.0.1:8000
```

Tests and lint:

```bash
pytest                          # single test: pytest tests/test_diagnostics.py::test_create_proposal_with_mock_provider
ruff check .
```

Frontend (from `frontend-preview/`):

```bash
npm install
npm run dev                     # http://localhost:3000
npm run build
npm run lint
```

Config: copy `.env.example` to `.env` in the repo root. With `LLM_PROVIDER=mock` (or no API key set for the
configured provider), the backend falls back to a deterministic, non-LLM proposal — useful for frontend
development and tests without any API key.

## Architecture

**Request flow:** `frontend-preview` POSTs a `DiagnosticRequest` to
`POST /api/v1/diagnostics/proposal` → `app/api/v1/routes/diagnostics.py` →
`run_automation_diagnostic()` in `app/agents/automation_graph.py` → returns a `DiagnosticResponse`.

**LangGraph pipeline** (`app/agents/automation_graph.py`), a 2-node `StateGraph`:
1. `enrich_context` — calls the `get_business_profile` and `build_default_flow` LangChain tools
   (`app/agents/tools.py`) to fetch sector-specific guidance and a default 5-step visual workflow, purely
   in Python (no LLM call).
2. `generate_with_llm` — resolves a chat model via `app/llm/client.py`; if none is configured
   (`get_chat_model()` returns `None`), short-circuits to `fallback_response()` (deterministic mock). If a
   model exists, calls `llm.with_structured_output(DiagnosticResponse)` so the LLM is forced to return the
   exact Pydantic schema, seeded with `BASE_SYSTEM_PROMPT` (`app/prompts/system.py`) plus the per-request
   prompt from `build_user_prompt()` and the tool-enriched context appended inline.

**LLM provider selection** (`app/llm/client.py` + `app/core/config.py`): `LLM_PROVIDER` env var picks
between `groq` (`langchain_groq.ChatGroq`), `openai`, `azure_openai`, or falls through to `None` (mock) if
the provider is unset/unrecognized or its API key is missing. There is no explicit `"mock"` branch — mock
mode is really "no provider matched."

**Sector knowledge base** (`app/prompts/business_profiles.py`): a `BUSINESS_PROFILES` dict keyed by the
`BusinessType` enum (`app/schemas/diagnostic.py`) — one hand-written profile per vertical (law firm, dental
clinic, notary, gestoría, real estate, ecommerce, professional services, generic "other"), each with
`identity`, `common_pain_points`, `automation_opportunities`, `typical_tools`, `kpis`, `workflow_style`,
`constraints`, `tone`. This dict is the single source of both the LLM system-prompt context
(`format_business_profile`) and the deterministic fallback proposal (`fallback_response` in
`app/agents/tools.py`) — the two paths intentionally read from the same profile so mock and LLM output stay
thematically consistent. Adding a new business vertical means: add an enum value + label in
`BusinessType`, add a matching entry in `BUSINESS_PROFILES`, and add it to the frontend's `businessTypes`
array in `frontend-preview/app/page.tsx`.

**Schema contract** (`app/schemas/diagnostic.py`): `DiagnosticResponse` and its nested models
(`FlowStep`, `AutomationOpportunity`, `RoiEstimate`) use `model_config = ConfigDict(extra="forbid")` and are
the literal shape the LLM is constrained to produce via structured output — the frontend's hand-mirrored
TypeScript types in `frontend-preview/app/page.tsx` (`DiagnosticResponse`, `FlowStep`,
`AutomationOpportunity`) must stay in sync with this file manually; there's no shared schema generation
between backend and frontend.

**Frontend** (`frontend-preview/app/page.tsx`): a single client component — form state, a hardcoded
`sampleProposal` shown before the first real submission, `fetch()` to
`${NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000"}/api/v1/diagnostics/proposal`, and a results view that
renders `automations`, `flow` (via a `suggested_icon` → lucide-react icon lookup in `iconMap`), ROI, and
phases. No routing, no component split, no state management library — everything lives in this one file.
