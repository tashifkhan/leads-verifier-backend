from __future__ import annotations

from langgraph.graph import END, StateGraph

from .models import Lead, ProductOffer, ScoringState
from .scoring_logic import calculate_rule_score
from .llm_chain import build_ai_chain, parse_ai_response


def run_rule_engine_node(state: ScoringState) -> ScoringState:
    lead: Lead = state.get("lead")  # type: ignore
    offer: ProductOffer = state.get("offer")  # type: ignore
    rule_score = calculate_rule_score(lead, offer)
    return {**state, "rule_score": rule_score}


async def run_ai_intent_classification_node(state: ScoringState) -> ScoringState:
    try:
        chain = build_ai_chain()
        text = await chain.ainvoke(
            {
                "lead": state.get("lead"),  # type: ignore
                "offer": state.get("offer"),  # type: ignore
            }
        )
        intent, reasoning, points = parse_ai_response(text)
        return {
            **state,
            "ai_intent": intent,
            "ai_reasoning": reasoning,
            "ai_points": points,
        }
    except Exception as e:
        # In case of AI failure, degrade gracefully
        return {
            **state,
            "ai_intent": "Low",
            "ai_reasoning": f"AI error: {e}",
            "ai_points": 10,
            "error_message": str(e),
        }


def calculate_final_score_node(state: ScoringState) -> ScoringState:
    rule_score = int(state.get("rule_score", 0))
    ai_points = int(state.get("ai_points", 0))
    final_score = max(0, min(100, rule_score + ai_points))
    return {**state, "final_score": final_score}


workflow = StateGraph(ScoringState)
workflow.add_node("rule_engine", run_rule_engine_node)
workflow.add_node("ai_classification", run_ai_intent_classification_node)
workflow.add_node("final_score_calculation", calculate_final_score_node)

workflow.set_entry_point("rule_engine")
workflow.add_edge("rule_engine", "ai_classification")
workflow.add_edge("ai_classification", "final_score_calculation")
workflow.add_edge("final_score_calculation", END)

scoring_workflow = workflow.compile()
