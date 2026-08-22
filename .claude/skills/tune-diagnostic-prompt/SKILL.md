---
name: tune-diagnostic-prompt
description: Change what kind of automation proposals the LLM generates — tone, priorities (e.g. bias toward a certain solution type), required sections, or content rules. Use whenever the request is about changing what the AI proposes/writes, not about the request/response schema or the pipeline code.
---

# Tune the diagnostic proposal prompt

The content and "personality" of every AI-generated proposal comes from two prompt strings in
`app/prompts/system.py`: `BASE_SYSTEM_PROMPT` (fixed, sets rules/tone/structure) and `build_user_prompt()`
(built per-request, includes the sector profile and a numbered list of what to generate). Both feed into
`app/agents/automation_graph.py::generate_with_llm` via `llm.with_structured_output(DiagnosticResponse,
...)` — the LLM is still constrained to the exact `DiagnosticResponse` schema regardless of prompt wording;
prompt changes affect *what goes in the fields*, not the shape.

## Where to make the change

1. **`BASE_SYSTEM_PROMPT`** — add or edit a labeled section (existing ones: `OBJETIVO`, `REGLAS GENERALES`,
   `AUTOMATIZACIONES`, `AUTOMATIZACIONES BASADAS EN AGENTES`, `WORKFLOW`, `FASES DE IMPLEMENTACION`, `ROI`,
   `TONO`). This is where standing rules that apply to every request go.
2. **`build_user_prompt()`**'s numbered list (`Genera una propuesta preliminar con: 1. ... 8. ...`) — add a
   short reinforcing line here too if the rule is important. In practice, a rule stated only once in the
   system prompt is followed less reliably than one stated in both places — this project already does this
   for the agent/chatbot bias and the data-quality-phase rule, follow the same pattern for new ones.

## Keep the mock path thematically consistent

`app/agents/tools.py::fallback_response()` is the deterministic (non-LLM) proposal, used when no provider
is configured. It's hand-written, so a prompt change doesn't automatically apply to it — if the change is
about *content* (e.g. "always mention X"), also update the relevant string(s) in `fallback_response()` so
mock and LLM output stay aligned, per the project's existing convention (see the "Sector knowledge base"
section of the root `CLAUDE.md`).

## Verifying the change actually did something

Prompt changes can't be verified by `pytest`/`ruff` alone — those check schema validity and code style, not
content. To actually see the effect:

1. `pytest` and `ruff check .` first, to make sure nothing is syntactically broken.
2. Check `fallback_response()`'s output directly (no API calls, no quota risk):
   ```
   python -c "
   from app.agents.tools import fallback_response
   from app.schemas.diagnostic import DiagnosticRequest
   payload = DiagnosticRequest(company_name='Test', business_type='dental_clinic', employee_count=5,
       automation_goal='...', pain_points=['...'], current_tools=['WhatsApp'], preferred_contact='email')
   print(fallback_response(payload))
   "
   ```
3. One real call against the configured LLM provider (`curl -X POST .../diagnostics/proposal ...`) to see
   the actual generated content — but see the `debug-llm-proposal-failure` skill's point about Groq's daily
   token quota before doing this repeatedly; one or two calls to confirm the change, not a loop.

## Don't

- Don't change `method="json_mode"` handling or the retry logic in `automation_graph.py` while doing prompt
  work — that's a separate, deliberate mechanism (see `project-architect` agent notes), unrelated to prompt
  content.
- Don't remove the existing `AUTOMATIZACIONES BASADAS EN AGENTES` or `FASES DE IMPLEMENTACION` sections as
  part of an unrelated change — both are explicit product decisions, not leftover drafts.
