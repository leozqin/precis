from hashlib import md5
from typing import Type

from feedparser import FeedParserDict, parse
from markdown2 import markdown
from pydantic import BaseModel
from readabilipy import simple_json_from_html_string

from app.context import GlobalSettings


class Feed(BaseModel):
    name: str
    category: str = "uncategorized"
    type: str = "rss"
    url: str
    notify_destination: str = None
    notify: bool = True
    preview_only: bool = False
    refresh_enabled: bool = True

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
    unretrievable: bool = False
    banned: bool = False

    @property
    def id(self) -> str:
        return md5(self.url.encode()).hexdigest()


class RawContent(EntryContent):
    @staticmethod
    async def get_entry_html(url: str, settings: GlobalSettings) -> EntryContent:
        return await settings.content_retrieval_handler.get_content(url)

    @staticmethod
    def get_main_content(content: str) -> str:
        md = simple_json_from_html_string(html=content, use_readability=True)

        return md["plain_content"]

    @staticmethod
    def summarize(
        feed: Feed, entry: FeedEntry, mk: str, settings: GlobalSettings
    ) -> str:

        summary = settings.llm_handler.summarize(feed=feed, entry=entry, mk=mk)

        if summary:
            return markdown(summary)

    async def to_entry_content(self) -> EntryContent:
        main_content = self.get_main_content(self.content)
        if not self.banned or self.unretrievable:
            return EntryContent(
                url=self.url, content=main_content, summary=self.summarize(main_content)
            )
        else:
            return EntryContent(
                url=self.url, banned=self.banned, unretrievable=self.unretrievable
            )


class HealthCheck(BaseModel):

    status: str = "OK"
