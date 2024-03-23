from logging import getLogger
from time import localtime, strftime

from rssynthesis.db import DB
from rssynthesis.models import Feed, FeedEntry, EntryContent

logger = getLogger("uvicorn.error")

db = DB()


def list_feeds():
    feeds = db.get_feeds()

    return [
        {
            "id": feed.id,
            "name": feed.name,
            "category": feed.category,
            "type": feed.type,
            "url": feed.url,
        }
        for feed in feeds
    ]


def list_entries(feed_id: None):

    if feed_id:
        feed = db.get_feed(id=feed_id)
    else:
        feed = None

    entries = db.get_entries(feed)

    for entry in entries:
        feed_entry: FeedEntry = entry["entry"]

        yield {
            "title": feed_entry.title,
            "url": feed_entry.url,
            "published_at": strftime(
                "%Y-%m-%d %H:%M", localtime(feed_entry.published_at)
            ),
            "updated_at": strftime(
                "%Y-%m-%d %H:%M", localtime(feed_entry.updated_at)
            ),
            "preview": feed_entry.preview,
            "id": entry["id"],
            "feed_id": entry["feed_id"],
        }


def get_entry_content(feed_entry_id):
    entry = db.get_feed_entry(id=feed_entry_id)
    content: EntryContent = db.get_entry_content(entry=entry)

    return {
        "title": entry.title,
        "url": entry.url,
        "content": content.content,
        "byline": ", ".join(entry.authors) if entry.authors else None,
    }
