import requests

from app.handlers import ContentRetrievalHandler


class RequestsContentRetriever(ContentRetrievalHandler):
    id = "requests"

    async def get_content(self, url: str) -> str:

        page = await requests.get(url)

        return page.text
