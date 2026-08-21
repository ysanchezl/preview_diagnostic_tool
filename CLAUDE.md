# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

FastAPI backend (`app/`) + Next.js preview frontend (`frontend-preview/`) that turns a short business
diagnostic form into an AI-generated preliminary automation proposal (executive summary, prioritized
automation opportunities, a visual end-to-end workflow, ROI narrative, and implementation phases). It's a
lead-gen / sales-preview tool, not a full product: every proposal is explicitly framed as preliminary and
ends in a call to contact the team. It also has an optional website-enrichment feature: given a business's
URL, it scrapes the public site and uses the LLM to pre-fill parts of the diagnostic form.

Business-sector guidance (`BUSINESS_PROFILES`) is a static, hand-written dict — there is no database or
retrieval layer in this repo. A Postgres/pgvector-backed semantic retrieval version was prototyped and
fully removed as unnecessary complexity for the current scope; see
`docs/future-evolution/business-profile-rag.md` if that direction is revisited later.

## Commands

Backend (run from repo root; requires Python >=3.11, since `app/schemas/diagnostic.py` uses
`enum.StrEnum`):

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

## Known gotchas (learned the hard way — read before debugging)

- **Groq model names change.** If a request fails with `groq.NotFoundError: model_not_found`, the
  `GROQ_MODEL` in `.env` has probably been deprecated by Groq. Check currently available models with
  `GET https://api.groq.com/openai/v1/models` (needs `Authorization: Bearer $GROQ_API_KEY`) and update
  `GROQ_MODEL` in `.env` **and** the default in `app/core/config.py`.
- **Groq + `with_structured_output` on large/nested schemas fails.** Symptom:
  `Tool call validation failed: ... attempted to call tool 'json' which was not in request.tools`. Fix is to
  pass `method="json_mode"` to `with_structured_output(...)` (already done in `automation_graph.py` and
  `agents/enrichment.py`) — the default function-calling method breaks on Groq's `gpt-oss` models once the
  schema gets big enough (this is exactly what `DiagnosticResponse` triggered).
- **Unhandled exceptions lose CORS headers** (Starlette/FastAPI quirk: `ServerErrorMiddleware` sits outside
  `CORSMiddleware`, so a raw 500 has no `Access-Control-Allow-Origin` header and the browser reports a
  generic `NetworkError` instead of showing the real error). `app/main.py` registers a catch-all
  `@app.exception_handler(Exception)` specifically to route errors through the middleware stack correctly —
  don't remove it, and don't let new routes leak unhandled exceptions past it without good reason.
- **`uvicorn --reload` on Windows sometimes hangs mid-reload**, leaving a stale worker process that keeps
  serving old code on the port while looking alive. If behavior doesn't match a recent edit, don't trust
  `--reload` — kill the uvicorn process tree and restart it clean.
- **Never run `npm run build` while `npm run dev` is running** against the same `frontend-preview/`
  directory — they fight over the `.next` cache and you'll get `React Client Manifest` / `webpack_modules`
  errors in the dev server. If it happens, stop the dev server, delete `.next`, restart `npm run dev`.

## Architecture

**Request flow:** `frontend-preview` POSTs a `DiagnosticRequest` to
`POST /api/v1/diagnostics/proposal` → `app/api/v1/routes/diagnostics.py` →
`run_automation_diagnostic()` in `app/agents/automation_graph.py` → returns a `DiagnosticResponse`.
The same router also exposes `GET /api/v1/diagnostics/business-types`, a trivial listing of
`BusinessType` enum values/labels used to populate the frontend's business-type dropdown.

**LangGraph pipeline** (`app/agents/automation_graph.py`), a 2-node `StateGraph`:
1. `enrich_context` — calls the `get_business_profile` and `build_default_flow` LangChain tools
   (`app/agents/tools.py`) to fetch sector-specific guidance (a static lookup into the `BUSINESS_PROFILES`
   dict, see below) and a default 5-step visual workflow.
2. `generate_with_llm` — resolves a chat model via `app/llm/client.py`; if none is configured
   (`get_chat_model()` returns `None`), short-circuits to `fallback_response()` (deterministic mock). If a
   model exists, calls `llm.with_structured_output(DiagnosticResponse, method="json_mode")` (see gotcha
   above for why `json_mode` specifically) so the LLM is forced to return the exact Pydantic schema, seeded
   with `BASE_SYSTEM_PROMPT` (`app/prompts/system.py`) plus the per-request prompt from `build_user_prompt()`
   and the tool-enriched context appended inline.

