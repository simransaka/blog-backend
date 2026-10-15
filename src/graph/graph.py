from langgraph.graph import StateGraph, START, END

from src.state import State

from src.nodes import (
    router_node,
    planner,
    worker,
    reducer,
    fanout,
    research_node,
    evaluator_node,
    orchestrator_node,
    submit_evidence_node,
)

graph = StateGraph(State)


# router decision
def router_next(state: State) -> str:
    return "evaluator" if state["needs_research"] else "planner"

# evaluator decision
def evaluator_next(state: State) -> str:
    return "submit_evidence" if state["evidence_sufficient"] else "orchestrator"

# graph - nodes
graph.add_node("planner", planner)
graph.add_node("worker", worker)
graph.add_node("reducer", reducer)
# graph.add_node("research", research_node)
graph.add_node("router", router_node)
graph.add_node("orchestrator", orchestrator_node)
graph.add_node("evaluator", evaluator_node)
graph.add_node("submit_evidence", submit_evidence_node)



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
graph.add_edge("worker", "reducer")
graph.add_edge("reducer", END)


blog = graph.compile()

png_data = blog.get_graph().draw_mermaid_png()

with open("graph.png", "wb") as file:
    file.write(png_data)