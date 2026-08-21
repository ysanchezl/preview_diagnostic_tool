import asyncio
from urllib.robotparser import RobotFileParser

import pytest
from fastapi.testclient import TestClient

import app.agents.enrichment as enrichment_module
from app.agents.enrichment import WebsiteSignals
from app.api.v1.routes import enrichment as enrichment_route
from app.main import app
from app.schemas.diagnostic import BusinessType
from app.services.scraper import ScrapedSite, ScrapingError, _is_allowed

client = TestClient(app)


async def _fake_fetch_ok(url: str) -> ScrapedSite:
    return ScrapedSite(
        home_text="Clinica Sonrisa Norte. Agenda tu cita online.",
        about_text=(
            "Somos una clinica dental con alta demanda de llamadas para confirmar citas y "
            "pacientes que no acuden a sus citas confirmadas. Usamos WhatsApp y Google "
            "Calendar para gestionar la agenda del equipo."
        ),
    )


async def _fake_extract_ok(home_text: str, about_text: str) -> WebsiteSignals:
    return WebsiteSignals(
        company_name="Clinica Sonrisa Norte",
        business_type=BusinessType.DENTAL_CLINIC,
        detected_tools=["WhatsApp", "Google Calendar"],
        candidate_pain_points=[
            "Alto volumen de llamadas para confirmar citas",
            "Pacientes que no acuden a sus citas",
        ],
        candidate_objectives=(
            "Automatizar la confirmacion de citas y el seguimiento de pacientes para reducir "
            "llamadas manuales y mejorar la asistencia."
        ),
        confidence={
            "company_name": "high",
            "business_type": "high",
            "detected_tools": "medium",
            "candidate_pain_points": "medium",
            "candidate_objectives": "medium",
        },
    )


async def _fake_fetch_timeout(url: str) -> ScrapedSite:
    raise ScrapingError("timeout")


async def _fake_fetch_robots_disallowed(url: str) -> ScrapedSite:
    raise ScrapingError("robots_disallowed")


async def _fake_fetch_no_about(url: str) -> ScrapedSite:
    return ScrapedSite(home_text="Bienvenido a nuestra web.", about_text="")


@pytest.fixture(autouse=True)
def _reset_throttle():
    enrichment_route._enrichment_throttle.reset()
    yield


def test_enrich_happy_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(enrichment_route, "fetch_site_text", _fake_fetch_ok)
    monkeypatch.setattr(enrichment_route, "extract_website_signals", _fake_extract_ok)

    response = client.post(
        "/api/v1/diagnostics/enrich",
        json={"website_url": "https://clinicasonrisanorte.example.com", "allow_scraping": True},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["scraped_ok"] is True
    assert body["suggested_company_name"] == "Clinica Sonrisa Norte"
    assert body["suggested_business_type"] == "dental_clinic"
    assert "WhatsApp" in body["suggested_current_tools"]
    assert len(body["candidate_pain_points"]) == 2
    assert body["candidate_objectives"]
    assert body["error_reason"] is None


def test_enrich_returns_no_candidates_without_about_content(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _fake_extract_no_candidates(home_text: str, about_text: str) -> WebsiteSignals:
        return WebsiteSignals(company_name="Generic Co", confidence={"company_name": "low"})

    monkeypatch.setattr(enrichment_route, "fetch_site_text", _fake_fetch_no_about)
    monkeypatch.setattr(enrichment_route, "extract_website_signals", _fake_extract_no_candidates)

    response = client.post(
        "/api/v1/diagnostics/enrich",
        json={"website_url": "https://sitio-sin-info.example.com", "allow_scraping": True},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["scraped_ok"] is True
    assert body["candidate_pain_points"] == []
    assert body["candidate_objectives"] is None


class _FakeStructuredLLM:
    def __init__(self) -> None:
        self.last_messages: list | None = None

    async def ainvoke(self, messages: list):
        self.last_messages = messages
        return WebsiteSignals()


class _FakeLLM:
    def __init__(self) -> None:
        self.structured = _FakeStructuredLLM()

    def with_structured_output(self, schema, method=None):
        return self.structured


def test_extract_website_signals_flags_insufficient_about_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_llm = _FakeLLM()
    monkeypatch.setattr(enrichment_module, "get_chat_model", lambda: fake_llm)

    asyncio.run(enrichment_module.extract_website_signals("Inicio de la web", "muy corto"))

    sent_content = fake_llm.structured.last_messages[1].content
    assert "vacio o insuficiente" in sent_content


def test_enrich_requires_allow_scraping() -> None:
    response = client.post(
        "/api/v1/diagnostics/enrich",
        json={"website_url": "https://clinicasonrisanorte.example.com", "allow_scraping": False},
    )

    assert response.status_code == 400


def test_enrich_handles_scraping_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(enrichment_route, "fetch_site_text", _fake_fetch_timeout)

    response = client.post(
        "/api/v1/diagnostics/enrich",
        json={"website_url": "https://sitio-caido.example.com", "allow_scraping": True},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["scraped_ok"] is False
    assert body["error_reason"] == "timeout"


def test_enrich_respects_robots_disallow(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(enrichment_route, "fetch_site_text", _fake_fetch_robots_disallowed)

    response = client.post(
        "/api/v1/diagnostics/enrich",
        json={"website_url": "https://no-scraping.example.com", "allow_scraping": True},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["scraped_ok"] is False
    assert body["error_reason"] == "robots_disallowed"


def test_is_allowed_respects_disallow_all() -> None:
    parser = RobotFileParser()
    parser.parse(["User-agent: *", "Disallow: /"])

    assert _is_allowed(parser, "https://example.com/") is False


def test_is_allowed_defaults_to_true_without_robots_txt() -> None:
    assert _is_allowed(None, "https://example.com/") is True
