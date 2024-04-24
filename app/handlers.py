from abc import ABC, abstractmethod
from os import environ
from typing import ClassVar

from pydantic import BaseModel

from app.models import Feed, FeedEntry


class HandlerBase(BaseModel, ABC):
    id: ClassVar[str] = "generic handler base"


class ContentRetrievalHandler(HandlerBase):
    id: ClassVar[str] = "generic_content_retrieval_handler"

    @abstractmethod
    async def get_content(self, url: str) -> str:
        pass


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


class SummarizationHandler(HandlerBase):
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
