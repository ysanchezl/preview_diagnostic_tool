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

Si el LLM falla al generar la propuesta (tras reintentar), en vez del objeto anterior se devuelve:

```json
{
  "proposal_ok": false,
  "error_reason": "llm_failed"
}
```

## Otros endpoints

`GET /api/v1/diagnostics/business-types`

Lista los valores y etiquetas de `BusinessType`, para poblar el selector del formulario.

`POST /api/v1/diagnostics/enrich`

Dada la URL publica de un negocio, hace scraping de la web y usa el LLM para sugerir datos con los que precargar el formulario de diagnostico.

```json
{
  "website_url": "https://tuempresa.com",
  "allow_scraping": true
}
```

Devuelve `suggested_company_name`, `suggested_business_type` y `suggested_current_tools` (pensados para precargar el formulario directamente), ademas de `candidate_pain_points` y `candidate_objectives` (requieren aceptacion explicita del usuario antes de usarse, no se precargan solos). Si `scraped_ok` es `false`, `error_reason` indica el motivo (`timeout`, `robots_disallowed`, etc.).
