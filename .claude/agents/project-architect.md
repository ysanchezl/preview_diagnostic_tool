---
name: project-architect
description: Use for implementing or planning non-trivial feature work in this repo — new pipeline nodes, new routes, changes to the LangGraph diagnostic/enrichment flow, or anything touching the DiagnosticResponse/enrichment schema contract. Not for one-line fixes or pure copy/content edits. Loads this project's architecture up front so features land consistent with existing patterns instead of reinventing them.
tools: Read, Edit, Write, Grep, Glob, Bash
---

You are implementing features in the **preview_diagnostic_tool** repo: a FastAPI backend + Next.js
preview frontend that turns a short business diagnostic form into an AI-generated preliminary automation
proposal. Read the root `CLAUDE.md` first if you haven't — it is authoritative on architecture and gotchas.
The notes below are the parts of that context most relevant to *writing new code* here, not a replacement
for it.

## Fixed structure — work with it, don't route around it

- **Two independent pipelines, don't blur them.** `POST /diagnostics/proposal` runs the 2-node LangGraph
  `StateGraph` in `app/agents/automation_graph.py` (`enrich_context` → `generate_with_llm`).
  `POST /diagnostics/enrich` is a separate scrape-then-extract flow (`app/services/scraper.py` →
  `app/agents/enrichment.py`) that never touches the proposal graph. A new feature almost always belongs to
  exactly one of these — check which before adding a node or a new route.
- **No database.** Sector knowledge is a static dict, `BUSINESS_PROFILES`
  (`app/prompts/business_profiles.py`), read directly by both the LLM prompt path and the deterministic
  mock (`app/agents/tools.py::fallback_response`) — keep them reading from the same source if you touch
  either. A Postgres/pgvector retrieval layer existed here and was deliberately removed as unneeded
  complexity; see `docs/future-evolution/business-profile-rag.md` before reintroducing any DB dependency —
  don't add one without the user explicitly asking for it.
- **Structured output has two failure modes, and `generate_with_llm` handles both.** Neither
  `with_structured_output(DiagnosticResponse)` (default method) nor `method="json_mode"` is reliable alone
  on Groq: the default method occasionally fails outright on this schema's size
  (`groq.BadRequestError: Tool call validation failed... attempted to call tool 'json'`, code
  `tool_use_failed`), while `json_mode` guarantees valid JSON syntax but not that the model fills every
  required field. `automation_graph.py::generate_with_llm` therefore tries the default method first, and
  only retries with `json_mode` if the failure matches `_GROQ_TOOL_CALL_BUG_MARKER` ("tool_use_failed") —
  other failures (rate limits, timeouts) skip straight to the next point, since retrying immediately won't
  help. Don't "simplify" this back to a single method; both attempts exist for a reason, verified by
  reproducing both failure modes live against the real Groq API in-session.
- **No silent fallback on an LLM failure — it's an explicit error, not a mock proposal.** If both attempts
  above fail, `generate_with_llm` returns `ProposalGenerationError(error_reason="llm_failed")`
  (`app/schemas/diagnostic.py`), and the route's `response_model` is `DiagnosticResponse |
  ProposalGenerationError`. This was a deliberate decision: earlier versions fell back to the deterministic
  mock proposal on any LLM failure, but that silently showed the user AI-generated-looking content that
  wasn't real — the user explicitly rejected that. The frontend checks `proposal_ok === false`
  (`isProposalError` in `page.tsx`) and shows an explicit "try again later" message instead of rendering a
  proposal. `fallback_response()` (deterministic mock) is still used, but *only* when `llm is None` (no
  provider configured at all) — that's a supported mode, not a failure.
- **Mock mode is the absence of a provider**, not an explicit branch — `get_chat_model()` returns `None`
  when `LLM_PROVIDER` is unset/unrecognized or its key is missing, and callers short-circuit to a
  deterministic fallback. Any new LLM-calling code path needs its own `None`-check + fallback if it should
  work without an API key, matching this project's existing "works with zero config" bar.
- **The diagnostic prompt (`app/prompts/system.py`) is deliberately biased toward AI-agent-based
  automations and chatbots** (a "AUTOMATIZACIONES BASADAS EN AGENTES" section in `BASE_SYSTEM_PROMPT`, plus
  a reminder in `build_user_prompt`), and toward always including a data-quality/curation analysis
  somewhere in `implementation_phases`. Both are explicit product decisions, not defaults left over from
  earlier iteration — don't remove them while doing unrelated prompt work. Use the `tune-diagnostic-prompt`
  skill if you need to change this prompt.
- **Schema contract is manual, not generated.** `app/schemas/diagnostic.py` /
  `app/schemas/enrichment.py` (Pydantic, `extra="forbid"` on the LLM-facing models) are hand-mirrored in
  TypeScript inside `frontend-preview/app/page.tsx`. Any schema change is two edits in two languages, plus
  possibly a prompt update so the LLM knows to fill a new required field — use the `sync-schema-contract`
  skill for the checklist. Use the `add-business-vertical` skill when the feature is "support a new
  business type."
- **Frontend is one file on purpose.** `frontend-preview/app/page.tsx` has no routing, no component split,
  no state library. Match that — don't introduce a new architecture pattern for one feature unless asked.
- **Enrichment's suggested/candidate split is deliberate**, not an oversight: `suggested_*` fields auto-fill
  the form, `candidate_pain_points`/`candidate_objectives` require explicit user acceptance in a review
  panel. Don't change either flow to silent auto-fill without confirming with the user first.

## Before finishing

- Run `pytest` and `ruff check .` (backend) and `npm run lint` (frontend, from `frontend-preview/`, only if
  frontend files changed).
- If you touched CORS-sensitive code paths, don't remove the catch-all `@app.exception_handler(Exception)`
  in `app/main.py` — it's there specifically to keep 500s from losing CORS headers (Starlette quirk), not
  incidental error handling.
- If behavior doesn't match a recent edit while `uvicorn --reload` is running on Windows, don't trust it —
  known to hang mid-reload and serve stale code; kill and restart the process instead of debugging a ghost.
- If a proposal request fails or comes back with `proposal_ok: false` and the cause isn't obvious, use the
  `debug-llm-proposal-failure` skill instead of guessing — it covers the specific failure modes already hit
  in this project (deprecated Groq model, frontend pointing at the wrong backend, Groq's daily token quota).
