
from __future__ import annotations

from src.state import State
from langgraph.types import Send
import logging

logger = logging.getLogger(__name__)


def fanout(state: State):
    logger.info("Called Fanout")
    logger.info("[STAGE] Writing blog sections")

    critique_result = state.get("critique")

    if critique_result is not None:
        # Extract integer task IDs from SectionFeedback objects.
        task_ids = [
            feedback.task_id
            for feedback in critique_result.sections_to_revise
        ]

        tasks = [
            task
            for task in state["plan"].tasks
            if task.id in task_ids
        ]

        is_revision = True

    else:
        tasks = state["plan"].tasks
        is_revision = False

    logger.info(
        "Dispatching %d tasks: %s",
        len(tasks),
        [task.id for task in tasks]
    )

    return [
        Send(
            "worker",
            {
                "task": task,
                "task_id": task.id,
                "topic": state["topic"],
                "plan": state["plan"],
                "mode": state["mode"],
                "evidence": state.get("evidence", []),
                "is_revision": is_revision,
                "critique": critique_result,
            },
        )
        for task in tasks
    ]