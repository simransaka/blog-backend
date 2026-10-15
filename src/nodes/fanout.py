from __future__ import annotations

from src.state import State
from langgraph.types import Send
import logging

logger = logging.getLogger(__name__)


# intermediate function
def fanout(state: State):
    logger.info("Called Fanout")
    return [
        Send(
            "worker",
            {
                "task": task,
                "topic": state["topic"],
                "plan": state["plan"],
                "mode": state["mode"],
                "evidence": state.get("evidence", []),
            },
        )
        for task in state["plan"].tasks
    ]