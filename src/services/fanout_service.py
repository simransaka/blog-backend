from __future__ import annotations

from src.state import State
from langgraph.types import Send


# intermediate function
def fanout(state: State):
    print("fanout called...")
    return [
        Send(
            "worker",
            {
                "task": task,
                "topic": state["topic"],
                "plan": state["plan"],
                "mode": state["mode"],
                "evidence": [e.model_dump() for e in state.get("evidence", [])],
            },
        )
        for task in state["plan"].tasks
    ]