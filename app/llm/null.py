from typing import ClassVar

from pydantic import BaseModel

from app.handlers import Feed, FeedEntry, LLMHandler


class NullLLMHandler(LLMHandler, BaseModel):
    id: ClassVar[str] = "null_llm"

    def summarize(self, feed: Feed, entry: FeedEntry, mk: str):
        return None
