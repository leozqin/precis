from yaml import load, SafeLoader
from logging import getLogger
from calendar import timegm

from datetime import datetime, timezone

from rssynthesis.db import DB
from rssynthesis.models import Feed

logger = getLogger("uvicorn.error")

db = DB()


def load_feeds(config_path: str) -> None:
    with open(config_path, "r") as fp:
        configs = load(fp, Loader=SafeLoader)

    for config in configs:
        feed = Feed(**config)
        logger.info(f"Found feed id {feed.id} with contents {feed.dict()}")

        db.clear_active_feeds()
        db.insert_feed(feed)


def check_feeds():
    now = int(datetime.now(tz=timezone.utc).timestamp())
    logger.info(f"Checking feeds starting at time {now}")
    new_items = []

    for feed in db.get_feeds():
        logger.info(f"Polling feed {feed.id}: {feed.name}")

        poll_state = db.get_poll_state(feed)
        if poll_state:
            for entry in feed.rss.entries:
                published_time = timegm(entry.published_parsed)
                logger.info(published_time)

                if published_time > poll_state:
                    new_items.append(entry)
        else:
            # if we have no history, take the first 5
            new_items.extend(feed.rss.entries[0:4])

        db.update_poll_state(feed=feed, now=now)

    logger.info(f"Found {len(new_items)} new item(s)")

    return new_items
