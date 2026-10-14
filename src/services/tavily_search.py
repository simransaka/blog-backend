from __future__ import annotations

from typing import List
import logging

from langchain_tavily import TavilySearch


tool = TavilySearch(max_results=5)

logger = logging.getLogger(__name__)


def tavily_search(query: str, max_results: int = 5) -> List[dict]:
    logger.info("Searching Tavily...")

    if max_results != 5:
        search_tool = TavilySearch(max_results=max_results)
    else:
        search_tool = tool

    results = search_tool.invoke({
        "query": query
    })

    if isinstance(results, dict) and "error" in results:
        logger.error("Tavily search failed: %s", results["error"])
        raise RuntimeError(f"Tavily search failed: {results['error']}")

    if isinstance(results, dict):
        results = results.get("results", [])

    print("Tavily response type:", type(results))
    print("Tavily response:", repr(results))

    normalized: List[dict] = []
    print("found results")

    for r in results or []:
        if not isinstance(r, dict):
            logger.warning("Skipping unexpected result type: %s", type(r).__name__)
            continue
        
        normalized.append(
            {
                "title": r.get("title") or "",
                "url": r.get("url") or "",
                "snippet": r.get("content") or r.get("snippet") or "",
                "published_at": r.get("published_date") or r.get("published_at"),
                "source": r.get("source"),
            }
        )
    logger.info("Tavily search completed: %d results", len(normalized))
    
    return normalized