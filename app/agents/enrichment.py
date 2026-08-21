from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from app.llm.client import get_chat_model
from app.schemas.diagnostic import BusinessType

_BUSINESS_TYPE_VALUES = ", ".join(item.value for item in BusinessType)

MIN_ABOUT_TEXT_CHARS = 200

EXTRACTION_SYSTEM_PROMPT = f"""
Eres un analista que extrae senales de negocio a partir del texto visible de una pagina web.
Recibiras dos bloques de texto claramente etiquetados: CONTENIDO DE INICIO y CONTENIDO DE
SOBRE NOSOTROS / SERVICIOS.

IMPORTANTE: independientemente del idioma en el que este escrito el texto de la web (espanol,
ingles u otro), candidate_pain_points y candidate_objectives SIEMPRE deben redactarse en espanol
(traduce el sentido, no generes texto en ingles). company_name y detected_tools se mantienen tal
cual aparecen (son nombres propios, no se traducen).

Debes inferir:
- company_name: nombre del negocio si aparece claramente en el texto. Si no aparece, usa null.
- business_type: SOLO uno de estos valores exactos, sin inventar categorias nuevas:
  {_BUSINESS_TYPE_VALUES}
  Si no puedes inferirlo con confianza razonable, usa null.
- detected_tools: lista corta (maximo 8) de herramientas, software o plataformas mencionadas o
  claramente inferibles del texto (ej. WhatsApp, Google Calendar, Shopify).
- candidate_pain_points: entre 5 y 10 viñetas cortas con posibles puntos de dolor operativos,
  basadas UNICAMENTE en lo que el bloque de SOBRE NOSOTROS / SERVICIOS dice explicita o
  claramente implica sobre su forma de operar. Si ese bloque esta vacio o es demasiado corto
  para sustentar una inferencia razonable, devuelve una lista vacia. No generalices a partir
  del sector ni inventes problemas que el texto no respalda.
- candidate_objectives: un parrafo de MAXIMO 3 oraciones centrado en automatizacion de procesos,
  reduccion de costes y mejora de productividad, basado en los candidate_pain_points detectados.
  Si no hay candidate_pain_points, usa null.
- confidence: para cada una de las claves "company_name", "business_type", "detected_tools",
  "candidate_pain_points" y "candidate_objectives", indica "high", "medium" o "low" segun la
  certeza de la inferencia correspondiente.

No inventes datos que no esten respaldados por el texto. Ante la duda, usa confidence "low" y
deja el campo en null o en una lista vacia.

Responde SOLO con la estructura solicitada, en JSON.
""".strip()


class WebsiteSignals(BaseModel):
    company_name: str | None = None
    business_type: BusinessType | None = None
    detected_tools: list[str] = Field(default_factory=list, max_length=8)
    candidate_pain_points: list[str] = Field(default_factory=list, max_length=10)
    candidate_objectives: str | None = None
    confidence: dict[str, Literal["high", "medium", "low"]] = Field(default_factory=dict)


def _fallback_signals() -> WebsiteSignals:
    return WebsiteSignals(
        company_name=None,
        business_type=None,
        detected_tools=[],
        candidate_pain_points=[],
        candidate_objectives=None,
        confidence={
            "company_name": "low",
            "business_type": "low",
            "detected_tools": "low",
            "candidate_pain_points": "low",
            "candidate_objectives": "low",
        },
    )


async def extract_website_signals(home_text: str, about_text: str) -> WebsiteSignals:
    llm = get_chat_model()
    if llm is None:
        return _fallback_signals()

    # Sitios de una sola pagina no tienen /nosotros, /servicios, etc. como paginas propias;
    # en ese caso el contenido de inicio hace de "about" tambien.
    effective_about = about_text if len(about_text.strip()) >= MIN_ABOUT_TEXT_CHARS else home_text
    if len(effective_about.strip()) < MIN_ABOUT_TEXT_CHARS:
        about_note = "(vacio o insuficiente, no uses este bloque para inferir pain points)"
    else:
        about_note = effective_about

    structured_llm = llm.with_structured_output(WebsiteSignals, method="json_mode")
    response = await structured_llm.ainvoke(
        [
            SystemMessage(content=EXTRACTION_SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    f"CONTENIDO DE INICIO:\n{home_text}\n\n"
                    f"CONTENIDO DE SOBRE NOSOTROS / SERVICIOS:\n{about_note}"
                )
            ),
        ]
    )

    if isinstance(response, WebsiteSignals):
        return response
    return WebsiteSignals.model_validate(response)
