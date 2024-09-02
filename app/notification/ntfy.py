from json import dumps
from logging import getLogger
from os import environ
from typing import ClassVar, Mapping

import requests

from app.handlers import NotificationHandler
from app.models import Feed, FeedEntry

logger = getLogger("uvicorn.error")


class NtfyNotificationHandler(NotificationHandler):
    id: ClassVar[str] = "ntfy"
    root_url: str = environ.get("NTFY_ROOT_URL", "https://ntfy.sh/")
    topic: str = environ.get("NTFY_TOPIC")
    routing: Mapping[str, str] = {}

    async def send_notification(self, feed: Feed, entry: FeedEntry):

        if feed.notify_destination:
            topic = self.routing.get(feed.notify_destination, self.topic)
            logger.info(f"Sending message to topic {feed.notify_destination} - {topic}")
        else:
            topic = self.topic
            logger.info(f"Sending message to default topic {topic}")

        headers = {
            "title": "Precis: New Feed Entry",
            "tags": ["newspaper"],
            "click": self.make_read_link(entry),
        }

        actions = [
            {
                "action": "view",
                "label": "Read in Precis",
                "url": self.make_read_link(entry),
            },
            {"action": "view", "label": "View Original", "url": entry.url},
        ]

        messsage = f"{feed.name} - {entry.title}"

        data = {
            "topic": topic,
            **headers,
            "message": messsage,
            "actions": actions,
        }

        logger.debug(f"request to ntfy: {data}")

        req = requests.post(url=self.root_url, data=dumps(data))

        logger.debug(f"response from ntfy: {req.text}: {req.reason}")
