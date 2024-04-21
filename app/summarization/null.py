from pydantic import BaseModel
from typing import ClassVar

from app.models import SummarizationHandler, Feed, FeedEntry


class NullSummarizationHandler(SummarizationHandler, BaseModel):
    id: ClassVar[str] = "null"

    def summarize(self, feed: Feed, entry: FeedEntry, mk: str):
        return None
