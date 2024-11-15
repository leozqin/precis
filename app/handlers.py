from abc import ABC, abstractmethod
from fnmatch import fnmatch
from os import environ
from typing import ClassVar

from pydantic import BaseModel

from app.constants import BANNED_GLOBS
from app.models import Feed, FeedEntry, RawContent


class HandlerBase(BaseModel, ABC):
    id: ClassVar[str] = "generic handler base"


class ContentRetrievalHandler(HandlerBase):
    id: ClassVar[str] = "generic_content_retrieval_handler"

    @abstractmethod
    async def get_html(self, url) -> str:
        pass

    async def get_content(self, entry: FeedEntry) -> RawContent:
        if await self.is_banned():
            return RawContent(url=entry.url, banned=True)

        try:
            html = self.get_html()
            if not html:
                return RawContent(url=entry.url, unretrievable=True)
            return RawContent(url=entry.url, content=html)
        except Exception:
            return RawContent(url=entry.url, unretrievable=True)

    @staticmethod
    async def is_banned(url) -> bool:
        return any(fnmatch(url, i) for i in BANNED_GLOBS)


class NotificationHandler(HandlerBase):
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


class LLMHandler(HandlerBase):
    id: ClassVar[str] = "generic_llm_handler"

    @abstractmethod
    def summarize(self, feed: Feed, entry: FeedEntry, mk: str):
        pass

    def get_summarization_prompt(self, mk: str):
        prompt = f"""
Summarize this article:

{mk}
"""
        return prompt

    @property
    def summarization_system_prompt(self):
        return """
Your goal is to write a brief but detailed summary of the text given to you.
Only output the summary without any headings or sections.
Provide the summary in markdown.
    """
