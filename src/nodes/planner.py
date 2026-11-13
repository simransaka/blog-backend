
from __future__ import annotations

import logging
import time

import ollama
from pydantic import ValidationError

from src.state import State
from src.models import Plan
from src.prompts import PLANNER_PROMPT
from src.config import PLANNER_MAX_EVIDENCE, MODEL

logger = logging.getLogger(__name__)

MAX_PLANNER_RETRIES = 3


def planner(state: State) -> dict:
    logger.info("Planner called")

    evidence = state.get("approved_evidence", [])
    mode = state.get("mode", "closed_book")

    user_prompt = (
        f"Topic: {state['topic']}\n"
        f"Mode: {mode}\n\n"
        f"Evidence (ONLY use for fresh claims; may be empty):\n"
        f"{evidence[:PLANNER_MAX_EVIDENCE]}"
    )

    messages = [
        {"role": "system", "content": PLANNER_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    last_error = None

    for attempt in range(1, MAX_PLANNER_RETRIES + 1):

        try:
            logger.info(
                "Planner generation attempt %d/%d",
                attempt,
                MAX_PLANNER_RETRIES,
            )

            msg = ollama.chat(
                model=MODEL,
                messages=messages,
                format=Plan.model_json_schema(),
                options={
                    "temperature": 0,
                },
            )

            content = msg.message.content

            # Check for empty response
            if not content or not content.strip():
                raise ValueError("Ollama returned an empty planner response")

            logger.debug("Planner raw output: %r", content)

            # Validate JSON using Pydantic
            plan = Plan.model_validate_json(content)

            logger.info("Planner planned the flow successfully")
            logger.info("Tasks are: %s", plan.tasks)
            logger.info("[STAGE] Blog structure generated")

            return {"plan": plan}

        except (ValidationError, ValueError) as exc:
            last_error = exc

            logger.warning(
                "Planner attempt %d failed: %s",
                attempt,
                exc,
            )

        except ollama.ResponseError as exc:
            last_error = exc

            logger.error(
                "Ollama response error on attempt %d: %s",
                attempt,
                exc,
            )

        except Exception as exc:
            logger.exception(
                "Unexpected planner error on attempt %d",
                attempt,
            )
            raise

        if attempt < MAX_PLANNER_RETRIES:
            time.sleep(2)

    logger.error(
        "Planner failed after %d attempts. Last error: %s",
        MAX_PLANNER_RETRIES,
        last_error,
    )

    raise RuntimeError(
        f"Planner could not generate a valid plan after "
        f"{MAX_PLANNER_RETRIES} attempts: {last_error}"
    ) from last_error