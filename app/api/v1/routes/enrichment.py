import asyncio

from fastapi import APIRouter, HTTPException, Request

from app.agents.enrichment import extract_website_signals
from app.core.rate_limit import InMemoryThrottle
from app.schemas.enrichment import WebsiteEnrichmentRequest, WebsiteEnrichmentResponse
from app.services.scraper import ScrapingError, fetch_site_text

ENRICH_TOTAL_TIMEOUT = 25.0

router = APIRouter()

_enrichment_throttle = InMemoryThrottle(min_interval_seconds=5.0)


def _failed_response(source_url: str, reason: str) -> WebsiteEnrichmentResponse:
    return WebsiteEnrichmentResponse(
        suggested_company_name=None,
        suggested_business_type=None,
        suggested_current_tools=[],
        candidate_pain_points=[],
        candidate_objectives=None,
        confidence={},
        source_url=source_url,
        scraped_ok=False,
        error_reason=reason,
    )


@router.post("/enrich", response_model=WebsiteEnrichmentResponse)
async def enrich_from_website(
    payload: WebsiteEnrichmentRequest, request: Request
) -> WebsiteEnrichmentResponse:
    if not payload.allow_scraping:
        raise HTTPException(
            status_code=400,
            detail="allow_scraping debe ser true para analizar la web.",
        )

    client_key = request.client.host if request.client else "unknown"
    if not _enrichment_throttle.allow(client_key):
        raise HTTPException(
            status_code=429,
            detail="Demasiadas solicitudes de analisis. Intenta de nuevo en unos segundos.",
        )

    source_url = str(payload.website_url)

    async def _scrape_and_extract():
        scraped = await fetch_site_text(source_url)
        return await extract_website_signals(scraped.home_text, scraped.about_text)

    try:
        signals = await asyncio.wait_for(_scrape_and_extract(), timeout=ENRICH_TOTAL_TIMEOUT)
    except TimeoutError:
        return _failed_response(source_url, "timeout")
    except ScrapingError as exc:
        return _failed_response(source_url, exc.reason)
    except Exception:
        return _failed_response(source_url, "unexpected_error")

    return WebsiteEnrichmentResponse(
        suggested_company_name=signals.company_name,
        suggested_business_type=signals.business_type,
        suggested_current_tools=signals.detected_tools,
        candidate_pain_points=signals.candidate_pain_points,
        candidate_objectives=signals.candidate_objectives,
        confidence=signals.confidence,
        source_url=source_url,
        scraped_ok=True,
        error_reason=None,
    )
