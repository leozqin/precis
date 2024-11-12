import pytest

from app.models import EntryContent, Feed, FeedEntry


def test_feed():
    feed = Feed(
        name="Leo's Website",
        category="blog",
        url="https://www.leozqin.me/index.xml",
        notify=True,
        notify_destination="news",
    )

    assert feed
    assert feed.id == "5524eb0fe9f75845720c8744410ad865"
    assert not feed.rss.get("bozo")
    assert feed.validate()


def test_feed_failed():
    feed = Feed(
        name="Bad Website",
        category="blog",
        url="https://nothing.notatld",
        notify=True,
        notify_destination="news",
    )

    assert feed
    assert feed.id == "2e03fc9169f7f98b97a104367ba45008"
    assert feed.rss.get("bozo")
    assert not feed.validate()


def test_feed_entry():
    entry = FeedEntry(
        feed_id="abc123",
        title="Hello World",
        url="http://nothing.notatld",
        published_at=1,
        updated_at=2,
    )

    assert entry
    assert entry.id == "8a5faf510cc4194205442a2734fd6f2f"


def test_entry_content():
    content = EntryContent(
        url="http://nothing.notatld", content="Hello World", summary="Just World"
    )

    assert content
    assert content.id == "8a5faf510cc4194205442a2734fd6f2f"
