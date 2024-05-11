from hashlib import md5
from typing import Type

from feedparser import FeedParserDict, parse
from pydantic import BaseModel


class Feed(BaseModel):
    name: str
    category: str = "uncategorized"
    type: str = "rss"
    url: str
    notify_destination: str = None
    notify: bool = True
    preview_only: bool = False

    @property
    def rss(self) -> Type[FeedParserDict]:
        return parse(self.url)

    @property
    def id(self) -> str:
        return md5(self.url.encode()).hexdigest()

    def validate(self):
        return bool(self.rss.entries)


class FeedEntry(BaseModel):
    feed_id: str
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
