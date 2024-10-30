from app.llm.null import NullLLMHandler
from app.llm.ollama import OllamaLLMHandler
from app.llm.openai import OpenAILLMHandler

llm_handlers = {
    NullLLMHandler.id: NullLLMHandler,
    OllamaLLMHandler.id: OllamaLLMHandler,
    OpenAILLMHandler.id: OpenAILLMHandler,
    # redirect null summarization handler to null llm
    # TODO: Deprecate
    "null_summarization": NullLLMHandler,
}
