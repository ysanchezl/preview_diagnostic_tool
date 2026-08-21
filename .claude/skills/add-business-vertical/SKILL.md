---
name: add-business-vertical
description: Add a new supported business vertical (BusinessType) end-to-end across backend and frontend — enum, sector profile, and form dropdown, kept consistent so mock and LLM output stay thematically correct. Use when asked to support a new business type/vertical/sector.
---

# Add a new business vertical

This project's sector knowledge lives in one static dict (`BUSINESS_PROFILES`) that both the LLM
system prompt and the deterministic mock fallback read from — see the "Sector knowledge base" section
of the root `CLAUDE.md` before starting. There is no database step; everything here is source code.

## Steps

1. **`app/schemas/diagnostic.py`** — add a new member to the `BusinessType` `StrEnum`, with a `label`
   (the human-readable Spanish name used in prompts and the frontend dropdown).

2. **`app/prompts/business_profiles.py`** — add a matching entry to `BUSINESS_PROFILES` keyed by the new
   enum value. Fill in every field the `BusinessProfile` shape requires: `identity`, `business_context`,
   `common_pain_points`, `automation_opportunities`, `typical_tools`, `kpis`, `workflow_style`,
   `constraints`, `tone`. Write these the way the existing profiles are written (concrete, sector-specific,
   Spanish) — don't leave placeholders.
   - `automation_opportunities` needs **at least 2 items**: `app/agents/tools.py::fallback_response`
     indexes `profile["automation_opportunities"][0]` and `[1]` directly (plus a `[:3]` slice, which is
     safe with fewer), so 0 or 1 items will raise an `IndexError` in mock mode. Prefer 3+ anyway, since
     the LLM prompt path also benefits from more sector detail.

3. **`frontend-preview/app/page.tsx`** — add the new value/label pair to the `businessTypes` array so it
   shows up in the form's dropdown. Keep the label text identical to the backend's `BusinessType.label` for
   that enum member — they're not derived from each other, so a mismatch is silent.

4. **Verify**:
   - `pytest` (mock-provider path exercises `fallback_response`, which will now touch the new profile).
   - `ruff check .`
   - With the backend running (`LLM_PROVIDER=mock` in `.env`, or no provider configured), submit the form
     with the new business type from the frontend and confirm the proposal renders without error — this is
     the actual `IndexError`/`KeyError` tripwire from step 2, and it only surfaces at request time.

## Don't

- Don't add a Postgres/embeddings step — that layer was removed from this repo (see
  `docs/future-evolution/business-profile-rag.md`). `BUSINESS_PROFILES` is the single source of truth.
- Don't invent a new shape for the profile dict per-entry — every value in `BUSINESS_PROFILES` must satisfy
  the same `BusinessProfile` structure or `format_business_profile`/`fallback_response` will break for that
  entry specifically, not just at import time.
