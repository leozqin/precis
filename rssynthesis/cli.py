from argparse import ArgumentParser
from rssynthesis.models import Feed, FeedEntry
from calendar import timegm
import requests
from readabilipy import simple_json_from_html_string
from readability import Document
from html2text import HTML2Text
from sys import argv

from rssynthesis.db import DB
from playwright.sync_api import sync_playwright, Route

def block_aggressively(route: Route): 
	if (route.request.resource_type != "document"): 
		route.abort() 
	else: 
		route.continue_()
          
excluded_resource_types = ["stylesheet", "script", "image", "font"] 
def block_lightly(route): 
	if (route.request.resource_type in excluded_resource_types): 
		route.abort() 
	else: 
		route.continue_() 

def test_feed(url: str):
    feed = Feed(name="test", url=url)

    entries = feed.rss.entries[0:1]
    
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(reduced_motion="reduce", no_viewport=True)

        for entry in entries:
            print(entry.link)
            page.route("**/*", block_aggressively) 
            page.goto(entry.link)
            page.wait_for_load_state("domcontentloaded")

            content = page.content()
            print(content)

            # extract the main content
            document = simple_json_from_html_string(page.content())

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
