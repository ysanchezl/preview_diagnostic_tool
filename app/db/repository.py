from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import BusinessProfileRecord
from app.prompts.business_profiles import BusinessProfile
from app.schemas.diagnostic import BusinessType


def _record_to_profile(record: BusinessProfileRecord) -> BusinessProfile:
    return BusinessProfile(
        identity=record.identity,
        business_context=record.business_context,
        common_pain_points=record.common_pain_points,
        automation_opportunities=record.automation_opportunities,
        typical_tools=record.typical_tools,
        kpis=record.kpis,
        workflow_style=record.workflow_style,
        constraints=record.constraints,
        tone=record.tone,
    )


async def get_business_profile_from_db(
    session: AsyncSession, business_type: BusinessType
) -> BusinessProfile | None:
    record = await session.get(BusinessProfileRecord, business_type.value)
    if record is None:
        return None
    return _record_to_profile(record)


async def search_similar_profiles(
    session: AsyncSession, embedding: list[float], limit: int = 3
) -> list[tuple[BusinessProfile, float]]:
    distance = BusinessProfileRecord.embedding.cosine_distance(embedding)
    stmt = (
        select(BusinessProfileRecord, distance.label("distance"))
        .where(BusinessProfileRecord.embedding.is_not(None))
        .order_by(distance)
        .limit(limit)
    )
    result = await session.execute(stmt)
    return [(_record_to_profile(record), dist) for record, dist in result.all()]
