from logging import getLogger
from pathlib import Path
from typing import Any, ClassVar, Mapping, Type

from pydantic import BaseModel
from ruamel.yaml import YAML

from app.constants import CONFIG_DIR
from app.db import StorageHandler
from app.storage.tinydb import TinyDBStorageHandler

logger = getLogger("uvicorn.error")


class StorageEngine(BaseModel):
    type: str
    config: Mapping[str, Any] = {}

    handlers: ClassVar = {"tinydb": TinyDBStorageHandler}

    def get_handler(self) -> Type[StorageHandler]:
        logger.info(f"loading storage handler of type {self.type}")
        return self.handlers[self.type](**self.config)


def load_storage_config() -> StorageEngine:
    notification_config_path = Path(CONFIG_DIR, "settings.yml").resolve()

    with open(notification_config_path, "r") as fp:
        yaml = YAML(typ="safe")
        config = yaml.load(fp)

    return StorageEngine(**config.get("storage", {}))


storage_handler = load_storage_config().get_handler()
