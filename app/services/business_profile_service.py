import logging

from app.agents.tools import get_business_profile
from app.db.repository import get_business_profile_from_db
from app.db.session import async_session_factory
from app.prompts.business_profiles import BusinessProfile
from app.schemas.diagnostic import BusinessType

logger = logging.getLogger(__name__)


async def get_business_profile_with_retrieval(business_type: BusinessType) -> BusinessProfile:
    """Retrieve the business profile from Postgres; fall back to the static profile on any
    DB error (unreachable DB, table not migrated yet, etc.) so the diagnostic pipeline never
    breaks because of infrastructure issues."""
    profile: BusinessProfile | None = None
    try:
        async with async_session_factory() as session:
            profile = await get_business_profile_from_db(session, business_type)
    except Exception:
        logger.warning(
            "Business profile DB retrieval failed, using static fallback", exc_info=True
        )

    if profile is not None:
        return profile
    return get_business_profile.invoke(business_type.value)
