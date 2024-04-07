from logging import getLogger
from pathlib import Path
from typing import List, Optional

from html2text import HTML2Text
from markdown2 import markdown
from readabilipy import simple_json_from_html_string
from readability import Document
from tinydb import Query, TinyDB

from app.constants import DATA_DIR
from app.content.engine import content_handler
from app.models import EntryContent, Feed, FeedEntry
from app.summarization.engine import summarization_handler

logger = getLogger("uvicorn.error")


class DB:
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

    def upsert_feed_entry(self, feed: Feed, entry: FeedEntry):
        table = self.db.table("entries")

        row = {
            "id": entry.id,
            "feed_id": feed.id,
            "entry": entry.dict(),
        }

        query = Query().id.matches(entry.id)
        table.upsert(row, cond=query)

    def get_entries(self, feed: Feed = None):
        table = self.db.table("entries")

        if feed:
            query = Query().feed_id.matches(feed.id)
            entries = table.search(query)
        else:
            entries = table.all()

        return [
            {"entry": FeedEntry(**i["entry"]), "feed_id": i["feed_id"], "id": i["id"]}
            for i in entries
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

    @staticmethod
    async def _get_entry_html(url: str) -> str:

        return await content_handler.get_content(url)

    @staticmethod
    def _get_entry_md(content: str) -> str:

        md = simple_json_from_html_string(html=content)

        cleaned_document = Document(input=md["content"])

        converter = HTML2Text()
        converter.ignore_images = True
        converter.ignore_links = True

        return converter.handle(cleaned_document.summary(html_partial=True))

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
                logger.info(f"starting redrive for feed entry {entry.id}")

            raw_content = await self._get_entry_html(entry.url)
            content = self._get_entry_md(content=raw_content)

            summary = summarization_handler.summarize(
                feed=self.get_feed(entry.feed_id), entry=FeedEntry, mk=content
            )

            entry_content = EntryContent(
                url=entry.url,
                content=markdown(content),
                summary=markdown(summary) if summary else None,
            )

            query = Query().id.matches(entry.id)
            table.upsert(
                {"id": entry_content.id, "entry_contents": entry_content.dict()},
                cond=query,
            )

            return entry_content
