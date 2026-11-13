from typing import Literal
from pydantic import BaseModel, Field

from src.models import Plan
from src.services import edit_plan


class Memory(BaseModel):
    plan: Plan
    status: Literal["Approved", "Rejected", "Edited"]
    edited_plan: edit_plan | None = None
    critique_score: float | None = Field(
        default=None,
        ge=0,
        le=10
    )