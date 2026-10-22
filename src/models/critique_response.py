from pydantic import BaseModel, Field
from typing import List
from .section_feedback import SectionFeedback


class CritiqueResponse(BaseModel):
    score: float                       # 1-10
    sections_to_revise: List[SectionFeedback]   # task_id + reason
    unsupported_claims: List[str] = Field(
        default_factory=list
    )