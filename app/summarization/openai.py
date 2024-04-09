from app.models import SummarizationHandler, Feed, FeedEntry
from pydantic import BaseModel
from openai import OpenAI

from os import environ


class OpenAISummarizationHandler(SummarizationHandler, BaseModel):
    api_key: str = environ.get("OPENAI_API_KEY")
    model: str = "gpt-3.5-turbo"

    def summarize(self, feed: Feed, entry: FeedEntry, mk: str):
        client = OpenAI(api_key=self.api_key)

        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": self.get_prompt(mk=mk)},
            ],
            model=self.model,
            n=1
        )

        return completion.choices[0].message.content
