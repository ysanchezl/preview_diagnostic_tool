from fastapi import APIRouter

from app.agents.automation_graph import run_automation_diagnostic
from app.schemas.diagnostic import (
    BusinessType,
    DiagnosticRequest,
    DiagnosticResponse,
    ProposalGenerationError,
)

router = APIRouter()


@router.post("/proposal", response_model=DiagnosticResponse | ProposalGenerationError)
async def create_proposal(
    payload: DiagnosticRequest,
) -> DiagnosticResponse | ProposalGenerationError:
    return await run_automation_diagnostic(payload)


@router.get("/business-types")
def list_business_types() -> list[dict[str, str]]:
    return [{"value": item.value, "label": item.label} for item in BusinessType]
