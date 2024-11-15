from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from logging import getLogger
from typing import Any, List, Mapping, Optional, Type

from pydantic import BaseModel, Field, validator

from app.content import content_retrieval_handlers
from app.handlers import (
    ContentRetrievalHandler,
    HandlerBase,
    LLMHandler,
    NotificationHandler,
)
from app.llm import llm_handlers
from app.models import *
from app.notification import notification_handlers


class Themes(str, Enum):
    black = "black"
    coffee = "coffee"
    dark = "dark"
    fantasy = "fantasy"
    forest = "forest"
    lemonade = "lemonade"
    lofi = "lofi"
    luxury = "luxury"
    night = "night"
    nord = "nord"
    pastel = "pastel"
    synthwave = "synthwave"
    winter = "winter"


class GlobalSettings(BaseModel):

    send_notification: bool = True
    theme: Themes = Themes.forest
    refresh_interval: int = 5
    reading_speed: int = 238

    notification_handler_key: str = "null_notification"
    llm_handler_key: str = "null_llm"
    content_retrieval_handler_key: str = "playwright"
    recent_hours: int = 36

    finished_onboarding: bool = False

    db: Any = Field(exclude=True)

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
    def llm_handler(self) -> LLMHandler:
        try:
            return self.db.get_handler(id=self.llm_handler_key)
        except IndexError:
            return self.db.handler_map[self.llm_handler_key]()

    @property
    def content_retrieval_handler(self) -> ContentRetrievalHandler:
        try:
            return self.db.get_handler(id=self.content_retrieval_handler_key)
        except IndexError:
            return self.db.handler_map[self.content_retrieval_handler_key]()


