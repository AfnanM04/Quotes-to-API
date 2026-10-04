from pydantic import BaseModel, Field

class Quote(BaseModel):
    id: str
    text: str
    author: str
    tags: list[str] = Field(default_factory=list)
    source_url: str

class QuoteList(BaseModel):
    items: list[Quote]
    page: int
    limit: int
    has_next: bool

class TagCount(BaseModel):
    tag: str
    count: int
