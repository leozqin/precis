from logging import getLogger

from rssynthesis.db import DB
from rssynthesis.models import Feed

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