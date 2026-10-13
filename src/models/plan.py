from typing import List, Literal
from pydantic import BaseModel, Field

from src.models.task import Task


class Plan(BaseModel):
    blog_title: str
    audience: str = Field(..., description="For whom this blog is")
    tone: str = Field(..., description="Writing tone (e.g., practical, crisp)")
    blog_kind: Literal[
        "explainer", "tutorial", "news_roundup", "comparison", "system_design"
    ] = "explainer"
    constraints: List[str] = Field(default_factory=list)
    tasks: List[Task]