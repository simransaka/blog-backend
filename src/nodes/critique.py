from __future__ import annotations

import ollama
import logging

from src.state import State
from src.config import MODEL
from src.prompts import CRITIQUE_PROMPT
from src.models import CritiqueResponse


logger = logging.getLogger(__name__)


def critique(state: State):
    logger.info("Critique called")

    revision_count = state.get("revision_count", 0) + 1
    sections = state.get("sections", {})

    if not sections:
        raise ValueError("Cannot critique empty sections.")

    sections = state.get("sections", [])
    draft_parts = []

    for task_id, section in sections:
        draft_parts.append(
            f"TASK_ID: {task_id}\n"
            f"VALUE: {section}"
        )
    draft = "\n\n".join(draft_parts)

    logger.info("Draft formed")
    
    response = ollama.chat(
                model=MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": CRITIQUE_PROMPT
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Plan: {state["plan"]}"
                            f"Evidence: {state.get("approved_evidence", [])}"
                            f"Draft: {draft}"
                            "Evaluate the whole draft and return structed critique object"
                        )           
                    }
                ],
                format=CritiqueResponse.model_json_schema(),
                options={"temperature": 0}
            )

    critique = CritiqueResponse.model_validate_json(
        response.message.content
    )

    logger.info(
        f"Critique score: {critique.score}\n"
        f"Sections to Revise: {critique.sections_to_revise}"
    )

    return {
        "critique": critique,
        "revision_count": revision_count
    }