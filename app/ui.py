from logging import getLogger
from time import localtime, strftime
from typing import List
from json import dumps

from app.storage.engine import storage_handler as db
from app.models import EntryContent, Feed, FeedEntry

logger = getLogger("uvicorn.error")


def _format_time(time: int) -> str:
    return strftime("%Y-%m-%d %I:%M %p", localtime(time)).lower()


def list_feeds():
    feeds = db.get_feeds()
    entries: List[FeedEntry] = [i["entry"] for i in db.get_entries()]

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
            "entry_count": entry_agg.get(feed.id, 0),
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
            "feed_name": feed.name if feed else "All",
            "title": feed_entry.title,
            "url": feed_entry.url,
            "published_at": _format_time(feed_entry.published_at),
            "updated_at": _format_time(feed_entry.updated_at),
            "sort_time": feed_entry.published_at,
            "preview": feed_entry.preview,
            "id": entry["id"],
            "feed_id": entry["feed_id"],
        }


async def get_entry_content(feed_entry_id, redrive: bool = False):
    entry: FeedEntry = db.get_feed_entry(id=feed_entry_id)
    feed: Feed = db.get_feed(entry.feed_id)

    base = {
        "id": feed_entry_id,
        "feed_id": entry.feed_id,
        "feed_name": feed.name,
        "title": entry.title,
        "url": entry.url,
        "published_at": _format_time(entry.published_at),
        "updated_at": _format_time(entry.updated_at),
        "byline": ", ".join(entry.authors) if entry.authors else None,
    }

    if feed.preview_only:
        return {**base, "preview": entry.preview, "content": None, "summary": None}
    else:
        content: EntryContent = await db.get_entry_content(entry=entry, redrive=redrive)
        return {
            **base,
            "preview": None,
            "content": content.content,
            "summary": content.summary,
        }


def get_handlers():

    handlers = db.get_handlers()

    return [
        {
            "type": k,
            "handler_type": db.handler_type_map[k],
            "config": v.dict() if v else None,
        }
        for k, v in handlers.items()
    ]


def get_handler_config(handler: str):

    try:
        handler = db.get_handler(id=handler)
        return {"type": handler.id, "config": dumps(handler.dict(), indent=4)}

    except IndexError:
        return {"type": handler, "config": None}


def get_settings():

    settings = db.get_settings()

    return settings.dict()
