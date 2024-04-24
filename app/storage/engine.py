from logging import getLogger
from pathlib import Path
from typing import Type

from ruamel.yaml import YAML

from app.constants import CONFIG_DIR
from app.context import StorageHandler
from app.storage import storage_handlers

logger = getLogger("uvicorn.error")


def load_storage_config() -> Type[StorageHandler]:
    notification_config_path = Path(CONFIG_DIR, "settings.yml").resolve()

    with open(notification_config_path, "r") as fp:
        yaml = YAML(typ="safe")
        config = yaml.load(fp)

    config_type = config.get("type", "tinydb")
    handler_type = storage_handlers.get(config_type)
    handler = handler_type(**config.get("config", {}))

    logger.info(f"loading storage handler of type {config_type}")

    return handler
