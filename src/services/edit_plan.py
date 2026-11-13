from src.state import State
from src.models import Plan


def edit_plan(state: State) -> dict:

    edited_plan = state.get("edited_plan")

    if not edited_plan:
        raise ValueError("Edited plan is missing.")

    if isinstance(edited_plan, dict):
        edited_plan = Plan.model_validate(edited_plan)

    return {
        "plan": edited_plan,
        "edited_plan": None,
    }