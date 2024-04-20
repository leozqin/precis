from app.storage.engine import storage_handler as db
from app.summarization.engine import summarization_handler
from app.notification.engine import notification_handler
from app.content.engine import content_handler

def load_handlers():
    db.upsert_handler(summarization_handler)
    db.upsert_handler(notification_handler)
    db.upsert_handler(content_handler)