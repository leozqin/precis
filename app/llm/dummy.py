from typing import ClassVar

from pydantic import BaseModel

from app.handlers import Feed, FeedEntry, LLMHandler


# An LLM Handler that doesn't return anything meaningful, but does return
# something, unlike null. Useful for testing or pranking your friends.
class DummyLLMHandler(LLMHandler, BaseModel):
    id: ClassVar[str] = "dummy_llm"
    # a dummy config option
    temerity: int = 5

    def summarize(self, feed: Feed, entry: FeedEntry, mk: str):
        return "cool story bro"
