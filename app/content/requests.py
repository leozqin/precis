import requests

from app.models import ContentRetriever


class RequestsContentRetriever(ContentRetriever):
    async def get_content(self, url: str) -> str:

        page = await requests.get(url)

        return page.text
