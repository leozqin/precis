import requests

from app.models import ContentRetrievalHandler


class RequestsContentRetriever(ContentRetrievalHandler):
    async def get_content(self, url: str) -> str:

        page = await requests.get(url)

        return page.text
