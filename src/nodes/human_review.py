import logging

from langgraph.types import interrupt
from src.state import State
from src.models import Plan

logger = logging.getLogger(__name__)


def human_review(state: State) -> dict:
    logger.info("Human review started")

    plan = state["plan"]

    decision = interrupt(
        {
            "message": "Review the blog plan before writing starts.",
            "plan": plan.model_dump()
            if hasattr(plan, "model_dump")
            else plan
        }
    )

    if decision.get("review") == "approve":
        logger.info("Plan approved by human")
        return {"human_review": "approved"}

    if decision.get("review") == "reject":
        logger.info("Plan rejected by human")
        return {"human_review": "rejected"}

    if decision.get("review") == "edit":
        logger.info("Human wants to edit the plan")
        return {"human_review": "edit"}

    raise ValueError(
        """Expected either "approve", "reject" or "edit" in the review as human decision"""
    )