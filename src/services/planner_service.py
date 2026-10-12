from __future__ import annotations

from src.state import State
from langgraph.types import Send

import ollama

from src.models.plan import Plan
from src.config import MODEL
from src.prompts.planner import PLANNER_PROMPT


def planner(state: State) -> dict:
    print("called planner...")

    evidence = state.get("evidence", [])
    mode = state.get("mode", "closed_book")

    msg = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": PLANNER_PROMPT},
            {
                "role": "user",
                "content": f"Topic: {state['topic']}\n"
                f"Mode: {mode}\n\n"
                f"Evidence (ONLY use for fresh claims; may be empty):\n"
                f"{[e.model_dump() for e in evidence][:16]}",
            },
        ],
        format=Plan.model_json_schema(),
    )
    print("planner working...")
    plan = Plan.model_validate_json(msg.message.content)
    print("planner completed...")
    return {"plan": plan}


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