from yaml import load, SafeLoader
from logging import getLogger
from calendar import timegm
from typing import List

from datetime import datetime, timezone

from rssynthesis.db import DB
from rssynthesis.models import Feed, FeedEntry

logger = getLogger("uvicorn.error")

db = DB()


def load_feeds(config_path: str) -> None:
    with open(config_path, "r") as fp:
        configs = load(fp, Loader=SafeLoader)

    db.clear_active_feeds()
    for config in configs:
        feed = Feed(**config)
        logger.info(f"Found feed id {feed.id} with contents {feed.dict()}")

        db.insert_feed(feed)


def check_feeds() -> List:
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
        add_feed_entries(feed=feed, entries=new_items)
        logger.info(f"Found {len(new_items)} new item(s) for feed {feed.name}")


def add_feed_entries(feed: Feed, entries: List) -> None:
    for entry in entries:
        feed_entry = FeedEntry(
            **{
                "title": entry.title,
                "url": entry.link,
                "published_at": timegm(entry.published_parsed),
                "updated_at": timegm(entry.updated_parsed),
                "preview": entry.summary,
                "authors": (
                    [i["name"] for i in entry.authors] if "authors" in entry else []
                ),
            }
        )
        logger.info(
            f"Upserting entry from {feed.name}: {feed_entry.title} - id {feed_entry.id}"
        )

        db.upsert_feed_entry(feed=feed, entry=feed_entry)
