from pydantic import BaseModel, ConfigDict
from ollama import Client, Message, ChatResponse, Options
from typing import Mapping, Any, ClassVar

from rssynthesis.models import SummarizationHandler, Feed, FeedEntry


class OllamaSummarizationHandler(SummarizationHandler, BaseModel):
    base_url: str
    model: str
    system: str = None
    options: Mapping[str, Any]

    supports_fallback_extractor: ClassVar[bool] = True

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

    def fallback_html_extractor(self, html: str):
        system = """
Your goal is to extract the main article body from this web page. Do not include ads, links, images, or navigation.
Only include the primary content of the page. Convert the article body to markdown. Add whitespace as needed to
improve readability and separate paragraphs from each other.
        """

        prompt = f"Extract the main article: {html}"

        return self._make_chat_call(system=system, prompt=prompt)