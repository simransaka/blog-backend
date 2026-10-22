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

                    if isinstance(result, list):
                        collected_evidence.extend(result)
                    elif isinstance(result, dict):
                        collected_evidence.append(result)

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
    logger.info("Page content fetched")
            
    return {
        "web_search_count": web_search_count,
        "evidence": collected_evidence,
        "research_steps": research_steps,
        "fetch_count": fetch_count,
    }
