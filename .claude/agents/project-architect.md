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
- **Structured output, not free text.** LLM calls go through
  `llm.with_structured_output(DiagnosticResponse, method="json_mode")`. `method="json_mode"` is required,
  not incidental — Groq's `gpt-oss` models fail function-calling structured output once the schema is big
  enough (`Tool call validation failed: ... attempted to call tool 'json'...`). Never change this back to
  the default method when touching `automation_graph.py` or `agents/enrichment.py`.
- **Mock mode is the absence of a provider**, not an explicit branch — `get_chat_model()` returns `None`
  when `LLM_PROVIDER` is unset/unrecognized or its key is missing, and callers short-circuit to a
  deterministic fallback. Any new LLM-calling code path needs its own `None`-check + fallback if it should
  work without an API key, matching this project's existing "works with zero config" bar.
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
