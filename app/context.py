from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from logging import getLogger
from typing import Any, List, Mapping, Optional, Type

from html2text import HTML2Text
from markdown2 import markdown
from pydantic import BaseModel, validator
from readabilipy import simple_json_from_html_string
from readability import Document

from app.content import content_retrieval_handlers
from app.handlers import (
    ContentRetrievalHandler,
    HandlerBase,
    NotificationHandler,
    SummarizationHandler,
)
from app.models import *
from app.notification import notification_handlers
from app.summarization import summarization_handlers


class Themes(str, Enum):
    synthwave = "synthwave"
    forest = "forest"
    dark = "dark"
    night = "night"


class GlobalSettings(BaseModel):

    send_notification: bool = True
    theme: Themes = Themes.forest
    refresh_interval: int = 5

    notification_handler_key: str = "null_notification"
    summarization_handler_key: str = "null_summarization"
    content_retrieval_handler_key: str = "playwright"

    finished_onboarding: bool = False

    db: Any

    @validator("db")
    def validate_db(cls, val):
        if issubclass(type(val), StorageHandler):
            return val

        raise TypeError("Wrong type for db, must be subclass of StorageHandler")

    @property
    def notification_handler(self) -> NotificationHandler:
        try:
            return self.db.get_handler(id=self.notification_handler_key)
        except IndexError:
            return self.db.handler_map[self.notification_handler_key]()

    @property
    def summarization_handler(self) -> SummarizationHandler:
        try:
            return self.db.get_handler(id=self.summarization_handler_key)
        except IndexError:
            return self.db.handler_map[self.summarization_handler_key]()

    @property
    def content_retrieval_handler(self) -> ContentRetrievalHandler:
        try:
            return self.db.get_handler(id=self.content_retrieval_handler_key)
        except IndexError:
            return self.db.handler_map[self.content_retrieval_handler_key]()


class StorageHandler(ABC):

    logger = getLogger("uvicorn.error")

    handler_map = {
        **summarization_handlers,
        **notification_handlers,
        **content_retrieval_handlers,
    }

    engine_map = {
        "summarization": summarization_handlers,
        "notification": notification_handlers,
        "content": content_retrieval_handlers,
    }

    handler_type_map = {
        **{k: "summarization" for k in summarization_handlers.keys()},
        **{k: "notification" for k in notification_handlers.keys()},
        **{k: "content" for k in content_retrieval_handlers.keys()},
    }

    def reconfigure_handler(self, id: str, config: Mapping):
        return self.handler_map[id](**config)

    @abstractmethod
    def clear_active_feeds(self) -> None:
        pass

    @abstractmethod
    def upsert_feed(self, feed: Feed) -> None:
        pass

    @abstractmethod
    def insert_feed(self, feed: Feed) -> None:
        pass

    @abstractmethod
    def get_feed(self, id: str) -> Feed:
        pass

    @abstractmethod
    def get_feeds(self) -> List[Feed]:
        pass

    @abstractmethod
    def get_poll_state(self, feed: Feed) -> Optional[int]:
        pass

    @abstractmethod
    def set_feed_start_ts(self, feed: Feed, start_ts: int) -> None:
        pass

    @abstractmethod
    def get_feed_start_ts(self, feed: Feed) -> int:
        pass

    @abstractmethod
    def update_poll_state(self, feed: Feed, now: int) -> None:
        pass

    @abstractmethod
    def upsert_feed_entry(self, feed: Feed, entry: FeedEntry) -> None:
        pass

    @abstractmethod
    def get_entries(self, feed: Feed = None) -> Mapping[str, FeedEntry | str]:
        pass

    @abstractmethod
    def get_feed_entry(self, id: str) -> FeedEntry:
        pass

    @abstractmethod
    def feed_entry_exists(self, id: str) -> bool:
        pass

    @abstractmethod
    async def get_entry_content(
        self, entry: FeedEntry, redrive: bool = False
    ) -> EntryContent:
        pass

    @abstractmethod
    def upsert_handler(
        self,
        handler: Type[HandlerBase],
    ) -> None:
        pass

    @abstractmethod
    def get_handlers(
        self,
    ) -> Mapping[str, Type[HandlerBase]]:
        pass

    @abstractmethod
    def get_handler(self, id: str) -> Type[HandlerBase]:
        pass

    @abstractmethod
    def get_settings(self) -> GlobalSettings:
        pass

    @abstractmethod
    def upsert_settings(self, settings: GlobalSettings) -> None:
        pass

    @staticmethod
    async def get_entry_html(url: str, settings: GlobalSettings) -> str:
        return await settings.content_retrieval_handler.get_content(url)

    @staticmethod
    def get_main_content(content: str) -> str:
        md = simple_json_from_html_string(html=content)

        cleaned_document = Document(input=md["content"])

        converter = HTML2Text()
        converter.ignore_images = True
        converter.ignore_links = True

        return markdown(converter.handle(cleaned_document.summary(html_partial=True)))

    @staticmethod
    def summarize(
        feed: Feed, entry: FeedEntry, mk: str, settings: GlobalSettings
    ) -> str:

        summary = settings.summarization_handler.summarize(
            feed=feed, entry=entry, mk=mk
        )

        if summary:
            return markdown(summary)
