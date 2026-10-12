from __future__ import annotations

from typing import List

from src.state import State

import ollama
from langchain_community.tools.tavily_search import TavilySearchResults

from src.retrieval.tavily_search import _tavily_search
from src.models.evidence_pack import EvidencePack
from src.config import MODEL
from src.prompts.research import RESEARCH_SYSTEM


# research
def research_node(state: State) -> dict:
    print("on research node")

    queries = state.get("queries", []) or []
    MAX_RESULTS = 6

    raw_results: List[dict] = []

    for q in queries:
        raw_results.extend(_tavily_search(q, max_results=MAX_RESULTS))

    if not raw_results:
        return {"evidence": []}

    print("need to do tavily search")

    extractor = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": RESEARCH_SYSTEM},
            {"role": "user", "content": f"Raw Results:\n{raw_results}"},
        ],
        format=EvidencePack.model_json_schema(),
    )

    pack = EvidencePack.model_validate_json(extractor.message.content)

    deduplicate = {}
    for e in pack.evidence:
        if e.url:
            deduplicate[e.url] = e

    print("tavily search done")

    return {"evidence": list(deduplicate.values())}
