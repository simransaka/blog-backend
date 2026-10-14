from __future__ import annotations

import ollama
import logging

from src.models import EvidenceItem
from src.config import MODEL
from src.prompts import WORKER_PROMPT
from src.config import WORKER_MAX_EVIDENCE

logger = logging.getLogger(__name__)


# worker - generate content for one blog section
def worker(payload: dict) -> dict:
    logger.info("Worker started")
    task = payload["task"]
    topic = payload["topic"]
    plan = payload["plan"]
    evidence = [EvidenceItem(**e) for e in payload.get("evidence", [])]
    mode = payload.get("mode", "closed_book")
    
    bullets_text = "\n- " + "\n- ".join(task.bullets)

    evidence_text = ""
    if evidence:
        evidence_text = "\n".join(
            f"- {e.title} | {e.url} | {e.published_at or 'date:unknown'} | {e.snippet or 'No snippet available'}".strip()
            for e in evidence[:WORKER_MAX_EVIDENCE]
        )
        
    logger.info(f"Task id: {task.id} being processed")

    response = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": WORKER_PROMPT},
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
    logger.info(f"For task id: {task.id}, section is ready")
    return {"sections": [(task.id, section_md)]}