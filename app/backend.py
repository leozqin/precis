from importlib.metadata import version
from json import dumps, loads
from logging import getLogger
from sys import version as py_version
from time import localtime, strftime, time
from typing import List, Mapping, Type

from pydantic import BaseModel
from textstat import textstat as txt

from app.constants import GITHUB_LINK, IS_DOCKER
from app.context import GlobalSettings, StorageHandler
from app.errors import InvalidFeedException
from app.models import EntryContent, Feed, FeedEntry, HealthCheck

logger = getLogger("uvicorn.error")


class PrecisBackend:
    def __init__(self, db: Type[StorageHandler]):
        self.db = db

    @staticmethod
    def _format_time(time: int) -> str:
        return strftime("%Y-%m-%d %I:%M %p", localtime(time)).lower()

    def health_check(self):

        return HealthCheck()

    def about(self):

        return {
            "version": version("precis"),
            "python_version": py_version,
            "fastapi_version": version("fastapi"),
            "docker": IS_DOCKER,
            "storage_handler": type(self.db).__name__,
            "github": GITHUB_LINK,
        }

    def list_feeds(self, agg=False):
        feeds = self.db.get_feeds()
        entry_list = self.db.get_entries() or []
        entries: List[FeedEntry] = [i["entry"] for i in entry_list]

        if agg:
            entry_agg = {}

            for entry in entries:
                if entry.feed_id in entry_agg:
                    entry_agg[entry.feed_id] += 1
                else:
                    entry_agg[entry.feed_id] = 1

        return [
            {
                "id": feed.id,
                "name": feed.name,
                "category": feed.category,
                "type": feed.type,
                "url": feed.url,
                "preview_only": feed.preview_only,
                "notify": feed.notify,
                "refresh_enabled": feed.refresh_enabled,
                "entry_count": entry_agg.get(feed.id, 0) if agg else False,
            }
            for feed in feeds
        ]

    def list_entries(self, feed_id: None, recent: bool = False):

        if feed_id:
            feed = self.db.get_feed(id=feed_id)
        else:
            feed = None

        settings: GlobalSettings = self.db.get_settings()
        start_time = time() - (settings.recent_hours * 3600)

        if recent:
            entries = self.db.get_entries(feed, after=start_time)
        else:
            entries = self.db.get_entries(feed=feed)

        for entry in entries:
            feed_entry: FeedEntry = entry["entry"]
            if not feed:
                local_feed: Feed = self.db.get_feed(entry["feed_id"])

            yield {
                "feed_name": feed.name if feed else local_feed.name,
                "title": feed_entry.title,
                "url": feed_entry.url,
                "published_at": self._format_time(feed_entry.published_at),
                "updated_at": self._format_time(feed_entry.updated_at),
                "sort_time": feed_entry.published_at,
                "preview": feed_entry.preview,
                "id": entry["id"],
                "feed_id": entry["feed_id"],
            }

    async def get_entry_content(self, feed_entry_id, redrive: bool = False):
        entry: FeedEntry = self.db.get_feed_entry(id=feed_entry_id)
        feed: Feed = self.db.get_feed(entry.feed_id)
        settings: GlobalSettings = self.db.get_settings()

        base = {
            "id": feed_entry_id,
            "feed_id": entry.feed_id,
            "feed_name": feed.name,
            "title": entry.title,
            "url": entry.url,
            "published_at": self._format_time(entry.published_at),
            "updated_at": self._format_time(entry.updated_at),
            "byline": ", ".join(entry.authors) if entry.authors else None,
        }

        if feed.preview_only:
            return {**base, "preview": entry.preview, "content": None, "summary": None}
        else:
            content: EntryContent = await self.db.get_entry_content(
                entry=entry, redrive=redrive
            )
            word_count = txt.lexicon_count(content.content)
            return {
                **base,
                "preview": None,
                "content": content.content,
                "summary": content.summary,
                "word_count": word_count,
                "reading_level": int(
                    txt.text_standard(content.content, float_output=True)
                ),
                "reading_time": int(word_count / settings.reading_speed),
            }

    def get_handlers(self):

        handlers = self.db.get_handlers()

        return [
            {
                "type": k,
                "handler_type": self.db.handler_type_map[k],
                "config": v.dict() if v else None,
            }
            for k, v in handlers.items()
        ]

    def get_handler_config(self, handler: str):

        try:
            handler = self.db.get_handler(id=handler)
            return {"type": handler.id, "config": dumps(handler.dict(), indent=4)}

        except IndexError:
            return {"type": handler, "config": None}

    def get_handler_schema(self, handler: str):

        handler_obj: Type[BaseModel] = self.db.handler_map.get(handler)

        return dumps(handler_obj.schema(), indent=4)

    async def get_settings(self):

        settings: GlobalSettings = self.db.get_settings()

        return settings.dict()

    async def get_feed_config(self, id: str) -> Mapping:

        feed: Feed = self.db.get_feed(id=id)

        return {"id": feed.id, **feed.dict()}

    async def update_feed(self, feed: Feed):
        if not feed.validate():
            logger.info("feed is invalid!")
            raise InvalidFeedException(
                (
                    f"Feed {feed.name} does not have any entries at url {feed.url}. "
                    "Press back to return to the feed you configured"
                )
            )

        self.db.upsert_feed(feed=feed)
        settings = self.db.get_settings()

        if not settings.finished_onboarding:
            settings.finished_onboarding = True
            self.db.upsert_settings(settings=settings)

    async def update_settings(self, settings: GlobalSettings):

        self.db.upsert_settings(settings=settings)

    async def update_handler(self, handler: str, config: str):

        config_dict = loads(config)
        handler_obj = self.db.reconfigure_handler(id=handler, config=config_dict)
        self.db.upsert_handler(handler=handler_obj)

    async def delete_feed(self, feed_id: str):

        feed = self.db.get_feed(id=feed_id)

        entries = self.db.get_entries(feed=feed)
        for entry_dict in entries:
            entry: FeedEntry = entry_dict.get("entry")
            self.db.delete_feed_entry(feed_entry=entry)

        self.db.delete_feed(feed=feed)

    @staticmethod
    async def list_content_handler_choices():
        from app.content import content_retrieval_handlers

        return list(content_retrieval_handlers.keys())

    @staticmethod
    async def list_summarization_handler_choices():
        from app.summarization import summarization_handlers

        return list(summarization_handlers.keys())

    @staticmethod
    async def list_notification_handler_choices():
        from app.notification import notification_handlers

        return list(notification_handlers.keys())
