import operator
from typing import TypedDict, List, Annotated, Optional, Literal
from langgraph.graph.message import add_messages

from src.models.plan import Plan
from src.models import (
    EvidenceItem,
    CritiqueResponse
)


class State(TypedDict):
    messages: Annotated[list, add_messages]

    topic: str

    # will get from routing/research
    mode: Literal["closed_book", "hybrid", "open_book"]
    needs_research: bool
    queries: List[str]
    evidence: List[EvidenceItem]
    plan: Optional[Plan]

    # will get from worker
    sections: Annotated[List[tuple[int, str]], operator.add]
    final: str

    # orchestrator and evaluator purposes
    evidence_sufficient: bool
    evaluator_feedback: str
    research_steps: int
    fetch_count: int
    web_search_count: int

    # submit_evidence result
    approved_evidence: list[dict]

    # critique
    revision_count: int
    critique: CritiqueResponse | None