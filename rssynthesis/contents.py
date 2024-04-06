from typing import Mapping, Any, Type, ClassVar
from yaml import load, SafeLoader
from logging import getLogger
from pathlib import Path

from pydantic import BaseModel
from rssynthesis.content.playwright import PlaywrightContentRetriever
from rssynthesis.content.requests import RequestsContentRetriever

from rssynthesis.models import ContentRetriever
from rssynthesis.constants import CONFIG_DIR

logger = getLogger("uvicorn.error")

class ContentRetrievalEngine(BaseModel):
    type: str
    config: Mapping[str, Any] = {}

    handlers: ClassVar = {
        "requests": RequestsContentRetriever,
        "playwright": PlaywrightContentRetriever,
    }

    def get_handler(self) -> Type[ContentRetriever]:
        logger.info(f"loading content handler of type {self.type}")
        return self.handlers[self.type](**self.config)


def load_content_config() -> ContentRetrievalEngine:
    content_config_path = Path(CONFIG_DIR, "settings.yml").resolve()

    with open(content_config_path, "r") as fp:
        config = load(fp, Loader=SafeLoader)

    return ContentRetrievalEngine(**config.get("content", {}))


content_handler = load_content_config().get_handler()
