from typing import ClassVar

from pydantic import BaseModel

from app.handlers import Feed, FeedEntry, SummarizationHandler


class NullSummarizationHandler(SummarizationHandler, BaseModel):
    id: ClassVar[str] = "null"

    def summarize(self, feed: Feed, entry: FeedEntry, mk: str):
        return None
