from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BusinessType(StrEnum):
    LAW_FIRM = "law_firm"
    DENTAL_CLINIC = "dental_clinic"
    NOTARY = "notary"
    GESTORIA = "gestoria"
    REAL_ESTATE = "real_estate"
    ECOMMERCE = "ecommerce"
    PROFESSIONAL_SERVICES = "professional_services"
    OTHER = "other"

    @property
    def label(self) -> str:
        return {
            self.LAW_FIRM: "Bufete de abogados",
            self.DENTAL_CLINIC: "Clinica dental",
            self.NOTARY: "Notaria",
            self.GESTORIA: "Gestoria / asesoria",
            self.REAL_ESTATE: "Inmobiliaria",
            self.ECOMMERCE: "Ecommerce",
            self.PROFESSIONAL_SERVICES: "Servicios profesionales",
            self.OTHER: "Otro negocio",
        }[self]


class DiagnosticRequest(BaseModel):
    company_name: str = Field(min_length=2, max_length=120)
    business_type: BusinessType
    employee_count: int = Field(ge=1, le=5000)
    automation_goal: str = Field(min_length=15, max_length=800)
    pain_points: list[str] = Field(min_length=1, max_length=5)
    current_tools: list[str] = Field(default_factory=list, max_length=8)
    preferred_contact: Literal["email", "phone", "whatsapp", "not_specified"] = "not_specified"

    @field_validator("company_name", "automation_goal")
    @classmethod
    def clean_text(cls, value: str) -> str:
        return " ".join(value.strip().split())

    @field_validator("pain_points", "current_tools")
    @classmethod
    def clean_list(cls, values: list[str]) -> list[str]:
        cleaned = [" ".join(value.strip().split()) for value in values if value.strip()]
        return cleaned


class FlowStep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    short_description: str
    step_type: Literal[
        "start",
        "input",
        "process",
        "automation",
        "validation",
        "communication",
        "decision",
        "reporting",
        "end",
    ]
    owner: Literal["client", "automation", "team", "system"]
    suggested_icon: str
    estimated_impact: str
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)


class AutomationOpportunity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    problema_detectado: str
    solucion_propuesta: str
    beneficio_operativo: str
    impacto_estimado: str
    dificultad: Literal["baja", "media", "alta"]
    tipo: Literal["quick_win", "medio_plazo", "avanzado"]


class RoiEstimate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    headline: str
    assumptions: list[str]
    benefits: list[str]


class DiagnosticResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_name: str
    business_type: BusinessType
    executive_summary: str
    recommended_automation: str
    automations: list[AutomationOpportunity]
    flow: list[FlowStep]
    roi: RoiEstimate
    implementation_phases: list[str]
    contact_cta: str
    disclaimer: str
    provider: str = "unknown"
