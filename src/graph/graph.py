from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

from src.state import State
from src.config import ASSETS_DIR
from src.models import Plan
from src.services import edit_plan

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
    human_review
)

graph = StateGraph(State)
checkpointer = InMemorySaver()

# edit plan node
def edit_plan_node(state: State) -> dict:
    plan = state["plan"]

    if isinstance(plan, dict):
        plan = Plan.model_validate(plan)

    edited_plan = edit_plan(plan)

    return {"plan": edited_plan}


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

# human review decision

def human_review_next(state: State):
    review = state["human_review"]

    if review == "rejected":
        return "planner"

    if review == "edit":
        return "edit_plan"

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
graph.add_node("human_review", human_review)
graph.add_node("edit_plan", edit_plan_node)


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
graph.add_edge("planner", "human_review")
graph.add_conditional_edges(
    "human_review",
    human_review_next,
    {
        "planner": "planner",
        "edit_plan": "edit_plan",
    },
)
graph.add_conditional_edges("edit_plan", fanout, ["worker"])
graph.add_edge("worker", "critique")
graph.add_conditional_edges(
    "critique",
    critique_next,
    {
        "reducer": "reducer",
    },
)
graph.add_edge("reducer", END)


blog = graph.compile(checkpointer=checkpointer)

png_data = blog.get_graph().draw_mermaid_png()

with open(ASSETS_DIR / "graph.png", "wb") as file:
    file.write(png_data)