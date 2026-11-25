from pydantic import BaseModel, model_validator
from typing import Literal


class BlogRequest(BaseModel):
    topic: str


class ReviewRequest(BaseModel):
    thread_id: str
    review: Literal["approve", "reject", "edit"]
    edited_plan: dict | None = None

    @model_validator(mode="after")
    def validate_review_data(self):
        if self.review == "edit" and self.edited_plan is None:
            raise ValueError(
                "edited_plan is required when review is 'edit'."
            )

        if self.review != "edit" and self.edited_plan is not None:
            raise ValueError(
                "edited_plan is only allowed when review is 'edit'."
            )

        return self