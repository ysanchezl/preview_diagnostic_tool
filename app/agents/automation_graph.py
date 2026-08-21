import logging
from typing import TypedDict

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

from app.agents.tools import build_default_flow, fallback_response, get_business_profile
from app.llm.client import get_chat_model
from app.prompts.business_profiles import BusinessProfile
from app.prompts.system import BASE_SYSTEM_PROMPT, build_user_prompt
from app.schemas.diagnostic import (
    DiagnosticRequest,
    DiagnosticResponse,
    FlowStep,
    ProposalGenerationError,
)

logger = logging.getLogger(__name__)

# Groq's tool-calling protocol occasionally fails on this schema's size with a
# request-level error (not a content problem, see CLAUDE.md gotcha) - detected by this
# substring so we know a json_mode retry might actually help, as opposed to other
# failures (rate limits, timeouts) where retrying immediately won't.
_GROQ_TOOL_CALL_BUG_MARKER = "tool_use_failed"


class DiagnosticState(TypedDict):
    payload: DiagnosticRequest
    business_profile: BusinessProfile | dict[str, object]
    default_flow: list[dict[str, object]]
    proposal: DiagnosticResponse | ProposalGenerationError | None
    provider: str


async def enrich_context(state: DiagnosticState) -> DiagnosticState:
    payload = state["payload"]
    state["business_profile"] = get_business_profile.invoke(payload.business_type.value)
    state["default_flow"] = build_default_flow.invoke(
        {"company_name": payload.company_name, "business_type": payload.business_type.value}
    )
    return state


async def _generate_proposal(
    llm, messages: list[BaseMessage], method: str | None
) -> DiagnosticResponse:
    kwargs = {"method": method} if method is not None else {}
    structured_llm = llm.with_structured_output(DiagnosticResponse, **kwargs)
    response = await structured_llm.ainvoke(messages)
    if isinstance(response, DiagnosticResponse):
        return response
    return DiagnosticResponse.model_validate(response)


async def generate_with_llm(state: DiagnosticState) -> DiagnosticState:
    payload = state["payload"]
    llm = get_chat_model()

    if llm is None:
        state["proposal"] = fallback_response(payload)
        state["provider"] = "mock"
        return state

    messages: list[BaseMessage] = [
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

    try:
        proposal = await _generate_proposal(llm, messages, method=None)
    except Exception as exc:
        if _GROQ_TOOL_CALL_BUG_MARKER not in str(exc):
            logger.warning("LLM structured output failed (non-retryable)", exc_info=True)
            state["proposal"] = ProposalGenerationError(error_reason="llm_failed")
            state["provider"] = "error"
            return state

        logger.warning(
            "Groq tool-call structured output failed, retrying with json_mode", exc_info=True
        )
        try:
            proposal = await _generate_proposal(llm, messages, method="json_mode")
        except Exception:
            logger.warning("json_mode retry also failed to produce a valid proposal", exc_info=True)
            state["proposal"] = ProposalGenerationError(error_reason="llm_failed")
            state["provider"] = "error"
            return state

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


async def run_automation_diagnostic(
    payload: DiagnosticRequest,
) -> DiagnosticResponse | ProposalGenerationError:
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
