from abc import ABC, abstractmethod
from enum import Enum
from hashlib import md5
from json import dumps
from os import environ
from typing import ClassVar, Type

from feedparser import FeedParserDict, parse
from pydantic import BaseModel

# Entity Models


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


# Handler Models


class NotificationHandler(BaseModel, ABC):
    id: ClassVar[str] = "generic_notification_handler"

    @staticmethod
    def make_read_link(entry: FeedEntry) -> str:
        base_url = environ["RSS_BASE_URL"]
        return f"{base_url}/read/{entry.id}"

    async def login(self):
        pass

    async def logout(self):
        pass

    @property
    def destinations(self):
        pass

    async def send_notification(self, feed: Feed, entry: FeedEntry):
        pass


class SummarizationHandler(BaseModel, ABC):
    id: ClassVar[str] = "generic_summarization_handler"

    @abstractmethod
    def summarize(self, feed: Feed, entry: FeedEntry, mk: str):
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


class ContentRetrievalHandler(BaseModel, ABC):
    id: ClassVar[str] = "generic_content_retrieval_handler"

    @abstractmethod
    async def get_content(self, url: str) -> str:
        pass


# Settings


class Themes(str, Enum):
    synthwave = "synthwave"
    forest = "forest"
    dark = "dark"
    night = "night"


class GlobalSettingsSchema(BaseModel):

    send_notification: bool = True
    theme: Themes = Themes.forest
    refresh_interval: int = 5

    notification_handler_key: str = "null"
    summarization_handler_key: str = "null"
    content_retrieval_handler_key: str = "playwright"

    finished_onboarding: bool = False
