from yaml import load, SafeLoader
from logging import getLogger
from calendar import timegm
from typing import List, Mapping
from pathlib import Path

from datetime import datetime, timezone

from rssynthesis.db import DB
from rssynthesis.models import Feed, FeedEntry
from rssynthesis.notifications import notification_handler
from rssynthesis.constants import CONFIG_DIR

logger = getLogger("uvicorn.error")

db = DB()

def load_feeds() -> None:
    with open(Path(CONFIG_DIR, "feeds.yml").resolve(), "r") as fp:
        configs = load(fp, Loader=SafeLoader)

    db.clear_active_feeds()
    for config in configs:
        feed = Feed(**config)
        logger.info(f"Found feed id {feed.id} with contents {feed.dict()}")

        db.insert_feed(feed)

async def check_feeds() -> List:

    now = int(datetime.now(tz=timezone.utc).timestamp())
    logger.info(f"Checking feeds starting at time {now}")

    for feed in db.get_feeds():
        new_items = []
        logger.info(f"Polling feed {feed.id}: {feed.name}")

        poll_state = db.get_poll_state(feed)
        if poll_state:
            for entry in feed.rss.entries:
                published_time = timegm(entry.published_parsed)

                if published_time > poll_state:
                    new_items.append(entry)
        else:
            # if we have no history, take the first 5
            new_items.extend(feed.rss.entries[0:5])

        db.update_poll_state(feed=feed, now=now)
        await add_feed_entries(feed=feed, entries=new_items)
        logger.info(f"Found {len(new_items)} new item(s) for feed {feed.name}")


async def add_feed_entries(feed: Feed, entries: List) -> None:

    for entry in entries:
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
        logger.info(
            f"Upserting entry from {feed.name}: {feed_entry.title} - id {feed_entry.id}"
        )

        db.upsert_feed_entry(feed=feed, entry=feed_entry)
        db.get_entry_content(entry=feed_entry)

        await notification_handler.send_notification(feed=feed, entry=feed_entry)
