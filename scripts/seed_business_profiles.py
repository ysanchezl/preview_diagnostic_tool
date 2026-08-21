"""Seed/refresh the business_profiles table in Postgres from BUSINESS_PROFILES.

Usage (from repo root, with the venv activated and Postgres running):
    python scripts/seed_business_profiles.py

If OPENAI_API_KEY is not set, profiles are still seeded but without embeddings
(semantic search will simply have nothing to match against until re-seeded with a key).
"""

import asyncio

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert

from app.core.config import settings
from app.db.models import Base, BusinessProfileRecord
from app.db.session import async_session_factory, engine
from app.prompts.business_profiles import BUSINESS_PROFILES
from app.prompts.system import format_business_profile


def _build_embeddings_client():
    if not settings.openai_api_key:
        return None
    from langchain_openai import OpenAIEmbeddings

    return OpenAIEmbeddings(api_key=settings.openai_api_key, model=settings.embedding_model)


async def seed() -> None:
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)

    embeddings_client = _build_embeddings_client()
    if embeddings_client is None:
        print("OPENAI_API_KEY no configurada: se sembraran los perfiles sin embeddings.")

    async with async_session_factory() as session:
        for business_type, profile in BUSINESS_PROFILES.items():
            markdown = format_business_profile(profile)
            embedding = embeddings_client.embed_query(markdown) if embeddings_client else None

            values = {
                "identity": profile["identity"],
                "business_context": profile["business_context"],
                "common_pain_points": profile["common_pain_points"],
                "automation_opportunities": profile["automation_opportunities"],
                "typical_tools": profile["typical_tools"],
                "kpis": profile["kpis"],
                "workflow_style": profile["workflow_style"],
                "constraints": profile["constraints"],
                "tone": profile["tone"],
                "content_markdown": markdown,
                "embedding": embedding,
            }
            stmt = insert(BusinessProfileRecord).values(
                business_type=business_type.value, **values
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=[BusinessProfileRecord.business_type], set_=values
            )
            await session.execute(stmt)
        await session.commit()

    print(f"Sembrados {len(BUSINESS_PROFILES)} perfiles de negocio en Postgres.")


if __name__ == "__main__":
    asyncio.run(seed())
