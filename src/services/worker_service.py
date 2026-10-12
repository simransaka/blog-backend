from __future__ import annotations

import re
import tempfile
from pathlib import Path
from typing import List, Optional
from src.state import State
from langgraph.types import Send

import ollama
from langchain_community.tools.tavily_search import TavilySearchResults

from src.models.evidence_item import EvidenceItem
from src.config import MODEL
from src.prompts.worker import WORKER_SYSTEM



# worker - generate content for one blog section
def worker(payload: dict) -> dict:
    print("worker called...")
    task = payload["task"]
    topic = payload["topic"]
    plan = payload["plan"]
    evidence = [EvidenceItem(**e) for e in payload.get("evidence", [])]
    mode = payload.get("mode", "closed_book")

    blog_title = plan.blog_title
    bullets_text = "\n- " + "\n- ".join(task.bullets)

    evidence_text = ""
    if evidence:
        evidence_text = "\n".join(
            f"- {e.title} | {e.url} | {e.published_at or 'date:unknown'}".strip()
            for e in evidence[:20]
        )

    print("worker in process")

    response = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": WORKER_SYSTEM},
            {
                "role": "user",
                "content": f"Blog title: {plan.blog_title}\n"
                f"Audience: {plan.audience}\n"
                f"Tone: {plan.tone}\n"
                f"Blog kind: {plan.blog_kind}\n"
                f"Constraints: {plan.constraints}\n"
                f"Topic: {topic}\n"
                f"Mode: {mode}\n\n"
                f"Section title: {task.title}\n"
                f"Goal: {task.goal}\n"
                f"Target words: {task.target_words}\n"
                f"Tags: {task.tags}\n"
                f"requires_research: {task.requires_research}\n"
                f"requires_citations: {task.requires_citations}\n"
                f"requires_code: {task.requires_code}\n"
                f"Bullets:{bullets_text}\n\n"
                f"Evidence (ONLY use these URLs when citing):\n{evidence_text}\n",
            },
        ],
    )

    section_md = response.message.content.strip()
    print("sections ready...")
    return {"sections": [section_md]}