---
name: sync-schema-contract
description: Keep the backend Pydantic schemas (app/schemas/diagnostic.py, app/schemas/enrichment.py) and their hand-mirrored TypeScript types in frontend-preview/app/page.tsx in sync after a schema change. Use whenever a field is added/renamed/removed on DiagnosticRequest, DiagnosticResponse, FlowStep, AutomationOpportunity, RoiEstimate, or the enrichment response/request models.
---

# Sync the backend/frontend schema contract

There is no shared schema generation between backend and frontend in this repo — the frontend's
TypeScript interfaces in `frontend-preview/app/page.tsx` are manually hand-mirrored copies of the Pydantic
models in `app/schemas/diagnostic.py` (and `app/schemas/enrichment.py` for the website-enrichment feature).
A change on one side that isn't mirrored on the other fails silently or weirdly, not with a build error.

## Where each side lives

- Backend: `app/schemas/diagnostic.py` (`DiagnosticRequest`, `DiagnosticResponse`, `FlowStep`,
  `AutomationOpportunity`, `RoiEstimate`, `BusinessType`) and `app/schemas/enrichment.py`
  (`WebsiteEnrichmentRequest`/`WebsiteEnrichmentResponse`).
- Frontend: matching `interface`/`type` declarations near the top of `frontend-preview/app/page.tsx`
  (`DiagnosticResponse`, `FlowStep`, `AutomationOpportunity`, etc.) plus whatever local state/props consume
  them further down the same file.

## When changing a backend schema

1. Edit the Pydantic model. Remember `DiagnosticResponse` and its nested models use
   `model_config = ConfigDict(extra="forbid")` — they are the literal shape the LLM is constrained to
   produce via `with_structured_output(..., method="json_mode")` (`app/agents/automation_graph.py`). A new
   **required** field means the LLM must be told to produce it: update `BASE_SYSTEM_PROMPT`
   (`app/prompts/system.py`) or `build_user_prompt` with guidance, or give the field a sensible default so
   `extra="forbid"` doesn't reject otherwise-valid LLM output that omits it.
2. Update `app/agents/tools.py::fallback_response` (and `build_default_flow` if it's a `FlowStep` field) so
   the deterministic mock path also produces the new/changed field — mock and LLM output are meant to stay
   thematically and structurally consistent.
3. Mirror the change in the corresponding TypeScript type in `frontend-preview/app/page.tsx`, and update
   any rendering code that should display the new field.
4. If the field affects validation (e.g. a new required string, a length constraint), check
   `extractErrorMessage`/`friendlyValidationMessage` in `frontend-preview/app/page.tsx` — these translate
   backend Pydantic 422 errors into Spanish messages field-by-field, so a new validated field with no entry
   there will fall through to a generic message instead of a helpful one.
5. Verify: `pytest`, `ruff check .`, `npm run lint` (from `frontend-preview/`), and a manual round trip
   through the running app (submit the form, check the response renders) — schema drift here doesn't
   surface as a type error, it surfaces as a field being silently missing or `undefined` in the UI.

## Don't

- Don't change a field's meaning without checking `pain_points`' current cap (10 items, deliberately raised
  from 5 to match the enrichment flow's candidate suggestions) or similar tuned constraints — they're sized
  against a specific frontend flow, not arbitrary.
- Don't forget the enrichment schema (`app/schemas/enrichment.py`) has the same manual-mirroring problem for
  `suggested_*`/`candidate_*` fields — see the enrichment section of the root `CLAUDE.md` for the
  suggested-vs-candidate frontend contract before changing those.
