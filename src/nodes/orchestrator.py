from __future__ import annotations

import ollama
import logging
import json

from src.state import State
from src.config import (
    MODEL,
    MAX_RESEARCH_STEPS,
    MAX_FETCHES
)
from src.tools import (
    fetch_page,
    web_search
)
from src.prompts import ORCHESTRATOR_PROMPT
from src.services import (
    search_result_validator,
    evidence_fact_checker
)
from src.models import FetchedPageContent, EvidenceItem


logger = logging.getLogger(__name__)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for relevant information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query.",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_page",
            "description": "Fetch and extract content from a webpage.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The webpage URL.",
                    }
                },
                "required": ["url"],
            },
        },
    },
]

TOOL_MAP = {
    "web_search": web_search,
    "fetch_page": fetch_page
}

def orchestrator(state: State):
    logger.info("Orchestrator started")

    messages=[
        {
            "role": "system",
            "content": ORCHESTRATOR_PROMPT
        },
        {
            "role": "user",
            "content": (
                f"Topic: {state['topic']}\n"
                f"Mode: {state['mode']}\n"
                f"Needs research: {state['needs_research']}"
            ),
        }
    ]

    research_steps = state.get("research_steps", 0)
    web_search_count = state.get("web_search_count", 0)
    fetch_count = state.get("fetch_count", 0)
    collected_evidence = list(state.get("evidence", []))
    collected_fetched_content = list(
    state.get("fetched_page_content", [])
    )

    while research_steps < MAX_RESEARCH_STEPS:
        response = ollama.chat(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            options={"temperature": 0}
        )

        assistant_message = response.message
        messages.append(assistant_message)

        if not assistant_message.tool_calls:
            break

        for call in assistant_message.tool_calls:
            if research_steps >= MAX_RESEARCH_STEPS:
                break

            name = call.function.name
            args = call.function.arguments or {}

            logger.info(f"Args: {args}")

            if name == "web_search" and web_search_count >=2:
                logger.info("Tavily search limit reached.")
                result = "Search limit reached. Use existing evidence"

            elif name == "fetch_page" and fetch_count >=MAX_FETCHES:
                logger.error("Page fetch limit reached.")
                result = "Page fetch limit reached."
            elif name not in TOOL_MAP:
                logger.error(f"Unknown tool: {name}")
                result = f"Unknown tool: {name}"
            else:
                try:
                    if name == "web_search":
                        web_search_count +=1
                        logger.info(f"Tavily search {web_search_count}")

                    elif name == "fetch_page":
                        fetch_count +=1
                        logger.info(f"Fetching web page count {fetch_count}")

                    research_steps +=1
                        

                    result = TOOL_MAP[name].invoke(args)

                    if name == "web_search":
                        valid_results = []

                        for item in result:
                            try:
                                evidence = (
                                    item
                                    if isinstance(item, EvidenceItem)
                                    else EvidenceItem.model_validate(item)
                                )

                                validated = search_result_validator(evidence)

                                if validated is not None:
                                    valid_results.append(validated)

                            except Exception:
                                logger.exception("Failed to validate search result")

                        collected_evidence.extend(valid_results)

                        # Ollama receives only the accepted results.
                        result = [
                            item.model_dump()
                            for item in valid_results
                        ]
                    elif name == "fetch_page":
                        valid_content = []

                        try:
                            content = (
                                result
                                if isinstance(result, FetchedPageContent)
                                else FetchedPageContent.model_validate(result)
                            )

                            checked_content = evidence_fact_checker(
                                content=content,
                                query=args.get("url", ""),
                                topic=state["topic"],
                            )

                            if checked_content is not None:
                                valid_content.append(checked_content)

                        except Exception:
                            logger.exception("Failed to validate or fact-check fetched page")

                        collected_fetched_content.extend(valid_content)

                        # Ollama receives only the accepted content.
                        result = [
                            item.model_dump()
                            for item in valid_content
                        ]
                except Exception as exc:
                    logger.exception("Tool execution failed: %s", name)
                    result = f"Tool error: {exc}"

            messages.append({
                "role": "tool",
                "tool_name": name,
                "content": (
                    result if isinstance(result, str)
                    else json.dumps(result, default=str)
                ),
            })

            
    return {
        "web_search_count": web_search_count,
        "evidence": collected_evidence,
        "research_steps": research_steps,
        "fetch_count": fetch_count,
        "fetched_page_content": collected_fetched_content,
    }
