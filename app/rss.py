from calendar import timegm
from datetime import datetime, timezone
from json import dump, load
from logging import getLogger
from pathlib import Path
from tempfile import SpooledTemporaryFile
from typing import List, Mapping, Type

from opml import OpmlDocument, OpmlOutline
from ruamel.yaml import YAML

from app.constants import CONFIG_DIR, DATA_DIR
from app.context import GlobalSettings, StorageHandler
from app.models import EntryContent, Feed, FeedEntry

logger = getLogger("uvicorn.error")


class PrecisRSS:
    def __init__(self, db: Type[StorageHandler]) -> None:
        self.db = db

    def load_feeds(self) -> None:
        feeds_path = Path(CONFIG_DIR, "feeds.yml").resolve()
        logger.info("Loading feeds from config", extra={"path": feeds_path})
        with open(feeds_path, "r") as fp:
            yaml = YAML(typ="safe")
            configs = yaml.load(fp)

        for config in configs:
            feed = Feed(**config)
            logger.info(f"Found feed id {feed.id} with contents {feed.dict()}")

            self.db.upsert_feed(feed)

    def load_settings(self) -> None:
        with open(Path(CONFIG_DIR, "settings.yml").resolve(), "r") as fp:
            yaml = YAML(typ="safe")
            configs = yaml.load(fp)

        settings = GlobalSettings(**configs, db=self.db)

        self.db.upsert_settings(settings)

    def load_handlers(self) -> None:
        with open(Path(CONFIG_DIR, "handlers.yml").resolve(), "r") as fp:
            yaml = YAML(typ="safe")
            configs: dict = yaml.load(fp)

        for k, v in configs.items():
            self.db.reconfigure_handler(id=k, config=v)

    async def _process_feed_entry(
        self, entry: Mapping, feed: Feed, start_ts: int
    ) -> True:
        published_time = timegm(entry.published_parsed)
        feed_entry = FeedEntry(
            **{
                "title": entry.title,
                "url": entry.link,
                "published_at": timegm(entry.published_parsed),
                "updated_at": timegm(entry.updated_parsed),
                "preview": entry.summary,
                "feed_id": feed.id,
                "authors": (
                    [i["name"] for i in entry.authors] if "authors" in entry else []
                ),
            }
        )

        if published_time >= (
            start_ts if start_ts else 0
        ) and not self.db.feed_entry_exists(feed_entry.id):
            await self.add_feed_entry(feed=feed, entry=feed_entry)
            return True

    async def _check_feed(self, feed: Feed):
        now = int(datetime.now(tz=timezone.utc).timestamp())
        logger.info(f"Polling feed {feed.id}: {feed.name}")

        poll_state = self.db.get_poll_state(feed)
        logger.info(f"Retrieved poll state: {poll_state}")
        if poll_state:
            entries = feed.rss.entries
        else:
            # if we have no history, take the first 5
            entries = feed.rss.entries[0:5]
            earliest_init_entry = min(
                [timegm(i.published_parsed) for i in entries] + [now]
            )
            self.db.set_feed_start_ts(feed=feed, start_ts=earliest_init_entry)

        logger.info("Starting feed entry retrieval")
        counter = 0
        start_ts = self.db.get_feed_start_ts(feed=feed)
        for entry in entries:
            processed = await self._process_feed_entry(
                entry=entry, feed=feed, start_ts=start_ts
            )
            if processed:
                counter += 1

        self.db.update_poll_state(feed=feed, now=now)

        logger.info(f"Found {counter} new item(s) for feed {feed.name}")

    async def check_feeds(self) -> List:

        now = int(datetime.now(tz=timezone.utc).timestamp())
        logger.info(f"Checking feeds starting at time {now}")

        for feed in self.db.get_feeds():
            feed: Feed
            if feed.refresh_enabled:
                await self._check_feed(feed=feed)

    async def check_feed_by_id(self, id: str) -> List:

        feed = self.db.get_feed(id=id)

        logger.info(f"Manual refresh requested for feed {feed.name}")

        await self._check_feed(feed=feed)

    async def add_feed_entry(self, feed: Feed, entry: FeedEntry) -> None:

        logger.info(f"Upserting entry from {feed.name}: {entry.title} - id {entry.id}")

        self.db.upsert_feed_entry(feed=feed, entry=entry)

        settings: GlobalSettings = self.db.get_settings()

        if not feed.preview_only:
            await self.db.get_entry_content(entry=entry)

        if feed.notify:
            if settings.send_notification:
                await settings.notification_handler.send_notification(
                    feed=feed, entry=entry
                )
            else:
                logger.info(
                    f"skipping notification for {entry.id} because of global setting"
                )

    @staticmethod
    async def get_entry_html(url: str, settings: GlobalSettings) -> str:
        return await settings.content_retrieval_handler.get_content(url)

    async def feeds_to_opml(self) -> OpmlDocument:
        feeds = self.db.get_feeds()

        opml = OpmlDocument(
            title="Precis RSS Backup",
            date_created=datetime.now(),
            date_modified=datetime.now(),
        )

        for feed in feeds:
            feed: Feed
            opml.add_rss(text=feed.name, xml_url=feed.url, categories=[feed.category])

        str_now = datetime.now().strftime("%Y%m%d%H%M%S")
        file_name = f"precis_{str_now}.opml"
        out_path = Path(DATA_DIR, file_name).resolve()

        logger.info(f"writing opml to {out_path}")
        opml.dump(fp=out_path)

        return out_path, file_name

    async def opml_to_feeds(self, file: SpooledTemporaryFile):

        opml = OpmlDocument.load(fp=file)

        feeds = []

        for entry in opml.outlines:
            entry: OpmlOutline

            feed = Feed(
                name=entry.text, url=entry.xml_url, category=entry.categories[0] or None
            )

            feeds.append(feed)

        for feed in feeds:
            self.db.upsert_feed(feed=feed)

        settings: GlobalSettings = self.db.get_settings()
        if not settings.finished_onboarding:
            settings.finished_onboarding = True
            self.db.upsert_settings(settings=settings)

    async def backup(self):

        feeds = self.db.get_feeds()
        settings: GlobalSettings = self.db.get_settings()
        handlers = self.db.get_handlers()

        backup = {
            "settings": settings.dict(exclude={"db"}),
            "handlers": {k: v.dict() for k, v in handlers.items() if v},
            "feeds": [i.dict() for i in feeds],
            "feed_entries": {},
            "entry_content": {},
            "poll_state": {},
        }

        for feed in feeds:
            feed: Feed
            backup["poll_state"][feed.id] = self.db.get_poll_state(feed)
            entries = [i["entry"] for i in self.db.get_entries(feed)]
            entry_content = {i.id: await self.db.get_entry_content(i) for i in entries}
            backup["feed_entries"][feed.id] = [i.dict() for i in entries]
            backup["entry_content"][feed.id] = {
                k: v.dict() for k, v in entry_content.items()
            }

        str_now = datetime.now().strftime("%Y%m%d%H%M%S")
        file_name = f"precis_backup_{str_now}.json"
        out_path = Path(DATA_DIR, file_name).resolve()

        logger.info(f"writing backup to {out_path}")

        with open(out_path, "w+") as fp:
            dump(backup, fp)

        return out_path, file_name

    async def restore(self, file: SpooledTemporaryFile):

        bk = load(file)

        settings = GlobalSettings(db=self.db, **bk.get("settings", {}))
        settings.finished_onboarding = True

        handlers = [
            self.db.reconfigure_handler(id=k, config=v)
            for k, v in bk.get("handlers", {}).items()
        ]
        feeds = [Feed(**i) for i in bk.get("feeds", [])]

        for handler in handlers:
            self.db.upsert_handler(handler=handler)

        self.db.upsert_settings(settings)

        for feed in feeds:
            self.db.upsert_feed(feed)

        feed_entries: dict = bk.get("feed_entries", {})
        for feed, entries in feed_entries.items():
            feed_obj = self.db.get_feed(id=feed)
            for entry in entries:
                entry_obj = FeedEntry(**entry)
                self.db.upsert_feed_entry(feed=feed_obj, entry=entry_obj)

        content: dict = bk.get("entry_content", {})
        for contents in content.values():
            for i in contents.values():
                content_obj = EntryContent(**i)
                await self.db.upsert_entry_content(content=content_obj)
