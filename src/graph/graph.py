from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

from src.state import State
from src.config import ASSETS_DIR
from src.models import Plan

from src.config import (
    CRITIQUE_PASS_SCORE,
    MAX_REVISIONS,
    MAX_WEB_SEARCH_COUNT,
    MAX_RESEARCH_STEPS,
    MAX_FETCHES,
)

from src.nodes import (
    router_node,
    planner,
    worker,
    reducer,
    fanout,
    evaluator,
    orchestrator,
    submit_evidence,
    critique,
    human_review
)


graph = StateGraph(State)

checkpointer = InMemorySaver()


# --------------------------------------------------
# EDIT PLAN NODE
# --------------------------------------------------

def edit_plan_node(state: State) -> dict:
    edited_plan = state.get("edited_plan")

    if not edited_plan:
        raise ValueError("Edited plan was not provided.")

    if isinstance(edited_plan, dict):
        edited_plan = Plan.model_validate(edited_plan)

    return {
        "plan": edited_plan
    }


# --------------------------------------------------
# ROUTER
# --------------------------------------------------

def router_next(state: State) -> str:

    if state["needs_research"]:
        return "evaluator"

    return "planner"


# --------------------------------------------------
# EVALUATOR
# --------------------------------------------------

def evaluator_next(state: State) -> str:
    web_search_count = state.get("web_search_count", 0)
    if (
        state.get("evidence_sufficient", False)
        or state.get("research_stalled", False)
        or web_search_count >= MAX_WEB_SEARCH_COUNT
        or state.get("research_steps", 0) >= MAX_RESEARCH_STEPS
        or state.get("fetch_count", 0) >= MAX_FETCHES
    ):
        return "submit_evidence"

    return "orchestrator"


# --------------------------------------------------
# HUMAN REVIEW
# --------------------------------------------------

def human_review_next(state: State):

    review = state["human_review"]

    if review in ("reject", "rejected"):
        return "planner"

    if review == "edit":
        return "edit_plan"

    if review in ("approve", "approved"):
        return fanout(state)

    raise ValueError(
        f"Invalid human review decision: {review}"
    )


# --------------------------------------------------
# CRITIQUE
# --------------------------------------------------

def critique_next(state: State):

    critique_result = state["critique"]

    if (
        critique_result.score >= CRITIQUE_PASS_SCORE
        or state["revision_count"] >= MAX_REVISIONS
        or not critique_result.sections_to_revise
    ):
        return "reducer"

    return fanout(state)


# --------------------------------------------------
# NODES
# --------------------------------------------------

graph.add_node("router", router_node)

graph.add_node("orchestrator", orchestrator)
graph.add_node("evaluator", evaluator)
graph.add_node("submit_evidence", submit_evidence)

graph.add_node("planner", planner)
graph.add_node("human_review", human_review)
graph.add_node("edit_plan", edit_plan_node)

graph.add_node("worker", worker)
graph.add_node("critique", critique)
graph.add_node("reducer", reducer)


# --------------------------------------------------
# EDGES
# --------------------------------------------------

graph.add_edge(START, "router")


# Router -> Research or Planner
graph.add_conditional_edges(
    "router",
    router_next,
    {
        "evaluator": "evaluator",
        "planner": "planner"
    }
)


# Evaluator -> Orchestrator or Submit Evidence
graph.add_conditional_edges(
    "evaluator",
    evaluator_next,
    {
        "orchestrator": "orchestrator",
        "submit_evidence": "submit_evidence"
    }
)


# Research loop
graph.add_edge("orchestrator", "evaluator")


# Research completed -> Planner
graph.add_edge("submit_evidence", "planner")


# Planner -> Human Review
graph.add_edge("planner", "human_review")


# Human Review -> Planner / Edit Plan / Workers
graph.add_conditional_edges(
    "human_review",
    human_review_next,
    {
        "planner": "planner",
        "edit_plan": "edit_plan"
    }
)


# Edited Plan -> Workers
graph.add_conditional_edges(
    "edit_plan",
    fanout,
    ["worker"]
)


# Workers -> Critique
graph.add_edge("worker", "critique")


# Critique -> Workers or Reducer
graph.add_conditional_edges(
    "critique",
    critique_next,
    {
        "reducer": "reducer"
    }
)


# Reducer -> END
graph.add_edge("reducer", END)


# --------------------------------------------------
# COMPILE
# --------------------------------------------------

blog = graph.compile(
    checkpointer=checkpointer
)


# --------------------------------------------------
# SAVE GRAPH IMAGE
# --------------------------------------------------

png_data = blog.get_graph().draw_mermaid_png()

with open(ASSETS_DIR / "graph.png", "wb") as file:
    file.write(png_data)
