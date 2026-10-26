from __future__ import annotations

from typing import List
from pydantic import ValidationError

import logging

from src.models import EvidencePack, EvidenceItem
from src.state import State


logger = logging.getLogger(__name__)



def submit_evidence(state: State) -> dict:
    """Validate and submit the collected research evidence."""

    items = state.get("evidence", [])
    unique_items = {}

    logger.info(
            "Called: submit_evidence | Arguments: items_count=%d",
            len(items),
    )

    for item in items:
        url = item.url

        if not isinstance(url, str) or not url.strip():
            continue

        try:
            evidence = EvidenceItem.model_validate(item)
        except ValidationError:
            logger.warning("Invalid evidence item %s", url)
            continue

        if url not in unique_items:
            unique_items[url] = evidence

    pack = EvidencePack(
        evidence=list(unique_items.values())
    )

    logger.info(f"Evidence submission done. Unique sources: {len(pack.evidence)}")

    return {
        "approved_evidence": [
            item.model_dump()
            for item in pack.evidence
        ]
    }