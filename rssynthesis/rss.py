from typing import List, Union, ClassVar, Optional, Any, Type
from yaml import load, SafeLoader
from logging import getLogger
from tinydb import TinyDB

from time import struct_time
from datetime import datetime, timedelta

from fastapi_utils.tasks import repeat_every
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
    now = int(datetime.now().timestamp())
    new_items = []

    for feed in db.get_feeds():
        logger.info(f"Polling feed {id}: {feed.name}")

        poll_state = db.get_poll_state(feed)
        if poll_state:
            for entry in feed.rss.entries:
                published_time: struct_time = int(entry.published_time)

                if published_time > poll_state:
                    new_items.append(entry)
        else:
            # if we have no history, take the first 5
            new_items.extend(feed.rss.entries[0:4])

        db.update_poll_state(feed=feed, now=now)

    for item in new_items:
        logger.info(f"Found new item {item}")

    return new_items

@repeat_every(seconds=60 * 5)
def poll_feeds():
    check_feeds()
