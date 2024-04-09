from logging import getLogger
from pathlib import Path
from typing import Any, ClassVar, Mapping, Type

from pydantic import BaseModel
from yaml import SafeLoader, load

from app.constants import CONFIG_DIR
from app.models import SummarizationHandler
from app.summarization.ollama import OllamaSummarizationHandler
from app.summarization.openai import OpenAISummarizationHandler

logger = getLogger("uvicorn.error")


class SummarizationEngine(BaseModel):
    type: str
    config: Mapping[str, Any] = {}

    handlers: ClassVar = {
        "ollama": OllamaSummarizationHandler,
        "openai": OpenAISummarizationHandler,
    }

    def get_handler(self) -> Type[SummarizationHandler]:
        logger.info(f"loading summarization handler of type {self.type}")
        return self.handlers[self.type](**self.config)


def load_summarization_config() -> SummarizationEngine:
    summarization_config_path = Path(CONFIG_DIR, "settings.yml").resolve()

    with open(summarization_config_path, "r") as fp:
        config = load(fp, Loader=SafeLoader)

    return SummarizationEngine(**config.get("summarization", {}))


summarization_handler = load_summarization_config().get_handler()
