import pytest
from fastapi.testclient import TestClient

import app.agents.automation_graph as automation_graph_module
from app.main import app

client = TestClient(app)

_VALID_PROPOSAL_PAYLOAD = {
    "company_name": "Clinica Sonrisa Norte",
    "business_type": "dental_clinic",
    "executive_summary": "Resumen ejecutivo de prueba.",
    "recommended_automation": "Automatizacion recomendada de prueba.",
    "automations": [
        {
            "problema_detectado": "Confirmacion manual de citas.",
            "solucion_propuesta": "Confirmacion automatica por WhatsApp.",
            "beneficio_operativo": "Menos tiempo en recepcion.",
            "impacto_estimado": "Alto impacto inicial.",
            "dificultad": "baja",
            "tipo": "quick_win",
        },
    ],
    "flow": [
        {
            "id": "step_1",
            "title": "Contacto",
            "short_description": "Recogemos el contexto.",
            "step_type": "start",
            "owner": "team",
            "inputs": ["Formulario"],
            "outputs": ["Mapa de necesidades"],
            "suggested_icon": "messages-square",
            "estimated_impact": "Alineacion inicial.",
        },
    ],
    "roi": {
        "headline": "Retorno aproximado.",
        "assumptions": ["Volumen mensual estable."],
        "benefits": ["Menos trabajo manual."],
    },
    "implementation_phases": ["Fase 1", "Fase 2", "Fase 3"],
    "contact_cta": "Contacta con nuestro equipo.",
    "disclaimer": "Propuesta preliminar y orientativa.",
    "provider": "llm",
}

_GROQ_TOOL_CALL_ERROR = Exception(
    "Error code: 400 - {'error': {'code': 'tool_use_failed', "
    "'message': \"Tool call validation failed: attempted to call tool 'json'\"}}"
)


class _FakeStructuredLLM:
    def __init__(self, outcomes: list) -> None:
        self._outcomes = list(outcomes)

    async def ainvoke(self, messages: list):
        outcome = self._outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


class _FakeLLM:
    def __init__(self, outcomes: list) -> None:
        self._structured = _FakeStructuredLLM(outcomes)

    def with_structured_output(self, schema, method=None):
        return self._structured


_DIAGNOSTIC_REQUEST_PAYLOAD = {
    "company_name": "Clinica Sonrisa Norte",
    "business_type": "dental_clinic",
    "employee_count": 12,
    "automation_goal": "Reducir llamadas y organizar citas, recordatorios y seguimientos.",
    "pain_points": ["Mucho tiempo confirmando citas"],
    "current_tools": ["Google Calendar", "WhatsApp"],
    "preferred_contact": "email",
}


def test_proposal_retries_with_json_mode_after_groq_tool_call_bug(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_llm = _FakeLLM([_GROQ_TOOL_CALL_ERROR, _VALID_PROPOSAL_PAYLOAD])
    monkeypatch.setattr(automation_graph_module, "get_chat_model", lambda: fake_llm)

    response = client.post("/api/v1/diagnostics/proposal", json=_DIAGNOSTIC_REQUEST_PAYLOAD)

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "llm"
    assert body["disclaimer"]


def test_proposal_returns_explicit_error_when_both_attempts_fail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_llm = _FakeLLM([_GROQ_TOOL_CALL_ERROR, ValueError("still missing required fields")])
    monkeypatch.setattr(automation_graph_module, "get_chat_model", lambda: fake_llm)

    response = client.post("/api/v1/diagnostics/proposal", json=_DIAGNOSTIC_REQUEST_PAYLOAD)

    assert response.status_code == 200
    body = response.json()
    assert body["proposal_ok"] is False
    assert body["error_reason"]


def test_proposal_returns_explicit_error_without_retry_on_unrelated_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_llm = _FakeLLM([ValueError("network hiccup, unrelated to the Groq tool-call bug")])
    monkeypatch.setattr(automation_graph_module, "get_chat_model", lambda: fake_llm)

    response = client.post("/api/v1/diagnostics/proposal", json=_DIAGNOSTIC_REQUEST_PAYLOAD)

    assert response.status_code == 200
    body = response.json()
    assert body["proposal_ok"] is False


def test_create_proposal_with_mock_provider() -> None:
    response = client.post(
        "/api/v1/diagnostics/proposal",
        json={
            "company_name": "Clinica Sonrisa Norte",
            "business_type": "dental_clinic",
            "employee_count": 12,
            "automation_goal": "Reducir llamadas y organizar citas, recordatorios y seguimientos.",
            "pain_points": [
                "Mucho tiempo confirmando citas",
                "Pacientes que no acuden",
            ],
            "current_tools": ["Google Calendar", "WhatsApp", "Excel"],
            "preferred_contact": "email",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["company_name"] == "Clinica Sonrisa Norte"
    assert body["business_type"] == "dental_clinic"
    assert len(body["flow"]) >= 5
    assert body["disclaimer"]
