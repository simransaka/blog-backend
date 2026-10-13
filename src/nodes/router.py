from __future__ import annotations

from src.state import State

import ollama

from src.models import RouterDecision
from src.prompts import ROUTER_PROMPT
from src.config import MODEL



def router_node(state: State) -> dict:
    print("on router node")
    topic = state["topic"]
    decider = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": ROUTER_PROMPT},
            {"role": "user", "content": f"Topic: {topic}"},
        ],
        format=RouterDecision.model_json_schema(),
    )

    decision = RouterDecision.model_validate_json(decider.message.content)

    print("made a decision")
    print("it needs research?: ", decision.needs_research)

    return {
        "needs_research": decision.needs_research,
        "mode": decision.mode,
        "queries": decision.queries,
    }


# route decision
def route_next(state: State) -> str:
    return "research" if state["needs_research"] else "planner"