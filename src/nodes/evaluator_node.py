import json
import logging
import ollama

from src.config import MODEL
from src.prompts import EVALUATOR_PROMPT
from src.state import State

logger = logging.getLogger(__name__)


def evaluator_node(state: State) -> dict:
    """Evaluate whether the collected evidence is sufficient."""

    evidence = state.get("evidence", [])[:10]

    logger.info("Evaluation started")

    response = ollama.chat(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": EVALUATOR_PROMPT
            },
            {
                "role": "user",
                "content": 
                f"Topic: {state['topic']}\n"
                f"Mode: {state["mode"]}\n"
                f"Evidence: {json.dumps(evidence, default=str)}"
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
        logger.info("Received Evaluation results")
    except (json.JSONDecodeError, TypeError) as ecx:
        logger.exception("Could not parse evaluator response")
        result = {
            "sufficient": False,
            "feedback": "Evaluation failed. Please evuluate the evidence again.",
        }

    sufficient = result.get("sufficient") is True
    feedback = result.get("feedback", "")

    logger.info("Evidence sufficient: %s", sufficient)

    return {
        "evidence_sufficient": sufficient,
        "evaluator_feedback": feedback
    }