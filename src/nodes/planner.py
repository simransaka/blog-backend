from __future__ import annotations

from src.state import State

import ollama
from pydantic import ValidationError

from src.models import Plan
from src.prompts import PLANNER_PROMPT
from src.config import (
    PLANNER_MAX_EVIDENCE,
    MAX_PLANNER_ATTEMPTS,
    MODEL
)


def planner(state: State) -> dict:
    print("called planner...")

    evidence = state.get("evidence", [])
    mode = state.get("mode", "closed_book")

    messages = [
        {"role": "system", "content": PLANNER_PROMPT},
        {
            "role": "user",
            "content": (
                f"Topic: {state['topic']}\n"
                f"Mode: {mode}\n\n"
                f"Evidence (ONLY use for fresh claims; may be empty):\n"
                f"{[e.model_dump() for e in evidence[:PLANNER_MAX_EVIDENCE]]}"
            ),
        },
    ]

    max_attempts = MAX_PLANNER_ATTEMPTS
    last_error = None

    for attempt in range(1, max_attempts + 1):
        msg = ollama.chat(
            model=MODEL,
            messages=messages,
            format=Plan.model_json_schema(),
        )

        print(f"Planner validation attempt {attempt}/{max_attempts}...")

        try:
            plan = Plan.model_validate_json(msg.message.content)
            print("planner completed...")
            return {"plan": plan}

        except ValidationError as exc:
            last_error = exc
            print(f"Planner output validation failed: {exc}")

            if attempt < max_attempts:
                messages = messages + [
                    {
                        "role": "assistant",
                        "content": msg.message.content,
                    },
                    {
                        "role": "user",
                        "content": (
                            "Your previous response failed validation. "
                            "Correct the JSON to satisfy the required Plan "
                            "schema and all constraints in the system prompt. "
                            "Return only the corrected JSON.\n\n"
                            f"Validation errors:\n{exc}"
                        ),
                    },
                ]

    raise ValueError(
        f"Planner failed to produce a valid Plan after {max_attempts} attempts."
    ) from last_error