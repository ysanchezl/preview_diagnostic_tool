---
name: debug-llm-proposal-failure
description: Diagnose why POST /api/v1/diagnostics/proposal (or /diagnostics/enrich) fails, times out, returns proposal_ok:false, or behaves differently than expected. Use whenever a request to either endpoint errors, hangs, or a teammate reports "the proposal/analysis isn't working" — before guessing, work through this checklist, most failures here are environment/config, not application bugs.
---

# Debug an LLM proposal/enrichment failure

This project's two LLM-calling endpoints (`/diagnostics/proposal`, `/diagnostics/enrich`) have several
known, previously-hit failure modes that look like application bugs but aren't. Work through these in
order before reading application code — most of the time spent debugging this in practice went into
finding which of these it was, not into fixing code.

## 1. Is the frontend even calling the backend you think it is?

Check `frontend-preview/.env.local` for `NEXT_PUBLIC_API_URL`. It can be pointing at the deployed Render
backend (`https://preview-diagnostic-tool.onrender.com`) instead of your local one — in that case your
local code changes have zero effect on what you see in the browser, and any bug you're chasing may actually
be a stale/differently-configured deployment, not your local code. Confirm which backend is live by hitting
both `/docs` endpoints directly with `curl` and comparing. Next.js only reads `.env.local` at dev-server
startup — restart `npm run dev` after changing it.

## 2. Is the configured Groq model still valid?

Symptom: `groq.NotFoundError: model_not_found`. `GROQ_MODEL` in `.env` gets deprecated by Groq without
warning. Check currently available models with `GET https://api.groq.com/openai/v1/models` (needs
`Authorization: Bearer $GROQ_API_KEY`) and update `GROQ_MODEL` in `.env` **and** the default in
`app/core/config.py`.

## 3. Have you hit Groq's rate limit or daily token quota?

Symptom: `groq.RateLimitError: Error code: 429`, with a message distinguishing "tokens per minute (TPM)"
(transient, retry in seconds) from "tokens per day (TPD)" (you're done until it resets — the error message
includes a wait time, e.g. "try again in 38m"). This is easy to hit by accident: testing this pipeline
repeatedly in one session (manual curl calls, re-running `pytest tests/test_diagnostics.py` against the
real API) burns through the daily quota fast, since `DiagnosticResponse` is a large schema and every call
is expensive in tokens. If you're mid-debugging-session and things that worked five minutes ago now fail
the same way every time, suspect this before suspecting your code change.

## 4. Is this the expected two-attempt retry, working as designed?

`app/agents/automation_graph.py::generate_with_llm` tries the LLM without `json_mode` first, retries once
with `json_mode` only if the failure is Groq's specific tool-call bug (`tool_use_failed`), and returns
`ProposalGenerationError(error_reason="llm_failed")` (HTTP 200, `proposal_ok: false`) if both attempts fail
or the first attempt fails for an unrelated reason. **A `proposal_ok: false` response is not necessarily a
bug** — it's the intended graceful-degradation path. Check the backend's log output for the
`logger.warning(...)` lines in that function (`exc_info=True`, so the real exception is printed) before
assuming something is broken; the log line tells you which of the two attempts failed and why.

## 5. Reproduce deterministically instead of retrying against the real API

Don't debug by repeatedly calling the real Groq API — it's slow (each `DiagnosticResponse` generation can
take up to ~90s with the retry), costs quota (see #3), and non-deterministic (the failure you're chasing
may not reproduce on demand). Instead, monkeypatch `get_chat_model` with a fake LLM whose
`with_structured_output(...).ainvoke(...)` raises or returns whatever you're trying to reproduce — see
`_FakeLLM`/`_FakeStructuredLLM` in `tests/test_diagnostics.py` (proposal path) or `tests/test_enrichment.py`
(enrichment path) for the existing pattern, and write a new test case rather than a one-off script.

## 6. `/diagnostics/enrich` specifically

Its catch-all exception handler (`app/api/v1/routes/enrichment.py`) logs the real exception via
`logger.warning(..., exc_info=True)` before collapsing everything to `error_reason: "unexpected_error"` in
the response — check the backend logs, the JSON response alone won't tell you the real cause. Also: many
real-world sites return `403 Forbidden` to this scraper because it identifies itself honestly as
`PreviewDiagnosticBot/1.0` (no browser spoofing) — that's an external site's WAF blocking it, not a bug
here. Test against a plain site (e.g. `https://example.com`) first to confirm the pipeline itself works
before troubleshooting a specific blocked target.
