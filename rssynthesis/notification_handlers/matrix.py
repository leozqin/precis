from rssynthesis.models import NotificationHandler

from simplematrixbotlib import Bot, Creds
from os import environ
from logging import getLogger
from rssynthesis.models import Feed, FeedEntry

logger = getLogger("uvicorn.error")


class MatrixNotificationHandler(NotificationHandler):

    def __init__(
        self, homeserver: str, username: str, password: str, room_id: str
    ) -> None:
        self.room_id = room_id
        self.bot = Bot(
            creds=Creds(
                homeserver=homeserver,
                username=username,
                password=password,
            )
        )

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
        logger.info(f"Sending notification to {self.room_id}")

        await self.bot.api.send_markdown_message(room_id=self.room_id, message=msg)
