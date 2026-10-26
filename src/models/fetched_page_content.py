from pydantic import BaseModel


class FetchedPageContent(BaseModel):
    url: str
    content: str