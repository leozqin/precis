from argparse import ArgumentParser
from rssynthesis.models import Feed, FeedEntry
from calendar import timegm
import requests
from readabilipy import simple_json_from_html_string
from readability import Document
from html2text import HTML2Text
from sys import argv

from rssynthesis.db import DB


def test_feed(url: str):
    feed = Feed(name="test", url=url)

    entries = feed.rss.entries[0:5]

    for entry in entries:

        raw_content = requests.get(entry.id)
        # extract the main content
        document = simple_json_from_html_string(raw_content.text)

        # clean it up more
        cleaned_document = Document(input=document["content"])

        converter = HTML2Text()
        converter.ignore_images = True
        converter.ignore_links = True

        content = converter.handle(cleaned_document.summary(html_partial=True))

        yield content


def cli():
    verb = argv[1]

    if verb == "test-feed":
        feed_url = argv[2]
        entries = list(test_feed(feed_url))

        for entry in entries:
            print(entry)
