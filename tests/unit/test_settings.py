from enum import Enum

import pytest

from app.handlers import ContentRetrievalHandler, LLMHandler, NotificationHandler
from app.impls import load_storage_config
from app.settings import GlobalSettings


def test_global_settings():

    db = load_storage_config()
    settings = GlobalSettings(db=db)

    assert isinstance(settings.send_notification, bool)
    assert isinstance(settings.theme, Enum)
    assert isinstance(settings.refresh_interval, int)
    assert isinstance(settings.reading_speed, int)
    assert isinstance(settings.notification_handler_key, str)
    assert isinstance(settings.llm_handler_key, str)
    assert isinstance(settings.content_retrieval_handler_key, str)
    assert isinstance(settings.recent_hours, int)
    assert isinstance(settings.finished_onboarding, bool)
    assert isinstance(settings.notification_handler, NotificationHandler)
    assert isinstance(settings.llm_handler, LLMHandler)
    assert isinstance(settings.content_retrieval_handler, ContentRetrievalHandler)
