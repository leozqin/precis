from enum import Enum

from app.llm.null import NullLLMHandler
from app.llm.ollama import OllamaLLMHandler
from app.llm.openai import OpenAILLMHandler

llm_handlers = {
    "null_llm": NullLLMHandler,
    "ollama": OllamaLLMHandler,
    "openai": OpenAILLMHandler,
}
