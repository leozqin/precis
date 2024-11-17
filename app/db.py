from __future__ import annotations

from abc import ABC, abstractmethod
from logging import getLogger
from typing import List, Mapping, Optional, Type

from app.handlers import HandlerBase
from app.models import *
from app.settings import GlobalSettings


class StorageHandler(ABC):

    logger = getLogger("uvicorn.error")

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

        feed = self.get_feed(entry.feed_id)
        self.logger.debug(f"Found feed {feed} for entry {entry}")
        settings = self.get_settings()
        summarizer = settings.llm_handler.summarize

        content = await settings.content_retrieval_handler.get_content(
            feed=feed, entry=entry, summarizer=summarizer
        )
        self.logger.debug(f"Received content {content}")

        return content

    async def get_entry_content(
        self, entry: FeedEntry, redrive: bool = False
    ) -> EntryContent:

        if self.entry_content_exists(entry) and not redrive:
            return self.retrieve_entry_content(entry=entry)

        else:
            if redrive:
                self.logger.info(f"starting redrive for feed entry {entry.id}")

            self.logger.debug(f"Getting content for entry {type(entry)}: {entry}")
            entry_content = await self.get_content(entry=entry)
            await self.upsert_entry_content(entry_content)

            return entry_content
