from json import dumps, loads
from os import makedirs
from shutil import rmtree
from uuid import uuid4

import mock
import pytest

from app.backend import PrecisBackend
from app.constants import DATA_DIR
from app.db import GlobalSettings
from app.errors import InvalidFeedException
from app.impls import load_storage_config
from app.llm.dummy import DummyLLMHandler
from app.models import Feed, FeedEntry


def dummy_feeds():
    feed_1 = Feed(name="Hello World", url="https://not-a-url.local")
    feed_2 = Feed(name="FizzBuzz", url="https://also-not-a-url.local")
    feed_3 = Feed(name="LinkedList", url="https://linked-list.local")

    return feed_1, feed_2, feed_3


def dummy_entries(id: str, count: int, url: str, offset: int = 0):
    _time = 1732670009 - (offset * 60)
    return [
        FeedEntry(
            feed_id=id,
            title="Hello World",
            url=f"{url}/{i}",
            published_at=_time,
            updated_at=_time,
            authors=["Albert Einstein", "J Robert Oppenheimer"],
        )
        for i in range(count)
    ]


@pytest.fixture
def setup():
    patch_dir = DATA_DIR.joinpath(uuid4().hex)
    makedirs(patch_dir, exist_ok=True)

    with mock.patch("app.impls.DATA_DIR", patch_dir):
        db = load_storage_config()
        backend = PrecisBackend(db)
        yield db, backend

    rmtree(patch_dir)


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
    feed_1, feed_2, feed_3 = dummy_feeds()

    db.upsert_feed(feed_1)
    db.upsert_feed(feed_2)
    db.upsert_feed(feed_3)

    feeds = backend.list_feeds()
    assert len(feeds) == 3
    for feed in feeds:
        assert feed
        assert feed["entry_count"] is False

    agg_feeds = backend.list_feeds(agg=True)
    assert len(agg_feeds) == 3
    for feed in agg_feeds:
        count = feed["entry_count"]
        assert isinstance(count, int)


def test_list_entries(setup):
    db, backend = setup
    feed_1, feed_2, feed_3 = dummy_feeds()
    feed_1_count = 5
    feed_2_count = 10
    feed_3_count = 15

    db.upsert_feed(feed_1)
    db.upsert_feed(feed_2)
    db.upsert_feed(feed_3)

    for entry in dummy_entries(id=feed_1.id, count=feed_1_count, url=feed_1.url):
        db.upsert_feed_entry(feed=feed_1, entry=entry)

    for entry in dummy_entries(
        id=feed_2.id, count=feed_2_count, url=feed_2.url, offset=30
    ):
        db.upsert_feed_entry(feed=feed_2, entry=entry)

    for entry in dummy_entries(
        id=feed_3.id, count=feed_3_count, url=feed_3.url, offset=90
    ):
        db.upsert_feed_entry(feed=feed_3, entry=entry)

    settings: GlobalSettings = db.get_settings()
    settings.recent_hours = 1
    db.upsert_settings(settings=settings)

    all = list(backend.list_entries())
    recent = list(backend.list_entries(recent=True, time=1732670009.0))
    single_feed = list(backend.list_entries(feed_id=feed_1.id))

    assert all
    assert recent
    assert single_feed
    assert len(all) > len(recent)

    assert len(single_feed) == feed_1_count
    assert len(all) == feed_1_count + feed_2_count + feed_3_count
    assert len(recent) == feed_1_count + feed_2_count


def test_get_handlers(setup):
    _, backend = setup

    handlers = backend.get_handlers()

    assert handlers
    for handler in handlers:
        assert handler


def test_get_handler_config(setup):
    db, backend = setup

    dummy_handler = DummyLLMHandler(temerity=10)
    db.upsert_handler(handler=dummy_handler)

    cfg = backend.get_handler_config(dummy_handler.id)

    assert cfg
    assert cfg["type"] == dummy_handler.id
    assert isinstance(cfg["config"], str)

    handler_config = cfg["config"]
    assert handler_config
    assert loads(handler_config)
    assert loads(handler_config)["temerity"] == 10

    no_cfg = backend.get_handler_config(handler="blah")
    assert no_cfg["type"] == "blah"
    assert not no_cfg["config"]


def test_get_handler_schema(setup):
    _, backend = setup

    schema = backend.get_handler_schema("dummy_llm")
    assert schema
    assert loads(schema)
    assert "temerity" in schema
    assert loads(schema)["properties"]["temerity"]


@pytest.mark.asyncio
async def test_get_settings(setup):
    db, backend = setup

    settings_in = GlobalSettings(db=db)
    settings_in.reading_speed = 900

    db.upsert_settings(settings=settings_in)

    settings = await backend.get_settings()
    assert settings
    assert isinstance(settings, dict)
    assert settings["reading_speed"] == 900


@pytest.mark.asyncio
async def test_get_feed_config(setup):
    db, backend = setup
    feed_1, feed_2, feed_3 = dummy_feeds()

    for feed in [feed_1, feed_2, feed_3]:
        db.upsert_feed(feed=feed)
        cfg = await backend.get_feed_config(id=feed.id)

        assert cfg
        assert cfg["id"] == feed.id
        assert cfg["url"] == feed.url
        assert cfg["name"] == feed.name


@pytest.mark.asyncio
async def test_update_feed(setup):
    db, backend = setup

    class ValidatedFeed(Feed):
        def validate(self):
            return True

    feed = ValidatedFeed(name="Hello World", url="https://hello-world.local")

    await backend.update_feed(feed=feed)
    settings: GlobalSettings = db.get_settings()
    assert settings.finished_onboarding


@pytest.mark.asyncio
async def test_update_feed_failed(setup):
    _, backend = setup
    feed, _, _ = dummy_feeds()

    with pytest.raises(InvalidFeedException):
        await backend.update_feed(feed=feed)


@pytest.mark.asyncio
async def test_update_settings(setup):
    db, backend = setup
    settings_in: GlobalSettings = db.get_settings()
    settings_in.recent_hours = 48
    await backend.update_settings(settings=settings_in)

    settings_out: GlobalSettings = db.get_settings()
    assert settings_out
    assert settings_out.recent_hours == 48


@pytest.mark.asyncio
async def test_update_handler(setup):
    db, backend = setup
    db.upsert_handler(handler=DummyLLMHandler())

    handler_before: DummyLLMHandler = db.get_handler(id="dummy_llm")
    assert handler_before.temerity == 5

    config_in = dumps({"temerity": 100})
    await backend.update_handler(handler="dummy_llm", config=config_in)

    handler_after: DummyLLMHandler = db.get_handler(id="dummy_llm")
    assert handler_after.temerity == 100


@pytest.mark.asyncio
async def test_delete_feed(setup):
    db, backend = setup
    feed_1, feed_2, feed_3 = dummy_feeds()
    for feed in [feed_1, feed_2, feed_3]:
        db.upsert_feed(feed=feed)
        for entry in dummy_entries(id=feed.id, count=5, url=feed.url):
            db.upsert_feed_entry(feed=feed, entry=entry)

    feed = feed_1
    await backend.delete_feed(feed_id=feed.id)

    assert len(db.get_feeds()) == 2
    assert feed.id not in [i.id for i in db.get_feeds()]

    assert not db.get_entries(feed=feed)
