import json
import logging
import ollama

from src.config import MODEL, MAX_CHARACTERS, MAX_FETCHED_PAGES_COUNT
from src.models import EvidenceItem, FetchedPageContent
from src.prompts import EVALUATOR_PROMPT
from src.state import State

logger = logging.getLogger(__name__)


def evaluator(state: State) -> dict:
    """Evaluate whether the collected evidence is sufficient."""

    evidence = [
        item.model_dump() if isinstance(item, EvidenceItem) else item
        for item in state.get("evidence", [])[:10]
    ]
    fetched_content = [
        (
            item.model_dump()
            if isinstance(item, FetchedPageContent)
            else dict(item) if isinstance(item, dict) else item
        )
        for item in state.get("fetched_page_content", [])[
            :MAX_FETCHED_PAGES_COUNT
        ]
    ]
    for item in fetched_content:
        if isinstance(item, dict) and isinstance(item.get("content"), str):
            item["content"] = item["content"][:MAX_CHARACTERS]

    logger.info("Evaluation started")

    response = ollama.chat(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": EVALUATOR_PROMPT,
            },
            {
                "role": "user",
                "content": (
                    f"Topic: {state['topic']}\n"
                    f"Mode: {state.get('mode', 'open_book')}\n"
                    f"Evidence: {json.dumps(evidence, default=str)}\n"
                    "Fetched page content: "
                    f"{json.dumps(fetched_content, default=str)}"
                ),
            },
        ],
        format="json",
        options={
            "temperature": 0,
            "repeat_penalty": 1.1,
            "num_predict": 256,
        }
    )

    try:
        result = json.loads(response.message.content)
        if not isinstance(result, dict):
            raise ValueError("Evaluator response must be a JSON object")
        logger.info("Received Evaluation results")
    except (json.JSONDecodeError, TypeError, ValueError):
        logger.exception("Could not parse evaluator response")
        result = {
            "sufficient": False,
            "feedback": "Evaluation failed. Review the collected evidence.",
        }

    sufficient = result.get("sufficient") is True
    feedback = result.get("feedback", "")
    if not isinstance(feedback, str):
        feedback = str(feedback)

    logger.info("Evidence sufficient: %s", sufficient)

    return {
        "evidence_sufficient": sufficient,
        "evaluator_feedback": feedback
    }