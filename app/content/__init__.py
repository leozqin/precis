from enum import Enum

from app.content.playwright import PlaywrightContentRetriever
from app.content.requests import RequestsContentRetriever

content_retrieval_handlers = {
    "requests": RequestsContentRetriever,
    "playwright": PlaywrightContentRetriever,
}
