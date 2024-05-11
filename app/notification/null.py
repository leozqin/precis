from typing import ClassVar

from pydantic import BaseModel

from app.handlers import NotificationHandler
from app.models import Feed, FeedEntry


class NullNotificationHandler(NotificationHandler, BaseModel):
    id: ClassVar[str] = "null_notification"

    async def send_notification(self, feed: Feed, entry: FeedEntry):
        return None
