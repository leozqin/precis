from rssynthesis.models import NotificationHandler

from simplematrixbotlib import Bot, Creds
from os import environ
from logging import getLogger
from typing import Mapping
from rssynthesis.models import Feed, FeedEntry

logger = getLogger("uvicorn.error")


class MatrixNotificationHandler(NotificationHandler):

    def __init__(
        self,
        homeserver: str,
        username: str,
        password: str,
        room_id: str,
        destinations=Mapping[str, str],
    ) -> None:
        self.room_id = room_id
        self.bot = Bot(
            creds=Creds(
                homeserver=homeserver,
                username=username,
                password=password,
            )
        )
        self.default_room = room_id
        self._destinations = destinations

    @property
    def destinations(self) -> Mapping[str, str]:
        return self._destinations

    @staticmethod
    def _make_read_link(entry: FeedEntry) -> str:
        base_url = environ["RSS_BASE_URL"]
        return f"{base_url}/read/{entry.id}"

    async def login(self):
        await self.bot.api.login()

    async def logout(self) -> None:
        await self.bot.api.async_client.logout()

    async def send_notification(self, feed: Feed, entry: FeedEntry):
        msg = f"{feed.name}: [{entry.title}]({self._make_read_link(entry)})"

        if feed.notify_destination:
            room = self.destinations.get(feed.notify_destination, self.default_room)
            logger.info(
                "Sending notification to destination "
                f"{feed.notify_destination} - {self.room_id}"
            )
        else:
            room = self.default_room
            logger.info(f"Sending notification to default {self.room_id}")

        await self.bot.api.send_markdown_message(room_id=room, message=msg)
