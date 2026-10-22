from pydantic import BaseModel


class SectionFeedback(BaseModel):
    task_id: int
    reason: str