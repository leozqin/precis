import requests

from app.constants import USER_AGENT
from app.handlers import ContentRetrievalHandler
from app.models import EntryContent, FeedEntry


class RequestsContentRetriever(ContentRetrievalHandler):
    id = "requests"
    headers = {"User-Agent": USER_AGENT}

    async def get_html(self, url: str) -> str:
        try:
            page = requests.get(url, headers=self.headers)
            if page.text == "":
                return
            else:
                return page.text
        except:
            return