class StorageHandler(ABC):

    logger = getLogger("uvicorn.error")

    handler_map = {
        **llm_handlers,
        **notification_handlers,
        **content_retrieval_handlers,
    }

    engine_map = {
        "llm": llm_handlers,
        "notification": notification_handlers,
        "content": content_retrieval_handlers,
    }

    handler_type_map = {
        **{k: "llm" for k in llm_handlers.keys()},
        **{k: "notification" for k in notification_handlers.keys()},
        **{k: "content" for k in content_retrieval_handlers.keys()},
    }

    def reconfigure_handler(self, id: str, config: Mapping) -> Type[HandlerBase]:
        return self.handler_map[id](**config)

    @abstractmethod
    def clear_active_feeds(self) -> None:
        """
        Remove all feeds from the database
        """
        pass

    @abstractmethod
    def upsert_feed(self, feed: Feed) -> None:
        """
        Given a feed, update the feed if it already exists
        in the database, else create a new one.
        """
        pass

    @abstractmethod
    def insert_feed(self, feed: Feed) -> None:
        """
        Given a feed, insert it into the database, throwing an
        exception if it already exists
        """
        pass

    @abstractmethod
    def get_feed(self, id: str) -> Feed:
        """
        Given an ID, retrieve the Feed having that ID, throwing
        an exception if no Feed having that ID exists
        """
        pass

    @abstractmethod
    def get_feeds(self) -> List[Feed]:
        """
        Retrieve a list of all the active Feeds in the database
        """
        pass

    @abstractmethod
    def get_poll_state(self, feed: Feed) -> Optional[int]:
        """
        Given a feed, retrieve the poll state for that feed, if
        one exists
        """
        pass

    @abstractmethod
    def set_feed_start_ts(self, feed: Feed, start_ts: int) -> None:
        """
        Given a feed and a start ts, set the start ts for that feed
        """
        pass

    @abstractmethod
    def get_feed_start_ts(self, feed: Feed) -> int:
        """
        Given a feed, get the start ts for that feed
        """
        pass

    @abstractmethod
    def update_poll_state(self, feed: Feed, now: int) -> None:
        """
        Given a feed and the current time, update the poll state
        for that feed to the current time
        """
        pass

    @abstractmethod
    def upsert_feed_entry(self, feed: Feed, entry: FeedEntry) -> None:
        """
        Given a feed and a feed entry, update the feed entry to the
        given state, else create one if one does not exist
        """
        pass

    @abstractmethod
    def get_entries(
        self, feed: Feed = None, after: int = 0
    ) -> List[Mapping[str, FeedEntry]]:
        """
        Given a feed, retrieve the entries for that feed and return a list of
        dicts, where each dict has key entry = FeedEntry object, feed_id = the
        id of the feed for which the entry exists, and id = the entry ID. If no
        feed is specified return entries for all feeds. Optionally, only return
        entries after a certain epoch timestamp.
        """
        pass

    @abstractmethod
    def get_feed_entry(self, id: str) -> FeedEntry:
        """
        Given an ID, retrieve the feed entry having that id.
        """
        pass

    @abstractmethod
    def feed_entry_exists(self, id: str) -> bool:
        """
        Given an ID, return True if a feed entry with that ID exists
        """
        pass

    @abstractmethod
    async def get_entry_content(
        self, entry: FeedEntry, redrive: bool = False
    ) -> EntryContent:
        """
        Given a feed entry, return the EntryContent object for that entry
        if one exists. If the redrive argument is true or if none exists,
        create a new one using the URL of the feed entry and add it to the
        database using upsert_entry_content. Use the get_main_content
        static method for the class to clean the content as needed. Use the
        summarize static method for the class to build the summary.
        """
        pass

    @abstractmethod
    async def upsert_entry_content(self, content: EntryContent):
        """
        Given an EntryContent object, insert it into the database.
        """
        pass

    @abstractmethod
    def entry_content_exists(self, entry: FeedEntry) -> bool:
        """
        Return true if entry content exists for the FeedEntry else False
        """
        pass

    @abstractmethod
    def retrieve_entry_content(self, entry: FeedEntry) -> EntryContent:
        """
        Retrieve the content for the feed entry from storage
        """
        pass

    @abstractmethod
    def upsert_handler(
        self,
        handler: Type[HandlerBase],
    ) -> None:
        """
        Given a handler object, update that object in the database if it exists
        else insert a new one.
        """
        pass

    @abstractmethod
    def get_handlers(
        self,
    ) -> Mapping[str, Type[HandlerBase]]:
        """
        Return a mapping between the handler name and the handler object
        in the database, returning None for the handler if it doesn't exist.
        Enumerate handler IDs by using self.handler_map.keys()
        """
        pass

    @abstractmethod
    def get_handler(self, id: str) -> Type[HandlerBase]:
        """
        Given an ID, return the handler corresponding to that ID.
        """
        pass

    @abstractmethod
    def get_settings(self) -> GlobalSettings:
        """
        Retrive the global settings, if they exist. If not, instantiate
        a default global settings object and return that.
        """
        pass

    @abstractmethod
    def upsert_settings(self, settings: GlobalSettings) -> None:
        """
        Given a global settings object, use it to update the global settings in
        the database, or create one to match if it doesn't exist.
        """
        pass

    @abstractmethod
    def delete_feed(self, feed: Feed) -> None:
        """
        Given a feed, delete the feed from the database.
        """
        pass

    @abstractmethod
    def delete_feed_entry(self, feed_entry: FeedEntry) -> None:
        """
        Given a feed entry, delete the entry from the database.
        """
        pass

    async def get_content(self, entry: FeedEntry) -> EntryContent:

        raw_content = await self.get_settings().content_retrieval_handler.get_content(
            entry=entry
        )
        return await raw_content.to_entry_content()

    async def get_entry_content(
        self, entry: FeedEntry, redrive: bool = False
    ) -> EntryContent:

        if self.entry_content_exists(entry) and not redrive:
            return self.retrieve_entry_content(entry=entry)

        else:
            if redrive:
                self.logger.info(f"starting redrive for feed entry {entry.id}")

            entry_content = await self.get_content(entry=entry)
            await self.upsert_entry_content(entry_content)

            return entry_content
