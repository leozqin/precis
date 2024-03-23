from pydantic import BaseModel
from feedparser import parse, FeedParserDict
from typing import Type
from json import dumps
from hashlib import md5

class Feed(BaseModel):
    name: str
    category: str = "uncategorized"
    type: str = "rss"
    url: str

    @property
    def rss(self) -> Type[FeedParserDict]:
        return parse(self.url)

    @property
    def id(self) -> str:
        id = dumps([self.name, self.category, self.type, self.url])
        return md5(id.encode()).hexdigest()
    
class FeedEntry(BaseModel):
    title: str
    url: str
    published_at: int
    updated_at: int
    authors: list[str] = []
    preview: str = None

    @property
    def id(self) -> str:
        return md5(self.url.encode()).hexdigest()
    
class EntryContent(BaseModel):
    url: str
    content: str = None
    summary: str = None

    @property
    def id(self) -> str:
        return md5(self.url.encode()).hexdigest()