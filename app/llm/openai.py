from os import environ
from typing import ClassVar

from openai import OpenAI
from pydantic import BaseModel

from app.handlers import LLMHandler
from app.models import Feed, FeedEntry


class OpenAILLMHandler(LLMHandler, BaseModel):
    api_key: str = environ.get("OPENAI_API_KEY")
    model: str = "gpt-4o-mini"

    id: ClassVar[str] = "openai"

    def summarize(self, feed: Feed, entry: FeedEntry, mk: str):
        client = OpenAI(api_key=self.api_key)

        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": self.get_prompt(mk=mk)},
            ],
            model=self.model,
            n=1,
        )

        return completion.choices[0].message.content
