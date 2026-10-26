from langgraph.graph import StateGraph, START, END

from src.state import State
from src.config import ASSETS_DIR

from src.config import (
    CRITIQUE_PASS_SCORE,
    MAX_REVISIONS,
    MAX_WEB_SEARCH_COUNT
)

from src.nodes import (
    router_node,
    planner,
    worker,
    reducer,
    fanout,
    research_node,
    evaluator,
    orchestrator,
    submit_evidence,
    critique,
)

graph = StateGraph(State)


# router decision
def router_next(state: State) -> str:
    return "evaluator" if state["needs_research"] else "planner"

# evaluator decision
def evaluator_next(state: State) -> str:
    web_search_count = state.get("web_search_count", 0)

    if (
        web_search_count >= MAX_WEB_SEARCH_COUNT
        or state["evidence_sufficient"]
    ):
        return "submit_evidence"
    
    return "orchestrator"

# critique decision
def critique_next(state: State):
    critique_result = state["critique"]

    if (
        critique_result.score >= CRITIQUE_PASS_SCORE
        or state["revision_count"] >= MAX_REVISIONS
        or not critique_result.sections_to_revise
    ):
        return "reducer"

    return fanout(state)


# graph - nodes
graph.add_node("planner", planner)
graph.add_node("worker", worker)
graph.add_node("reducer", reducer)
# graph.add_node("research", research_node)
graph.add_node("router", router_node)
graph.add_node("orchestrator", orchestrator)
graph.add_node("evaluator", evaluator)
graph.add_node("submit_evidence", submit_evidence)
graph.add_node("critique", critique)



# graph - edges
graph.add_edge(START, "router")
graph.add_conditional_edges(
    "router", router_next, {"evaluator": "evaluator", "planner": "planner"}
)
graph.add_conditional_edges(
    "evaluator", evaluator_next, {"submit_evidence": "submit_evidence", "orchestrator": "orchestrator"}
)
graph.add_edge("orchestrator", "evaluator")
graph.add_edge("submit_evidence", "planner")
graph.add_conditional_edges("planner", fanout, ["worker"])
graph.add_edge("worker", "critique")
graph.add_conditional_edges(
    "critique",
    critique_next,
    {
        "reducer": "reducer",
    },
)
graph.add_edge("reducer", END)


blog = graph.compile()

png_data = blog.get_graph().draw_mermaid_png()

with open(ASSETS_DIR / "graph.png", "wb") as file:
    file.write(png_data)