from logging import getLogger
from pydantic import BaseModel
from typing import Any, Mapping, ClassVar, Type
from pathlib import Path
from yaml import load, SafeLoader

from rssynthesis.notification.matrix import MatrixNotificationHandler
from rssynthesis.models import NotificationHandler
from rssynthesis.constants import CONFIG_DIR

logger = getLogger("uvicorn.error")


class NotificationEngine(BaseModel):
    type: str
    config: Mapping[str, Any] = {}

    handlers: ClassVar = {"matrix": MatrixNotificationHandler}

    def get_handler(self) -> Type[NotificationHandler]:
        logger.info(f"loading notification handler of type {self.type}")
        return self.handlers[self.type](**self.config)


def load_notification_config() -> NotificationEngine:
    notification_config_path = Path(CONFIG_DIR, "settings.yml").resolve()

    with open(notification_config_path, "r") as fp:
        config = load(fp, Loader=SafeLoader)

    return NotificationEngine(**config.get("notification", {}))


notification_handler = load_notification_config().get_handler()
