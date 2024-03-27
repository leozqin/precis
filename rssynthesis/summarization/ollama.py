from pydantic import BaseModel, ConfigDict
from ollama import Client, Message, ChatResponse, Options
from typing import Mapping, Any, ClassVar

from rssynthesis.models import SummarizationHandler, Feed, FeedEntry


class OllamaSummarizationHandler(SummarizationHandler, BaseModel):
    base_url: str
    model: str
    system: str
    options: Mapping[str, Any]

    def summarize(self, feed: Feed, entry: FeedEntry, mk: str):
        client = Client(host=self.base_url)

        system = Message(role="system", content=self.system)
        prompt = Message(role="user", content=self.get_prompt(mk))

        options = Options(**self.options)
        
        chat: ChatResponse = client.chat(
            model=self.model,
            messages=[system, prompt],
            options=options
        )

        return chat["message"]["content"]