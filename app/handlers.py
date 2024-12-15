from __future__ import annotations

from abc import ABC, abstractmethod
from fnmatch import fnmatch
from logging import getLogger
from os import environ
from typing import Callable, ClassVar

from markdown2 import markdown
from pydantic import BaseModel
from readabilipy import simple_json_from_html_string

from app.constants import BANNED_GLOBS
from app.models import EntryContent, Feed, FeedEntry

logger = getLogger("uvicorn.error")


class HandlerBase(BaseModel, ABC):
    id: ClassVar[str] = "generic handler base"


class ContentRetrievalHandler(HandlerBase):
    id: ClassVar[str] = "generic_content_retrieval_handler"

    @abstractmethod
    async def get_html(self, url, use_script: bool) -> str:
        pass

    async def get_content(
        self,
        entry: FeedEntry,
        feed: Feed,
        summarizer: Callable[[Feed, FeedEntry, str], str],
    ) -> EntryContent:
        if await self.is_banned(entry.url):
            logger.info(f"Found banned entry from url {entry.url}")
            return EntryContent(url=entry.url, banned=True)

        try:
            if not feed.retrieve_content:
                logger.info(
                    "Feed is configured to not retrieve content, using rss content"
                )
                html = entry.content
            else:
                html = await self.get_html(url=entry.url, use_script=feed.use_script)

            content = self.get_main_content(content=html)
            if not html or not content:
                return EntryContent(url=entry.url, unretrievable=True)
            else:
                summary = summarizer(feed=feed, entry=entry, mk=content)

                return EntryContent(
                    url=entry.url,
                    content=content,
                    summary=markdown(summary) if summary else None,
                    unretrievable=False if content else True,
                )

        except Exception as e:
            logger.warning(
                f"Encountered retrieval exception, returning unretrievable: {e}"
            )
            return EntryContent(url=entry.url, unretrievable=True)

    @staticmethod
    async def is_banned(url) -> bool:
        return any(fnmatch(url, i) for i in BANNED_GLOBS)

    @staticmethod
    def get_main_content(content: str) -> str:
        md = simple_json_from_html_string(html=content, use_readability=True)

        return md["plain_content"]


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
