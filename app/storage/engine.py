from logging import getLogger
from os import environ
from typing import Type

from app.context import StorageHandler
from app.storage import storage_handlers

logger = getLogger("uvicorn.error")


def load_storage_config() -> Type[StorageHandler]:

    config_type = environ.get("PRECIS_STORAGE_HANDLER", "tinydb")
    handler_type = storage_handlers.get(config_type)
    handler = handler_type()

    logger.info(f"loading storage handler of type {config_type}")

    return handler
