from rssynthesis.models import ContentRetriever
import requests

class RequestsContentRetriever(ContentRetriever):

    async def get_content(self, url: str) -> str:

        page = await requests.get(url)

        return page.text
