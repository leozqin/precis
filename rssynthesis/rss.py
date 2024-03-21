from typing import List, Union, ClassVar, Optional, Any, Type
from pydantic import BaseModel, computed_field
from aenum import Enum, extend_enum
from urllib.request import urlopen

from feedparser import parse, FeedParserDict


class Category(str, Enum):
    uncategorized = "uncategorized"


class Config(BaseModel):
    name: str
    category: str = "uncategorized"
    type: str = "rss"
    url: str

    @computed_field
    @property
    def rss(self) -> Type[FeedParserDict]:
        return parse(self.url)
