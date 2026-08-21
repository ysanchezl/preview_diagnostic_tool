# Future evolution: semantic retrieval for business profiles (RAG)

## Status

Not implemented. A first version of this existed in the codebase (Postgres + pgvector, a
`BusinessProfileRecord` table, a seed script) and was removed in full because it had no concrete objective
yet — the static `BUSINESS_PROFILES` dict (`app/prompts/business_profiles.py`) already covers every
supported `BusinessType`, so exact-match lookup by enum value has no need for retrieval. This document is
just a record of the idea in case it becomes worth doing later, not a spec to implement as-is.

## What existed before removal

- `app/db/` — SQLAlchemy async engine/session, a `BusinessProfileRecord` model with a `pgvector` embedding
  column (`Vector(1536)`, matching OpenAI's `text-embedding-3-small`).
- `app/db/repository.py` — exact lookup by `business_type`, plus `search_similar_profiles` (cosine
  similarity over the embedding column) that was never actually called from the pipeline.
- `app/services/business_profile_service.py` — tried Postgres first, fell back to the static dict on any DB
  error, so Postgres was never a hard dependency.
- `scripts/seed_business_profiles.py` — loaded `BUSINESS_PROFILES` into Postgres, embedding each profile's
  markdown via `OpenAIEmbeddings` if `OPENAI_API_KEY` was set.
- `docker-compose.yml` — a local `pgvector/pgvector:pg16` container.

## When this would actually be worth reviving

Only once there's a real reason exact-match-by-enum isn't enough, for example:
- Business types stop being a small fixed enum (e.g. free-text or long-tail verticals), so you need
  nearest-neighbor matching against a bigger, less curated set of profiles instead of a `dict` key lookup.
- Profiles start being sourced/updated dynamically (e.g. per-client customization, ingesting real client
  data) rather than hand-written once by a person.
- The website-enrichment pipeline (`app/agents/enrichment.py`) needs to match a scraped site against
  *similar past businesses* rather than just classifying it into one of the fixed `BusinessType` values.

## Open decision if revived: embeddings provider

Not finalized before removal. Two options were on the table:
- OpenAI's `text-embedding-3-small` (paid API, 1536-dim) — what the removed code used.
- A self-hosted alternative, `BAAI/bge-m3` via `sentence-transformers` (1024-dim), in the separate
  `embedding_service` repo — not wired in.

If this is revived, decide the provider first since it determines the vector dimension in the schema.
