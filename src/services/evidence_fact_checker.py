from typing import List
import ollama
import logging

from src.state import State
from src.config import MODEL
from src.models import FetchedPageContent
from src.prompts import EVIDENCE_FACT_CHECKER_PROMPT


logger = logging.getLogger(__name__)


def evidence_fact_checker(
    content: FetchedPageContent,
    query: str,
    topic: str
) -> FetchedPageContent | None:
    """Check one newly fetched page and return it if accepted"""
    logger.info("Evidence fact checking started...")
    try:
        response = ollama.chat(
            model = MODEL,
            messages=[
                {
                    "role": "system",
                    "content": EVIDENCE_FACT_CHECKER_PROMPT
                },
                {
                    "role": "user",
                    "content": (
                        f"Topic: {topic}\n"
                        f"Query: {query}\n"
                        f"URL: {content.url}\n"
                        f"Fetched content:\n{content.content}"
                    ),
                },
            ],
            options={"temperature": 0},
        )

        result = response.message.content.strip().lower()

        logger.info(f"Evidence was based on the facts? {result}")

        if result == "true":
            return content
        else:
            logger.warning(
                f"""Rejected fetched content with url: 
                {content.url} and content: {content.content}"""
            )
    
    except Exception:
        logger.exception(
            "Error fact-checking page %s",
            content.url,
        )
        return None