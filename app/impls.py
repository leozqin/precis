from logging import getLogger
from os import environ
from typing import Type, Union

from app.content.playwright import PlaywrightContentRetriever
from app.content.requests import RequestsContentRetriever
from app.db import StorageHandler
from app.llm.dummy import DummyLLMHandler
from app.llm.null import NullLLMHandler
from app.llm.ollama import OllamaLLMHandler
from app.llm.openai import OpenAILLMHandler
from app.notification.jira import JiraNotificationHandler
from app.notification.matrix import MatrixNotificationHandler
from app.notification.ntfy import NtfyNotificationHandler
from app.notification.null import NullNotificationHandler
from app.notification.slack import SlackNotificationHandler
from app.storage.hybrid import HybridLMDBOfflineStorageHandler
from app.storage.lmdb import LMDBStorageHandler
from app.storage.tinydb import TinyDBStorageHandler

logger = getLogger("uvicorn.error")

storage_handlers = {
    "tinydb": TinyDBStorageHandler,
    "lmdb": LMDBStorageHandler,
    "hybrid": HybridLMDBOfflineStorageHandler,
}

notification_handlers = {
    "matrix": MatrixNotificationHandler,
    "null_notification": NullNotificationHandler,
    "slack": SlackNotificationHandler,
    "jira": JiraNotificationHandler,
    "ntfy": NtfyNotificationHandler,
}

content_retrieval_handlers = {
    "requests": RequestsContentRetriever,
    "playwright": PlaywrightContentRetriever,
}

llm_handlers = {
    NullLLMHandler.id: NullLLMHandler,
    OllamaLLMHandler.id: OllamaLLMHandler,
    OpenAILLMHandler.id: OpenAILLMHandler,
    DummyLLMHandler.id: DummyLLMHandler,
    # redirect null summarization handler to null llm
    # TODO: Deprecate
    "null_summarization": NullLLMHandler,
}


class ImplMixin:
    handler_map = {
        **llm_handlers,
        **notification_handlers,
        **content_retrieval_handlers,
    }

    engine_map = {
        "llm": llm_handlers,
        "notification": notification_handlers,
        "content": content_retrieval_handlers,
    }

    handler_type_map = {
        **{k: "llm" for k in llm_handlers.keys()},
        **{k: "notification" for k in notification_handlers.keys()},
        **{k: "content" for k in content_retrieval_handlers.keys()},
    }


def load_storage_config() -> Type[
    Union[ImplMixin, Type[StorageHandler]],
]:

    config_type = environ.get("PRECIS_STORAGE_HANDLER", "tinydb")
    handler_type = storage_handlers.get(config_type)
    handler = handler_type()

    # for the purpose of managing settings, the db handler needs to know about
    # implementations of other handlers. Here, we modify the signature of the chosen
    # handler to include the other handler impls. Doing it this way avoids creating a
    # circular dependency
    handler_cls_name = handler.__class__.__name__
    handler.__class__ = type(handler_cls_name, (handler_type, ImplMixin), {})

    logger.info(f"loading storage handler of type {config_type}")

    return handler
