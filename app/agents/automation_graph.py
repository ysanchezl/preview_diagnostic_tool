from typing import TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

from app.agents.tools import build_default_flow, fallback_response, get_business_profile
from app.llm.client import get_chat_model
from app.prompts.business_profiles import BusinessProfile
from app.prompts.system import BASE_SYSTEM_PROMPT, build_user_prompt
from app.schemas.diagnostic import DiagnosticRequest, DiagnosticResponse, FlowStep


class DiagnosticState(TypedDict):
    payload: DiagnosticRequest
    business_profile: BusinessProfile | dict[str, object]
    default_flow: list[dict[str, object]]
    proposal: DiagnosticResponse | None
    provider: str


def enrich_context(state: DiagnosticState) -> DiagnosticState:
    payload = state["payload"]
    state["business_profile"] = get_business_profile.invoke(payload.business_type.value)
    state["default_flow"] = build_default_flow.invoke(
        {"company_name": payload.company_name, "business_type": payload.business_type.value}
    )
    return state


async def generate_with_llm(state: DiagnosticState) -> DiagnosticState:
    payload = state["payload"]
    llm = get_chat_model()

    if llm is None:
        state["proposal"] = fallback_response(payload)
        state["provider"] = "mock"
        return state

    structured_llm = llm.with_structured_output(DiagnosticResponse)
    response = await structured_llm.ainvoke(
        [
            SystemMessage(content=BASE_SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    build_user_prompt(payload)
                    + "\n\nContexto generado por tools internas:\n"
                    + f"Perfil sectorial: {state['business_profile']}\n"
                    + f"Flujo visual base: {state['default_flow']}\n"
                )
            ),
        ]
    )

    if isinstance(response, DiagnosticResponse):
        proposal = response
    else:
        proposal = DiagnosticResponse.model_validate(response)

    proposal.provider = "llm"
    if not proposal.flow:
        proposal.flow = [FlowStep.model_validate(step) for step in state["default_flow"]]
    state["proposal"] = proposal
    state["provider"] = "llm"
    return state


def build_graph():
    graph = StateGraph(DiagnosticState)
    graph.add_node("enrich_context", enrich_context)
    graph.add_node("generate_proposal", generate_with_llm)
    graph.add_edge(START, "enrich_context")
    graph.add_edge("enrich_context", "generate_proposal")
    graph.add_edge("generate_proposal", END)
    return graph.compile()


automation_diagnostic_graph = build_graph()


async def run_automation_diagnostic(payload: DiagnosticRequest) -> DiagnosticResponse:
    result = await automation_diagnostic_graph.ainvoke(
        {
            "payload": payload,
            "business_profile": "",
            "default_flow": [],
            "proposal": None,
            "provider": "unknown",
        }
    )
    proposal = result["proposal"]
    if proposal is None:
        return fallback_response(payload)
    return proposal
