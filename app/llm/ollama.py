from typing import Any, ClassVar, Mapping

from ollama import ChatResponse, Client, Message, Options
from pydantic import BaseModel

from app.handlers import LLMHandler
from app.models import Feed, FeedEntry


class OllamaLLMHandler(LLMHandler, BaseModel):
    base_url: str
    model: str
    system: str = None
    options: Mapping[str, Any]

    id: ClassVar[str] = "ollama"

    def _make_chat_call(self, system: str, prompt: str):
        client = Client(host=self.base_url)
        system = Message(role="system", content=system)
        prompt = Message(role="user", content=prompt)

        options = Options(**self.options)

        chat: ChatResponse = client.chat(
            model=self.model, messages=[system, prompt], options=options
        )

        return chat["message"]["content"]

    def summarize(self, feed: Feed, entry: FeedEntry, mk: str):
        system = self.system if self.system else self.system_prompt

        return self._make_chat_call(system=system, prompt=self.get_prompt(mk))