**Website enrichment pipeline** (separate feature, does not touch the pipeline above):
`POST /api/v1/diagnostics/enrich` → `app/api/v1/routes/enrichment.py` →
`app/services/scraper.py` (`fetch_site_text`) → `app/agents/enrichment.py` (`extract_website_signals`) →
`WebsiteEnrichmentResponse`. Notes:
- The scraper fetches the home page plus a few candidate "about us"/"services" paths (in parallel),
  respects `robots.txt` (`_load_robots_parser`/`_is_allowed`), and identifies itself honestly via
  `USER_AGENT = "PreviewDiagnosticBot/1.0"` — no browser spoofing, no proxy rotation. It returns
  `home_text` and `about_text` separately so the extraction prompt can tell them apart; single-page sites
  with no dedicated "about" page fall back to using `home_text` for pain-point inference.
- Requests are throttled per-IP (`app/core/rate_limit.py`, in-memory, 5s cooldown) and the whole
  scrape+extract call is wrapped in a ~25s timeout; scraping failures (timeout, `robots_disallowed`,
  connection errors) return `scraped_ok=false` with a reason instead of a 500.
- `extract_website_signals` suggests `company_name`, `business_type`, `detected_tools`, and — separately —
  `candidate_pain_points`/`candidate_objectives`. The prompt explicitly forbids inventing pain points when
  the scraped "about" content is too thin, and forces Spanish output regardless of the source site's
  language.
- **Frontend contract**: `suggested_*` fields (company name, business type, tools) get merged straight into
  the form with a "Sugerido, verifica o edita" highlight. `candidate_pain_points`/`candidate_objectives` are
  intentionally **not** auto-filled — they render in a separate review panel and only land in the real form
  fields when the user explicitly accepts them (checkbox + "Añadir seleccionados" / "Usar esta sugerencia").
  Don't change this to silent auto-fill without checking with the user first — it was a deliberate decision.

**LLM provider selection** (`app/llm/client.py` + `app/core/config.py`): `LLM_PROVIDER` env var picks
between `groq` (`langchain_groq.ChatGroq`), `openai`, `azure_openai`, or falls through to `None` (mock) if
the provider is unset/unrecognized or its API key is missing. There is no explicit `"mock"` branch — mock
mode is really "no provider matched."

**Sector knowledge base** (`app/prompts/business_profiles.py`): a `BUSINESS_PROFILES` dict keyed by the
`BusinessType` enum (`app/schemas/diagnostic.py`) — one hand-written profile per vertical (law firm, dental
clinic, notary, gestoría, real estate, ecommerce, professional services, change-management/innovation
consulting, generic "other"), each with `identity`, `common_pain_points`, `automation_opportunities`,
`typical_tools`, `kpis`, `workflow_style`, `constraints`, `tone`. This dict is the single source of both the
LLM system-prompt context (`format_business_profile`) and the deterministic fallback proposal
(`fallback_response` in `app/agents/tools.py`) — the two paths intentionally read from the same profile so
mock and LLM output stay thematically consistent. Adding a new business vertical means: add an enum value +
label in `BusinessType`, add a matching entry in `BUSINESS_PROFILES`, and add it to the frontend's
`businessTypes` array in `frontend-preview/app/page.tsx`.

**Schema contract** (`app/schemas/diagnostic.py`): `DiagnosticResponse` and its nested models
(`FlowStep`, `AutomationOpportunity`, `RoiEstimate`) use `model_config = ConfigDict(extra="forbid")` and are
the literal shape the LLM is constrained to produce via structured output — the frontend's hand-mirrored
TypeScript types in `frontend-preview/app/page.tsx` (`DiagnosticResponse`, `FlowStep`,
`AutomationOpportunity`) must stay in sync with this file manually; there's no shared schema generation
between backend and frontend. `pain_points` allows up to 10 items (raised from 5 to match the number of
candidate pain points the enrichment flow can suggest).

**Frontend** (`frontend-preview/app/page.tsx`): a single client component — no routing, no component split,
no state management library, everything lives in this one file. The form and the proposal panel both start
empty (placeholders explain what to type; there's no hardcoded sample data anymore), and the proposal panel
only fills in after a real `/diagnostics/proposal` call. `fetch()` calls
`${NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000"}/api/v1/diagnostics/...`; the results view renders
`automations`, `flow` (via a `suggested_icon` → lucide-react icon lookup in `iconMap`), ROI, and phases.
Backend validation errors (Pydantic 422s) are translated into readable Spanish messages client-side
(`extractErrorMessage`/`friendlyValidationMessage`) instead of being dumped raw.
