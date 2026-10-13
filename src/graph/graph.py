from langgraph.graph import StateGraph, START, END

from src import State

from src.router import (
    router_node,
    route_next
)
from src.services import (
    planner,
    worker,
    reducer,
    fanout
)
from src.retrieval import research_node


graph = StateGraph(State)


# graph - nodes
graph.add_node("planner", planner)
graph.add_node("worker", worker)
graph.add_node("reducer", reducer)
graph.add_node("research", research_node)
graph.add_node("router", router_node)


# graph - edges
graph.add_edge(START, "router")
graph.add_conditional_edges(
    "router", route_next, {"research": "research", "planner": "planner"}
)
graph.add_edge("research", "planner")
graph.add_conditional_edges("planner", fanout, ["worker"])
graph.add_edge("worker", "reducer")
graph.add_edge("reducer", END)


blog = graph.compile()