import pytest

from app.db import StorageHandler
from app.handlers import ContentRetrievalHandler, LLMHandler, NotificationHandler
from app.impls import (
    content_retrieval_handlers,
    llm_handlers,
    load_storage_config,
    notification_handlers,
    storage_handlers,
)


@pytest.mark.parametrize(
    "hmap",
    [
        {"type": StorageHandler, "handlers": storage_handlers},
        {"type": NotificationHandler, "handlers": notification_handlers},
        {"type": ContentRetrievalHandler, "handlers": content_retrieval_handlers},
        {"type": LLMHandler, "handlers": llm_handlers},
    ],
)
def test_handlers_map(hmap):
    for key, handler in hmap["handlers"].items():
        assert isinstance(key, str)
        assert issubclass(handler, hmap["type"])


def test_load_storage_config():
    db = load_storage_config()

    assert isinstance(db, StorageHandler)
    assert db.handler_map
    assert db.engine_map
    assert db.handler_type_map
