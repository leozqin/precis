from logging import getLogger
from typing import List, Mapping, Optional, Type
from abc import ABC, abstractmethod

from app.content.engine import ContentRetrievalEngine
from app.models import (
    ContentRetrievalHandler,
    EntryContent,
    Feed,
    FeedEntry,
    NotificationHandler,
    SummarizationHandler
)
from app.settings import GlobalSettings
from app.notification.engine import NotificationEngine
from app.summarization.engine import SummarizationEngine
from app.reading import ReadingMethodsMixIn


class StorageHandler(ABC, ReadingMethodsMixIn):

    logger = getLogger("uvicorn.error")

    handler_map = {
        **SummarizationEngine.handlers,
        **NotificationEngine.handlers,
        **ContentRetrievalEngine.handlers,
    }

    engine_map = {
        "summarization": SummarizationEngine,
        "notification": NotificationEngine,
        "content": ContentRetrievalEngine,
    }

    handler_type_map = {
        **{k: "summarization" for k in SummarizationEngine.handlers.keys()},
        **{k: "notification" for k in NotificationEngine.handlers.keys()},
        **{k: "content" for k in ContentRetrievalEngine.handlers.keys()},
    }

    def reconfigure_handler(self, id: str, config: Mapping):

        return self.engine_map[self.handler_type_map[id]](
            type=id, config=config
        ).get_handler()
    
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
        handler: Type[
            SummarizationHandler | NotificationHandler | ContentRetrievalHandler
        ],
    ) -> None:
        pass
    
    @abstractmethod
    def get_handlers(
        self,
    ) -> Mapping[
        str, Type[SummarizationHandler | NotificationHandler | ContentRetrievalHandler]
    ]:
        pass
    
    @abstractmethod
    def get_handler(
        self, id: str
    ) -> Type[SummarizationHandler | NotificationHandler | ContentRetrievalHandler]:
        pass

    @abstractmethod
    def get_settings(self) -> GlobalSettings:
        pass
    
    @abstractmethod
    def upsert_settings(self, settings: GlobalSettings) -> None:
        pass