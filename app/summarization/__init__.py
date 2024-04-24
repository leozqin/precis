from enum import Enum

from app.summarization.null import NullSummarizationHandler
from app.summarization.ollama import OllamaSummarizationHandler
from app.summarization.openai import OpenAISummarizationHandler

summarization_handlers = {
    "null_summarization": NullSummarizationHandler,
    "ollama": OllamaSummarizationHandler,
    "openai": OpenAISummarizationHandler,
}
