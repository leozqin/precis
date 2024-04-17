from app.db import DB
from app.summarization.engine import summarization_handler
from app.notification.engine import notification_handler
from app.content.engine import content_handler

db = DB()

def load_handlers():
    db.upsert_handler(summarization_handler)
    db.upsert_handler(notification_handler)
    db.upsert_handler(content_handler)