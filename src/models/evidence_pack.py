from typing import List
from pydantic import BaseModel, Field

from src.models.evidence_item import EvidenceItem

class EvidencePack(BaseModel):
    evidence: List[EvidenceItem] = Field(default_factory=list)