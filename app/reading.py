from readabilipy import simple_json_from_html_string
from readability import Document
from html2text import HTML2Text
from markdown2 import markdown

from app.models import Feed, FeedEntry
from app.settings import GlobalSettings


class ReadingMethodsMixIn:

    @staticmethod
    async def get_entry_html(url: str, settings: GlobalSettings) -> str:
        return await settings.content_retrieval_handler.get_content(url)

    @staticmethod
    def get_main_content(content: str) -> str:
        md = simple_json_from_html_string(html=content)

        cleaned_document = Document(input=md["content"])

        converter = HTML2Text()
        converter.ignore_images = True
        converter.ignore_links = True

        return markdown(converter.handle(cleaned_document.summary(html_partial=True)))

    @staticmethod
    def summarize(
        feed: Feed, entry: FeedEntry, mk: str, settings: GlobalSettings
    ) -> str:

        summary = settings.summarization_handler.summarize(
            feed=feed, entry=entry, mk=mk
        )

        return markdown(summary)