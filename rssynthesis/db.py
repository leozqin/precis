from pathlib import Path
from tinydb import TinyDB, Query
from rssynthesis.models import Feed, FeedEntry, EntryContent
from rssynthesis.summarization.engine import summarization_handler
from typing import List, Optional
import requests
from html2text import HTML2Text
from readability import Document
from markdown2 import markdown
from rssynthesis.constants import DATA_DIR


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

    def get_entry_content(self, entry: FeedEntry) -> EntryContent:
        table = self.db.table("entry_contents")
        query = Query().id.matches(entry.id)

        existing = table.search(query)
        if existing:
            return EntryContent(**existing[0]["entry_contents"])

        else:
            raw_content = requests.get(entry.url)
            document = Document(raw_content.content)

            converter = HTML2Text()
            converter.ignore_images = True
            converter.ignore_links = True

            content = converter.handle(document.summary(html_partial=True))

            summary = summarization_handler.summarize(
                feed=self.get_feed(entry.feed_id), entry=FeedEntry, mk=content
            )

            entry_content = EntryContent(
                url=entry.url,
                content=markdown(content),
                summary=markdown(summary) if summary else None,
            )

            table.insert(
                {"id": entry_content.id, "entry_contents": entry_content.dict()}
            )

            return entry_content
