from os import makedirs
from shutil import rmtree

import pytest

from app.backend import PrecisBackend
from app.constants import DATA_DIR
from app.db import GlobalSettings
from app.impls import load_storage_config
from app.models import Feed, FeedEntry


def dummy_feeds():
    feed_1 = Feed(name="Hello World", url="https://not-a-url.local")

    feed_2 = Feed(name="FizzBuzz", url="https://also-not-a-url.local")

    return feed_1, feed_2


def dummy_entries(id: str, count: int):
    return [
        FeedEntry(
            feed_id=id,
            title="Hello World",
            url=f"https://test_feed.local/{i}",
            published_at=1732670009,
            updated_at=1732670009,
            authors=["Albert Einstein", "J Robert Oppenheimer"],
        )
        for i in range(count)
    ]


@pytest.fixture
def setup():
    makedirs(DATA_DIR, exist_ok=True)

    db = load_storage_config()
    backend = PrecisBackend(db)
    yield db, backend

    rmtree(DATA_DIR)


def test_format_time():
    int_time = 1732670009
    str_time = PrecisBackend._format_time(int_time)

    assert str_time == "2024-11-26 05:13 pm"


def test_health_check(setup):
    _, backend = setup
    hc = backend.health_check()

    assert hc.status == "OK"


def test_about(setup):
    _, backend = setup

    assert backend.about()


def test_list_feeds(setup):
    db, backend = setup
    feed_1, feed_2 = dummy_feeds()

    db.upsert_feed(feed_1)
    db.upsert_feed(feed_2)

    feeds = backend.list_feeds()
    assert len(feeds) == 2
    for feed in feeds:
        assert feed
        assert feed["entry_count"] is False

    agg_feeds = backend.list_feeds(agg=True)
    assert len(agg_feeds) == 2
    for feed in agg_feeds:
        count = feed["entry_count"]
        assert isinstance(count, int)


def test_list_entries(setup):
    db, backend = setup
    feed_1, feed_2 = dummy_feeds()
    feed_1_count = 5
    feed_2_count = 10

    db.upsert_feed(feed_1)
    db.upsert_feed(feed_2)

    for entry in dummy_entries(id=feed_1.id, count=feed_1_count):
        db.upsert_feed_entry(feed=feed_1, entry=entry)

    for entry in dummy_entries(id=feed_2.id, count=feed_2_count):
        db.upsert_feed_entry(feed=feed_2, entry=entry)

    settings: GlobalSettings = db.get_settings()
    settings.recent_hours = 1
    db.upsert_settings(settings=settings)
