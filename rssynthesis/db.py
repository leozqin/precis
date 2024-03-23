from pathlib import Path
from tinydb import TinyDB, Query
from rssynthesis.models import Feed, FeedEntry
from typing import List, Optional


class DB:
    """
    Use this class to encapsulate DB interactions
    """

    db_path = Path(Path(__file__).parent, "../", "db.json").resolve()
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
            {
                "entry": FeedEntry(**i["entry"]),
                "feed_id": i["feed_id"],
                "id": i["id"]
            } for i in entries
        ]