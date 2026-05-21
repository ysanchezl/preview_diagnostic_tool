from langchain_core.tools import tool

from app.prompts.business_profiles import BUSINESS_PROFILES, BusinessProfile
from app.schemas.diagnostic import (
    AutomationOpportunity,
    BusinessType,
    DiagnosticRequest,
    DiagnosticResponse,
    FlowStep,
    RoiEstimate,
)


@tool
def get_business_profile(business_type: str) -> BusinessProfile:
    """Return sector-specific automation guidance for a supported business type."""
    try:
        business = BusinessType(business_type)
    except ValueError:
        business = BusinessType.OTHER
    return BUSINESS_PROFILES.get(business, BUSINESS_PROFILES[BusinessType.OTHER])


@tool
def build_default_flow(company_name: str, business_type: str) -> list[dict[str, object]]:
    """Build a visual end-to-end automation flow for frontend rendering."""
    return [
        {
            "id": "contact",
            "title": "Toma de contacto",
            "short_description": (
                f"Recogemos el contexto de {company_name} y los puntos de friccion "
                "principales."
            ),
            "step_type": "start",
            "owner": "team",
            "suggested_icon": "messages-square",
            "estimated_impact": "Alineacion inicial del alcance y prioridades.",
            "inputs": ["Respuestas del diagnostico", "Canal preferido"],
            "outputs": ["Mapa inicial de necesidades"],
        },
        {
            "id": "listen",
            "title": "Te escuchamos y entendemos",
            "short_description": (
                "Ordenamos objetivos, excepciones operativas y tareas repetitivas del equipo."
            ),
            "step_type": "input",
            "owner": "team",
            "suggested_icon": "ear",
            "estimated_impact": "Mejor entendimiento de cuellos de botella reales.",
            "inputs": ["Objetivos", "Pain points"],
            "outputs": ["Criterios de exito"],
        },
        {
            "id": "analysis",
            "title": "Analisis del caso",
            "short_description": (
                "Identificamos integraciones, datos necesarios, riesgos y quick wins."
            ),
            "step_type": "process",
            "owner": "automation",
            "suggested_icon": "workflow",
            "estimated_impact": "Priorizacion de oportunidades de alto impacto y baja complejidad.",
            "inputs": ["Herramientas actuales", "Volumen operativo"],
            "outputs": ["Diseno preliminar del flujo"],
        },
        {
            "id": "automation",
            "title": "Flujo automatizado",
            "short_description": (
                "Proponemos un circuito simple de captura, clasificacion, avisos y seguimiento."
            ),
            "step_type": "automation",
            "owner": "system",
            "suggested_icon": "bot",
            "estimated_impact": "Reduccion de tareas manuales y mejora del seguimiento.",
            "inputs": ["Solicitudes", "Documentos", "Eventos"],
            "outputs": ["Tareas creadas", "Notificaciones", "Registro actualizado"],
        },
        {
            "id": "proposal",
            "title": "Propuesta y ROI",
            "short_description": (
                "Aterrizamos alcance, fases, beneficios esperados y criterios para medir retorno."
            ),
            "step_type": "end",
            "owner": "team",
            "suggested_icon": "chart-no-axes-combined",
            "estimated_impact": "Claridad sobre beneficios, fases y siguiente paso comercial.",
            "inputs": ["Flujo validado", "Prioridades"],
            "outputs": ["Propuesta ajustable", "Siguiente paso comercial"],
        },
    ]


def fallback_response(payload: DiagnosticRequest) -> DiagnosticResponse:
    profile = BUSINESS_PROFILES[payload.business_type]
    opportunities = ", ".join(profile["automation_opportunities"][:3]).lower()
    automations = [
        AutomationOpportunity(
            problema_detectado=payload.pain_points[0],
            solucion_propuesta=profile["automation_opportunities"][0],
            beneficio_operativo="Reducir trabajo manual y ordenar el seguimiento operativo.",
            impacto_estimado="Alto impacto inicial con complejidad controlada.",
            dificultad="baja",
            tipo="quick_win",
        ),
        AutomationOpportunity(
            problema_detectado="Informacion y comunicaciones dispersas",
            solucion_propuesta=profile["automation_opportunities"][1],
            beneficio_operativo="Mejorar trazabilidad y velocidad de respuesta.",
            impacto_estimado="Impacto visible en coordinacion interna y atencion al cliente.",
            dificultad="media",
            tipo="medio_plazo",
        ),
        AutomationOpportunity(
            problema_detectado="Falta de indicadores claros para priorizar mejoras",
            solucion_propuesta="Panel basico de seguimiento operativo y KPIs",
            beneficio_operativo="Medir carga de trabajo, tiempos de respuesta y oportunidades.",
            impacto_estimado="Mejor toma de decisiones sin depender de revisiones manuales.",
            dificultad="media",
            tipo="medio_plazo",
        ),
    ]
    flow = [
        FlowStep.model_validate(step)
        for step in build_default_flow.invoke(
            {"company_name": payload.company_name, "business_type": payload.business_type.value}
        )
    ]
    return DiagnosticResponse(
        company_name=payload.company_name,
        business_type=payload.business_type,
        executive_summary=(
            f"{payload.company_name} puede empezar con una automatizacion sencilla enfocada en "
            "reducir tareas repetitivas, mejorar el seguimiento y dar mas visibilidad al equipo."
        ),
        recommended_automation=(
            f"Para {payload.business_type.label.lower()}, recomendamos un flujo inicial "
            f"que combine {opportunities}. El objetivo seria cubrir primero: "
            f"{payload.automation_goal}"
        ),
        automations=automations,
        flow=flow,
        roi=RoiEstimate(
            headline=(
                "El retorno esperado vendria de ahorrar tiempo operativo y reducir perdidas "
                "de seguimiento."
            ),
            assumptions=[
                (
                    "La estimacion final requiere conocer volumen mensual, herramientas "
                    "reales e integraciones."
                ),
                "Conviene empezar con un alcance pequeno y medir antes de ampliar.",
                f"Conviene medir KPIs como: {', '.join(profile['kpis'][:3]).lower()}.",
            ],
            benefits=[
                "Menos tareas manuales y duplicadas.",
                "Mejor trazabilidad de solicitudes y clientes.",
                "Seguimiento mas consistente por email, telefono o WhatsApp.",
                "Base clara para medir productividad y oportunidades de mejora.",
            ],
        ),
        implementation_phases=[
            "Diagnostico y definicion del flujo prioritario.",
            "Prototipo con automatizaciones esenciales e integraciones minimas.",
            "Validacion con el equipo, ajustes y medicion de beneficios.",
        ],
        contact_cta=(
            "Contacta con nuestro equipo para revisar tu caso, ajustar el alcance y preparar "
            "una estimacion alineada con presupuesto, herramientas y requerimientos del negocio."
        ),
        disclaimer=(
            "Esta propuesta es preliminar y orientativa. Para estimar presupuesto, plazos y ROI "
            "con precision necesitamos una toma de contacto y analisis detallado del caso."
        ),
        provider="mock",
    )
