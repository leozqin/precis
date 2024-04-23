from logging import getLogger
from os import environ
from typing import ClassVar, Mapping

from pydantic import BaseModel, PrivateAttr
from simplematrixbotlib import Bot, Creds

from app.handlers import NotificationHandler
from app.models import Feed, FeedEntry

logger = getLogger("uvicorn.error")


class MatrixNotificationHandler(NotificationHandler, BaseModel):
    id: ClassVar[str] = "matrix"
    homeserver: str
    room_id: str
    username: str
    password: str
    routing: Mapping[str, str] = {}

    _bot: Bot = PrivateAttr(default=None)

    @property
    def bot(self):
        if not self._bot:
            self._bot = Bot(
                creds=Creds(
                    homeserver=self.homeserver,
                    username=self.username,
                    password=self.password,
                )
            )

        return self._bot

    @property
    def default_room(self):
        return self.room_id

    async def login(self):

        await self.bot.api.login()

    async def logout(self) -> None:
        await self.bot.api.async_client.logout()

    async def send_notification(self, feed: Feed, entry: FeedEntry):
        msg = f"{feed.name}: [{entry.title}]({self.make_read_link(entry)})"

        if feed.notify_destination:
            room = self.routing.get(feed.notify_destination, self.default_room)
            logger.info(
                "Sending notification to destination "
                f"{feed.notify_destination} - {room}"
            )
        else:
            room = self.default_room
            logger.info(f"Sending notification to default {room}")

        await self.bot.api.send_markdown_message(room_id=room, message=msg)
