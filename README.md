# Preview Diagnostic Tool Backend

Backend en FastAPI para generar una propuesta preliminar de automatizacion a partir de una smart card de diagnostico.

## Arranque

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

## Variables

Copia `.env.example` a `.env`. Si no configuras proveedor LLM, el servicio responde con una propuesta determinista de fallback para desarrollo.

## Endpoint principal

`POST /api/v1/diagnostics/proposal`

```json
{
  "company_name": "Clínica Sonrisa Norte",
  "business_type": "dental_clinic",
  "employee_count": 12,
  "automation_goal": "Reducir llamadas y organizar citas, recordatorios y seguimientos.",
  "pain_points": [
    "Mucho tiempo confirmando citas",
    "Pacientes que no acuden",
    "Informacion dispersa entre agenda, email y WhatsApp"
  ],
  "current_tools": ["Google Calendar", "WhatsApp", "Excel"],
  "preferred_contact": "email"
}
```
