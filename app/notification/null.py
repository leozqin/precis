from pydantic import BaseModel
from typing import ClassVar

from app.models import NotificationHandler, Feed, FeedEntry


class NullNotificationHandler(NotificationHandler, BaseModel):
    id: ClassVar[str] = "null"

    async def send_notification(self, feed: Feed, entry: FeedEntry):
        return None
