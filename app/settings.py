from app.models import (
    ContentRetrievalHandler,
    GlobalSettingsSchema,
    NotificationHandler,
    SummarizationHandler,
)
from app.storage.engine import storage_handler as db


class GlobalSettings(GlobalSettingsSchema):
    @property
    def notification_handler(self) -> NotificationHandler:
        return db.get_handler(id=self.notification_handler_key)

    @property
    def summarization_handler(self) -> SummarizationHandler:
        return db.get_handler(id=self.summarization_handler_key)

    @property
    def content_retrieval_handler(self) -> ContentRetrievalHandler:
        return db.get_handler(id=self.content_retrieval_handler_key)
