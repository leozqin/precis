from pydantic import BaseModel
from abc import ABC
from langchain_community.llms import ollama
from langchain_core.language_models.llms import BaseLLM
from feedparser import parse, FeedParserDict
from typing import Type, Mapping, Any, ClassVar
from json import dumps
from hashlib import md5
from enum import Enum


class Feed(BaseModel):
    name: str
    category: str = "uncategorized"
    type: str = "rss"
    url: str

    @property
    def rss(self) -> Type[FeedParserDict]:
        return parse(self.url)

    @property
    def id(self) -> str:
        id = dumps([self.name, self.category, self.type, self.url])
        return md5(id.encode()).hexdigest()


class FeedEntry(BaseModel):
    feed_id: str
    title: str
    url: str
    published_at: int
    updated_at: int
    authors: list[str] = []
    preview: str = None

    @property
    def id(self) -> str:
        return md5(self.url.encode()).hexdigest()


class EntryContent(BaseModel):
    url: str
    content: str = None
    summary: str = None

    @property
    def id(self) -> str:
        return md5(self.url.encode()).hexdigest()


class LLM(BaseModel):
    type: str
    config: Mapping[str, Any] = {}

    llm_type_map: ClassVar = {"ollama": ollama.Ollama}

    @property
    def llm(self) -> Type[BaseLLM]:
        if self.type not in self.llm_type_map:
            raise ValueError(f"supported llm types are {list(self.llm_type_map.keys())}")
        return self.llm_type_map[self.type](**self.config)


class NotificationHandler(ABC):

    async def login(self):
        pass

    async def logout(self):
        pass

    async def send_notification(self, feed: Feed, entry: FeedEntry):
        pass


