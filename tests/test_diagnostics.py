from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


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
