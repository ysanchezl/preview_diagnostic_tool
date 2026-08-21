from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.schemas.diagnostic import BusinessType


class WebsiteEnrichmentRequest(BaseModel):
    website_url: HttpUrl
    allow_scraping: bool = False


class WebsiteEnrichmentResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    suggested_company_name: str | None = None
    suggested_business_type: BusinessType | None = None
    suggested_current_tools: list[str] = Field(default_factory=list, max_length=8)
    candidate_pain_points: list[str] = Field(default_factory=list, max_length=10)
    candidate_objectives: str | None = None
    confidence: dict[str, Literal["high", "medium", "low"]] = Field(default_factory=dict)
    source_url: str
    scraped_ok: bool
    error_reason: str | None = None
