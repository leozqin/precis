from logging import getLogger
from pydantic import BaseModel
from typing import Any, Mapping, ClassVar, Type
from pathlib import Path
from yaml import load, SafeLoader

from rssynthesis.summarization.ollama import OllamaSummarizationHandler
from rssynthesis.models import SummarizationHandler
from rssynthesis.constants import CONFIG_DIR

logger = getLogger("uvicorn.error")


class SummarizationEngine(BaseModel):
    type: str
    config: Mapping[str, Any] = {}

    handlers: ClassVar = {
        "ollama": OllamaSummarizationHandler
    }

    def get_handler(self) -> Type[SummarizationHandler]:
        logger.info(f"loading summarization handler of type {self.type}")
        return self.handlers[self.type](**self.config)


def load_summarization_config() -> SummarizationEngine:
    summarization_config_path = Path(CONFIG_DIR, "summarization.yml").resolve()

    with open(summarization_config_path, "r") as fp:
        config = load(fp, Loader=SafeLoader)

    return SummarizationEngine(**config)


summarization_handler = load_summarization_config().get_handler()
