from logging import getLogger
from pathlib import Path
from typing import Any, ClassVar, Mapping, Type

from pydantic import BaseModel
from ruamel.yaml import YAML

from app.constants import CONFIG_DIR
from app.models import SummarizationHandler
from app.summarization.ollama import OllamaSummarizationHandler
from app.summarization.openai import OpenAISummarizationHandler
from app.summarization.null import NullSummarizationHandler

logger = getLogger("uvicorn.error")

class SummarizationEngine(BaseModel):
    type: str
    config: Mapping[str, Any] = {}

    handlers: ClassVar = {
        "ollama": OllamaSummarizationHandler,
        "openai": OpenAISummarizationHandler,
        "null": NullSummarizationHandler
    }

    def get_handler(self) -> Type[SummarizationHandler]:
        logger.info(f"loading summarization handler of type {self.type}")
        return self.handlers[self.type](**self.config)


def load_summarization_config() -> Type[SummarizationHandler]:
    summarization_config_path = Path(CONFIG_DIR, "settings.yml").resolve()

    with open(summarization_config_path, "r") as fp:
        yaml = YAML(typ="safe")
        config = yaml.load(fp)

    handler = SummarizationEngine(**config.get("summarization", {})).get_handler()
    return handler


summarization_handler = load_summarization_config()
