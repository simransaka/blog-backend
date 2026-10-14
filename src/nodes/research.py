from __future__ import annotations

from typing import List

from src.state import State

import ollama
import logging

from src.services import tavily_search
from src.models import EvidencePack
from src.config import MAX_RESULTS, MODEL
from src.prompts import RESEARCH_PROMPT

logger = logging.getLogger(__name__)

# research
def research_node(state: State) -> dict:
    logger.info("Rsearching on the queries")

    queries = state.get("queries", []) or []

    logger.info(f"Queries: {queries}")

    raw_results: List[dict] = []

    for q in queries:
        raw_results.extend(
            tavily_search(q, max_results=MAX_RESULTS)
        )


    if not raw_results:
        return {"evidence": []}

    logger.info(f"Collected {len(raw_results)} raw results.")

    extractor = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": RESEARCH_PROMPT},
            {"role": "user", "content": f"Raw Results:\n{raw_results}"},
        ],
        options={"num_ctx": 8192},
        format=EvidencePack.model_json_schema(),
    )

    pack = EvidencePack.model_validate_json(extractor.message.content)

    deduplicate = {}
    for e in pack.evidence:
        if e.url:
            deduplicate[e.url] = e

    logger.info("Tavily search done")
    logger.info(f"Research completed. Unique sources: {len(deduplicate)}")

    return {"evidence": list(deduplicate.values())}
