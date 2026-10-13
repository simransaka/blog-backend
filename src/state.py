import operator
from typing import TypedDict, List, Annotated, Optional, Literal

from src.models.plan import Plan
from src.models.evidence_item import EvidenceItem

class State(TypedDict):
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