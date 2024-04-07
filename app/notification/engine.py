from logging import getLogger
from pathlib import Path
from typing import Any, ClassVar, Mapping, Type

from pydantic import BaseModel
from yaml import SafeLoader, load

from app.constants import CONFIG_DIR
from app.models import NotificationHandler
from app.notification.matrix import MatrixNotificationHandler

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
