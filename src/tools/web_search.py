
from __future__ import annotations

from typing import List
import logging
import src.config
from langchain_core.tools import tool

from langchain_tavily import TavilySearch


tavily_tool = TavilySearch(max_results=5)

logger = logging.getLogger(__name__)

@tool
def web_search(query: str, max_results: int = 5) -> List[dict]:
    """
    Search the web for relevant information about a given topic.

    Args:
        query: A focused search query.
        max_results: Maximum number of search results to retrieve.

    Returns:
        A list of normalized search results containing titles, URLs,
        snippets, publication dates, and source information.
    """

    logger.info("Searching Tavily...")

    if max_results != 5:
        search_tool = TavilySearch(max_results=max_results)
    else:
        search_tool = tavily_tool

    results = []

    logger.info("Fetching results for query - %s", query)

    result = search_tool.invoke({
        "query": query
    })

    if not isinstance(result, dict):
        logger.warning(
            "Unexpected Tavily response type: %s",
            type(result).__name__
        )
        return []

    if result.get("error"):
        logger.error(
            "Tavily search failed: %s",
            result["error"]
        )
        raise RuntimeError(
            f"Tavily search failed: {result['error']}"
        )

    query_results = result.get("results", [])
    results.extend(query_results)

    logger.info(
        "Results fetched for query '%s': %d",
        query,
        len(query_results)
    )

    logger.info("Total raw results fetched: %d", len(results))

    normalized: List[dict] = []

    for r in results:
        if not isinstance(r, dict):
            logger.warning(
                "Skipping unexpected result type: %s",
                type(r).__name__
            )
            continue

        logger.info(
            "Tavily search result: title=%s, url=%s, snippet=%s, "
            "published_at=%s, source=%s",
            r.get("title") or "",
            r.get("url") or "",
            r.get("content") or r.get("snippet") or "",
            r.get("published_date") or r.get("published_at"),
            r.get("source"),
        )

        normalized.append(
            {
                "title": r.get("title") or "",
                "url": r.get("url") or "",
                "snippet": r.get("content") or r.get("snippet") or "",
                "published_at": (
                    r.get("published_date")
                    or r.get("published_at")
                ),
                "source": r.get("source"),
            }
        )

    logger.info(
        "Tavily search completed: %d normalized results",
        len(normalized)
    )

    return normalized