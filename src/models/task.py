from typing import List
from pydantic import BaseModel, Field


class Task(BaseModel):
    id: int
    title: str = Field(
        ...,
        description="Clear, engaging title appropriate for the section's content."
        )
    goal: str = Field(
        ...,
        description="""
            One sentence describing what the reader should learn, understand, feel,
            or be able to do after reading this section."""
    )
    bullets: List[str] = Field(
        ...,
        min_length=3,
        max_length=5,
        description="3-5 concrete, relevant, non-overlapping subpoints that collectively fulfill the section goal",
    )
    target_words: int = Field(
        ..., description="Target word count for this section (120-200)"
    )
    tags: List[str] = Field(default_factory=list)
    requires_research: bool = False
    requires_citations: bool = False
    requires_code: bool = False