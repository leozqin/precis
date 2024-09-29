from enum import Enum
from json import JSONDecodeError, dumps, loads
from logging import getLogger
from pathlib import Path
from typing import Any, List, Mapping, Type

from lmdb import Environment, Transaction
from pydantic import BaseModel

from app.constants import DATA_DIR
from app.context import GlobalSettings, StorageHandler
from app.handlers import HandlerBase
from app.models import EntryContent, Feed, FeedEntry, Type

logger = getLogger("uvicorn.error")


class Named(Enum):
    feed = "feed"
    poll = "poll"
    feed_start = "feed_start"
    entry = "entry"
    entry_content = "entry_content"
    handler = "handler"
    settings = "settings"

    # secondary indices
    si_feed_entry = "si_feed_entry"


class LMDBStorageHandler(StorageHandler):
    def __init__(self) -> None:
        super().__init__()

        db_path = Path(DATA_DIR)
        self.db = Environment(
            path=bytes(db_path.resolve()),
            map_size=1024 * 1024 * 1024 * 2,
            create=True,
            readonly=False,
            max_dbs=32,
        )

    @staticmethod
    def _deserialize(val: Any):

        str_val = bytes(val).decode()

        try:
            logger.debug(f"attempting json load of {str_val}")
            value = loads(bytes(val).decode())
            logger.debug(f"deserialized value: {value}")
        except JSONDecodeError:
            value = str_val

        return value

    @staticmethod
    def _serialize(val: Any):

        if isinstance(val, BaseModel):
            logger.debug("detected subclass of basemodel")
            val = val.json()

        if isinstance(val, (list, dict)):
            logger.debug("detected json-serializable")
            val = dumps(val)

        logger.debug(f"serializing value: {val}")
        value = str(val).encode()

        return value

    def _db(self, db: Named):

        return self.db.open_db(db.value.encode())

    def clear_active_feeds(self) -> None:

        db = self._db(Named.feed)
        with self.db.begin(write=True, db=db) as txn:
            txn.drop(delete=False)

    def upsert_feed(self, feed: Feed) -> None:

        db = self._db(Named.feed)
        with self.db.begin(write=True, db=db) as txn:
            txn.replace(self._serialize(feed.id), self._serialize(feed))

    def insert_feed(self, feed: Feed) -> None:

        with self.db.begin(write=True, db=self._db(Named.feed)) as txn:
            txn.put(self._serialize(feed.id), self._serialize(feed))

    def get_feed(self, id: str) -> Feed:
        with self.db.begin(db=self._db(Named.feed)) as txn:
            value = txn.get(self._serialize(id))

        return Feed(**self._deserialize(value))

    def get_feeds(self) -> List[Feed]:
        with self.db.begin(self._db(Named.feed)) as txn:

            cur = txn.cursor()
            feed_cfgs = list(cur.iternext())

        return [Feed(**self._deserialize(i[1])) for i in feed_cfgs]

    def get_poll_state(self, feed: Feed) -> int | None:

        with self.db.begin(db=self._db(Named.poll)) as txn:
            value = txn.get(self._serialize(feed.id))

        if value:
            return self._deserialize(value)

    def set_feed_start_ts(self, feed: Feed, start_ts: int) -> None:

        with self.db.begin(db=self._db(Named.feed_start), write=True) as txn:
            txn.replace(self._serialize(feed.id), self._serialize(start_ts))

    def get_feed_start_ts(self, feed: Feed) -> int:

        with self.db.begin(db=self._db(Named.feed_start)) as txn:
            value = txn.get(self._serialize(feed.id))

        return self._deserialize(value)

    def update_poll_state(self, feed: Feed, now: int) -> None:

        with self.db.begin(db=self._db(Named.poll), write=True) as txn:
            txn.replace(self._serialize(feed.id), self._serialize(now))

    def upsert_feed_entry(self, feed: Feed, entry: FeedEntry) -> None:

        with self.db.begin(db=self._db(Named.entry), write=True) as txn:
            txn.replace(self._serialize(entry.id), self._serialize(entry))

        with self.db.begin(db=self._db(Named.si_feed_entry), write=True) as txn:
            value = txn.get(self._serialize(feed.id))

            if value:
                entries = self._deserialize(value)
                entries.append(entry.id)
            else:
                entries = [entry.id]

            txn.replace(self._serialize(feed.id), self._serialize(entries))

    def get_entries(
        self, feed: Feed = None, after: int = 0
    ) -> Mapping[str, FeedEntry | str]:
        entries = []

        if feed:
            with self.db.begin(db=self._db(Named.si_feed_entry)) as txn:
                _entries = txn.get(self._serialize(feed.id))
                entry_ids = []
                if _entries:
                    entry_ids = self._deserialize(_entries)

                with self.db.begin(db=self._db(Named.entry)) as txn:
                    cur = txn.cursor()
                    entries = cur.getmulti([self._serialize(i) for i in entry_ids])
        else:
            with self.db.begin(db=self._db(Named.entry)) as txn:
                cur = txn.cursor()
                entries = list(cur.iternext())

        out = []
        for entry in entries if entries else []:
            k, v = entry
            feed_entry = FeedEntry(**self._deserialize(v))
            if feed_entry.published_at > after:
                out.append(
                    {
                        "entry": feed_entry,
                        "feed_id": feed_entry.feed_id,
                        "id": self._deserialize(k),
                    }
                )

        return out

    def get_feed_entry(self, id: str) -> FeedEntry:

        with self.db.begin(db=self._db(Named.entry)) as txn:
            entry = txn.get(self._serialize(id))

        return FeedEntry(**self._deserialize(entry))

    def feed_entry_exists(self, id: str) -> bool:

        with self.db.begin(db=self._db(Named.entry)) as txn:
            cur = txn.cursor()

            return cur.set_key(self._serialize(id))

    async def get_entry_content(
        self, entry: FeedEntry, redrive: bool = False
    ) -> EntryContent:

        with self.db.begin(db=self._db(Named.entry_content)) as txn:
            cur = txn.cursor()
            exists = cur.set_key(self._serialize(entry.id))

        if exists and not redrive:
            with self.db.begin(db=self._db(Named.entry_content)) as txn:
                content = txn.get(self._serialize(entry.id))
            return EntryContent(**self._deserialize(content))

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

            await self.upsert_entry_content(entry_content)

            return entry_content

    async def upsert_entry_content(self, content: EntryContent):

        with self.db.begin(db=self._db(Named.entry_content), write=True) as txn:
            txn.replace(
                self._serialize(content.id),
                self._serialize(content),
            )

    def upsert_handler(self, handler: type[HandlerBase]) -> None:

        with self.db.begin(self._db(Named.handler), write=True) as txn:

            txn.replace(
                self._serialize(handler.id),
                self._serialize(handler.json(exclude_none=True)),
            )

    def _make_handler_obj(self, id: str, config: Mapping):

        return self.handler_map[id](**config)

    def get_handlers(self) -> Mapping[str, HandlerBase]:

        with self.db.begin(self._db(Named.handler)) as txn:

            cur = txn.cursor()
            handler_cfgs = list(cur.iternext())

        handlers = {i: None for i in self.handler_map.keys()}

        for cfg in handler_cfgs:
            k, v = cfg
            key = k.decode()
            handlers[key] = self._make_handler_obj(id=key, config=self._deserialize(v))

        return handlers

    def get_handler(self, id: str) -> HandlerBase:

        with self.db.begin(db=self._db(Named.handler)) as txn:
            cfg = txn.get(self._serialize(id))

        if cfg:
            handler_obj = self._make_handler_obj(
                id=id, config=self._deserialize(cfg) if cfg else {}
            )

            return handler_obj
        else:
            raise IndexError

    def get_settings(self) -> GlobalSettings:

        with self.db.begin(db=self._db(Named.settings)) as txn:
            cfg = txn.get("settings".encode())

        if cfg:
            return GlobalSettings(db=self, **self._deserialize(cfg))
        else:
            return GlobalSettings(db=self)

    def upsert_settings(self, settings: GlobalSettings) -> None:

        with self.db.begin(db=self._db(Named.settings), write=True) as txn:
            txn.replace(
                "settings".encode(),
                self._serialize(settings.json(exclude={"db"}, exclude_none=True)),
            )

        self.upsert_handler(settings.notification_handler)
        self.upsert_handler(settings.summarization_handler)
        self.upsert_handler(settings.content_retrieval_handler)

    def delete_feed(self, feed: Feed) -> None:

        with self.db.begin(db=self._db(Named.feed), write=True) as txn:
            txn.delete(self._serialize(feed.id))

        with self.db.begin(db=self._db(Named.si_feed_entry), write=True) as txn:
            txn.delete(self._serialize(feed.id))

        with self.db.begin(db=self._db(Named.poll), write=True) as txn:
            txn.delete(self._serialize(feed.id))

        with self.db.begin(db=self._db(Named.feed_start), write=True) as txn:
            txn.delete(self._serialize(feed.id))

    def delete_feed_entry(self, feed_entry: FeedEntry) -> None:

        with self.db.begin(db=self._db(Named.entry_content), write=True) as txn:
            txn.delete(self._serialize(feed_entry.id))

        with self.db.begin(db=self._db(Named.entry), write=True) as txn:
            txn.delete(self._serialize(feed_entry.id))

        with self.db.begin(db=self._db(Named.si_feed_entry), write=True) as txn:
            value = txn.get(self._serialize(feed_entry.feed_id))

            entries: List[str] = self._deserialize(value)
            entries.remove(feed_entry.id)

            txn.replace(self._serialize(feed_entry.feed_id), self._serialize(entries))
