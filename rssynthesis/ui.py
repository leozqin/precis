from logging import getLogger

from rssynthesis.db import DB
from rssynthesis.models import Feed, FeedEntry

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
            "url": feed.url
        } for feed in feeds
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
            "published_at": feed_entry.published_at,
            "updated_at": feed_entry.updated_at,
            "preview": feed_entry.preview,
            "id": entry["id"],
            "feed_id": entry["feed_id"]
        }