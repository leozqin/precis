from logging import getLogger
from pathlib import Path
from typing import List, Mapping, Optional, Type

from tinydb import Query, TinyDB

from app.constants import DATA_DIR
from app.context import GlobalSettings, StorageHandler
from app.handlers import (
    ContentRetrievalHandler,
    NotificationHandler,
    SummarizationHandler,
)
from app.models import EntryContent, Feed, FeedEntry

logger = getLogger("uvicorn.error")


class TinyDBStorageHandler(StorageHandler):
    """
    Use this class to encapsulate DB interactions
    """

    db_path = Path(DATA_DIR, "db.json").resolve()
    db = TinyDB(db_path)

    def clear_active_feeds(self) -> None:
        self.db.drop_table("feeds")

    def insert_feed(self, feed: Feed):
        table = self.db.table("feeds")
        table.insert({"id": feed.id, "feed": feed.dict()})

    def get_feed(self, id: str) -> Feed:
        table = self.db.table("feeds")

        query = Query()
        feed = table.search(query.id == id)[0]["feed"]

        return Feed(**feed)

    def get_feeds(self) -> List[Feed]:
        table = self.db.table("feeds")

        return [Feed(**i["feed"]) for i in table.all()]

    def get_poll_state(self, feed: Feed) -> Optional[int]:
        table = self.db.table("poll")

        query = Query().id.matches(feed.id)

        results = table.search(query)

        if results:
            return results[0]["last_polled_at"]

    def set_feed_start_ts(self, feed: Feed, start_ts: int):
        table = self.db.table("feed_start")

        query = Query().id.matches(feed.id)
        table.upsert({"id": feed.id, "start_ts": start_ts}, cond=query)

    def get_feed_start_ts(self, feed: Feed) -> int:
        table = self.db.table("feed_start")

        query = Query().id.matches(feed.id)
        results = table.search(query)

        if results:
            return results[0]["start_ts"]

    def update_poll_state(self, feed: Feed, now: int):
        table = self.db.table("poll")

        query = Query().id.matches(feed.id)
        table.upsert({"id": feed.id, "last_polled_at": now}, cond=query)

    def upsert_feed(self, feed: Feed):
        table = self.db.table("feeds")

        row = {
            "id": feed.id,
            "feed": feed.dict(),
        }

        query = Query().id.matches(feed.id)
        table.upsert(row, cond=query)

    def upsert_feed_entry(self, feed: Feed, entry: FeedEntry):
        table = self.db.table("entries")

        row = {
            "id": entry.id,
            "feed_id": feed.id,
            "entry": entry.dict(),
        }

        query = Query().id.matches(entry.id)
        table.upsert(row, cond=query)

    def get_entries(self, feed: Feed = None, after: int = 0):
        table = self.db.table("entries")

        if feed:
            query = Query().feed_id.matches(feed.id)
            entries = table.search(query)
        else:
            entries = table.all()

        return [
            {"entry": FeedEntry(**i["entry"]), "feed_id": i["feed_id"], "id": i["id"]}
            for i in entries
            if i["entry"]["published_at"] > after
        ]

    def get_feed_entry(self, id: str):
        table = self.db.table("entries")

        query = Query().id.matches(id)
        entry = table.search(query)[0]

        return FeedEntry(**entry["entry"])

    def feed_entry_exists(self, id: str):
        table = self.db.table("entries")

        query = Query().id.matches(id)
        if table.search(query):
            return True
        else:
            return False

    async def get_entry_content(
        self, entry: FeedEntry, redrive: bool = False
    ) -> EntryContent:
        table = self.db.table("entry_contents")
        query = Query().id.matches(entry.id)

        existing = table.search(query)
        if existing and not redrive:
            return EntryContent(**existing[0]["entry_contents"])

        else:
            if redrive:
                self.logger.info(f"starting redrive for feed entry {entry.id}")

            settings = self.get_settings()

            raw_content = await self.get_entry_html(entry.url, settings=settings)
            content = self.get_main_content(content=raw_content)

            feed = self.get_feed(entry.feed_id)

            summary = self.summarize(
                feed=feed, entry=entry, mk=content, settings=settings
            )

            entry_content = EntryContent(
                url=entry.url,
                content=content,
                summary=summary if summary else None,
            )

            await self.upsert_entry_content(content=entry_content)

            return entry_content

    async def upsert_entry_content(self, content: EntryContent):
        table = self.db.table("entry_contents")
        query = Query().id.matches(content.id)

        table.upsert(
            {"id": content.id, "entry_contents": content.dict()},
            cond=query,
        )

    def upsert_handler(
        self,
        handler: Type[
            SummarizationHandler | NotificationHandler | ContentRetrievalHandler
        ],
    ) -> None:
        table = self.db.table("handler")

        row = {
            "id": handler.id,
            "handler": handler.dict(),
        }

        query = Query().id.matches(handler.id)
        table.upsert(row, cond=query)

    def _make_handler_obj(self, id: str, config: Mapping):

        return self.handler_map[id](**config)

    def get_handlers(
        self,
    ) -> Mapping[
        str, Type[SummarizationHandler | NotificationHandler | ContentRetrievalHandler]
    ]:
        table = self.db.table("handler")

        handlers = {i: None for i in self.handler_map.keys()}

        for cfg in table.all():
            handlers[cfg["id"]] = self._make_handler_obj(
                id=cfg["id"], config=cfg["handler"]
            )

        return handlers

    def get_handler(
        self, id: str
    ) -> Type[SummarizationHandler | NotificationHandler | ContentRetrievalHandler]:
        table = self.db.table("handler")
        logger.info(f"requested handler {id}")
        query = Query().id.matches(id)
        handler = table.search(query)[0]

        handler_obj = self._make_handler_obj(
            id=handler["id"], config=handler["handler"]
        )

        return handler_obj

    def get_settings(self) -> GlobalSettings:
        table = self.db.table("settings")
        GlobalSettings.update_forward_refs()

        try:
            settings = table.all()[0]
            return GlobalSettings(db=self, **settings["settings"])
        except IndexError:
            return GlobalSettings(db=self)

    def upsert_settings(self, settings: GlobalSettings) -> None:
        table = self.db.table("settings")

        row = {
            "id": "settings",
            "settings": settings.dict(exclude={"db"}),
        }

        query = Query().id.matches("settings")
        table.upsert(row, cond=query)

        self.upsert_handler(settings.notification_handler)
        self.upsert_handler(settings.summarization_handler)
        self.upsert_handler(settings.content_retrieval_handler)

    def delete_feed(self, feed: Feed) -> None:
        feeds = self.db.table("feeds")
        query = Query().id.matches(feed.id)
        feeds.remove(query)

        feed_start = self.db.table("feed_start")
        feed_start.remove(query)

        poll = self.db.table("poll")
        poll.remove(query)

    def delete_feed_entry(self, feed_entry: FeedEntry) -> None:
        entry_contents = self.db.table("entry_contents")
        query = Query().id.matches(feed_entry.id)
        entry_contents.remove(query)

        entries = self.db.table("entries")
        entries.remove(query)
