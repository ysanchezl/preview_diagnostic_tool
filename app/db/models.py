from pgvector.sqlalchemy import Vector
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

EMBEDDING_DIM = 1536


class Base(DeclarativeBase):
    pass


class BusinessProfileRecord(Base):
    __tablename__ = "business_profiles"

    business_type: Mapped[str] = mapped_column(String(64), primary_key=True)
    identity: Mapped[str] = mapped_column(String)
    business_context: Mapped[str] = mapped_column(String)
    common_pain_points: Mapped[list[str]] = mapped_column(ARRAY(String))
    automation_opportunities: Mapped[list[str]] = mapped_column(ARRAY(String))
    typical_tools: Mapped[list[str]] = mapped_column(ARRAY(String))
    kpis: Mapped[list[str]] = mapped_column(ARRAY(String))
    workflow_style: Mapped[str] = mapped_column(String)
    constraints: Mapped[list[str]] = mapped_column(ARRAY(String))
    tone: Mapped[str] = mapped_column(String)
    content_markdown: Mapped[str] = mapped_column(String)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM), nullable=True)
