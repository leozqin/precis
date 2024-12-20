from logging import getLogger
from os import environ
from typing import ClassVar, Mapping

from slack_sdk.web.async_client import AsyncWebClient

from app.handlers import NotificationHandler
from app.models import Feed, FeedEntry

logger = getLogger("uvicorn.error")


class SlackNotificationHandler(NotificationHandler):
    id: ClassVar[str] = "slack"
    token: str = environ.get("SLACK_API_TOKEN")
    channel_name: str
    routing: Mapping[str, str] = {}

    @staticmethod
    def _escape_title(title: str) -> str:
        translation_table = {"&": "&amp;", "<": "&lt;", ">": "&gt;"}

        # Iterate over the string and replace characters if needed
        return "".join(translation_table.get(c, c) for c in title)

    async def send_notification(self, feed: Feed, entry: FeedEntry):
        client = AsyncWebClient(token=self.token)
        title = self._escape_title(entry.title)

        msg = f"{feed.name}: <{self.make_read_link(entry)}|{title}>"

        if feed.notify_destination:
            channel = self.routing.get(feed.notify_destination, self.channel_name)
            logger.info(
                "Sending notification to destination "
                f"{feed.notify_destination} - {channel}"
            )
        else:
            channel = self.channel_name
            logger.info(f"Sending notification to default channel {channel}")

        await client.chat_postMessage(channel=channel, text=msg, mrkdwn=True)
