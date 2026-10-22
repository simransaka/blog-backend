from typing import List, Literal
from pydantic import BaseModel, Field

from src.models.task import Task


class Plan(BaseModel):
    blog_title: str
    audience: str = Field(..., description="For whom this blog is")
    tone: str = Field(
        default="informative",
        description="""
            Writing tone appropriate for the topic and target audience,
            e.g., informative, conversational, professional, persuasive, humorous,
            or storytelling."""
        )
    blog_kind: str = Field(
        default="explainer",
        description="""
            Type or format of blog appropriate for the topic,
            e.g., explainer, tutorial, how-to guide, news roundup, comparison, opinion,
            review, travel blog, lifestyle blog, personal story, or listicle.
            Choose the most suitable format for the given topic."""
        )
    constraints: List[str] = Field(default_factory=list)
    tasks: List[Task]