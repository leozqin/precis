from pydantic import BaseModel
from abc import ABC, abstractmethod
from feedparser import parse, FeedParserDict
from typing import Type, ClassVar
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


class NotificationHandler(ABC):

    async def login(self):
        pass

    async def logout(self):
        pass

    async def send_notification(self, feed: Feed, entry: FeedEntry):
        pass


class SummarizationHandler(BaseModel, ABC):
    supports_fallback_extractor: ClassVar[bool] = False

    @abstractmethod
    def summarize(self, feed: Feed, entry: FeedEntry, mk: str):
        pass

    def fallback_html_extractor(self, html: str):
        pass

    def get_prompt(self, mk: str):
        prompt = f"""
Summarize this article:

{mk}
"""
        return prompt

    @property
    def system_prompt(self):
        return """
Your goal is to write a brief but detailed summary of the text given to you.
Only output the summary without any additional text. Provide the summary in markdown.
    """
