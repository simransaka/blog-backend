import operator
from typing import TypedDict, List, Annotated, Optional

from src.models.plan import Plan
from src.models.evidence_item import EvidenceItem

class State(TypedDict):
    topic: str

    # will get from routing/research
    mode: str
    needs_research: bool
    queries: List[str]
    evidence: List[EvidenceItem]
    plan: Optional[Plan]

    # will get from worker
    sections: Annotated[List[str], operator.add]
    final: str