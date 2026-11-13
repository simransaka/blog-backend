
from langgraph.types import interrupt

from src.state import State


def human_review(state: State) -> dict:

    plan = state["plan"]

    if isinstance(plan, dict):
        plan_data = plan
    else:
        plan_data = plan.model_dump(mode="json")

    decision = interrupt({
        "message": "Please review the blog plan.",
        "plan": plan_data,
    })

    review = decision.get("review")

    if review == "approve":
        return {
            "human_review": "approved",
        }

    if review == "reject":
        return {
            "human_review": "rejected",
        }

    if review == "edit":

        edited_plan = decision.get("edited_plan")

        if not edited_plan:
            raise ValueError("Edited plan was not provided.")

        return {
            "human_review": "edit",
            "edited_plan": edited_plan,
        }

    raise ValueError(f"Invalid review decision: {review}")
