from simplematrixbotlib import Bot, Creds
from os import environ
from logging import getLogger
from rssynthesis.models import Feed, FeedEntry

creds = Creds(
    homeserver=environ["MATRIX_HOMESERVER_URL"],
    username=environ["MATRIX_BOT_USERNAME"],
    password=environ["MATRIX_BOT_PASSWORD"],
)

bot = Bot(creds=creds)
room_id = environ["MATRIX_BOT_ROOM_ID"]

logger = getLogger("uvicorn.error")

def _make_read_link(entry: FeedEntry):
    base_url = environ["RSS_BASE_URL"]
    return f"{base_url}/read/{entry.id}"


async def send_notification(feed: Feed, entry: FeedEntry):
    msg = f"{feed.name}: [{entry.title}]({_make_read_link(entry)})"
    logger.info(f"Sending notification to {room_id}")
    await bot.api.send_markdown_message(room_id=room_id, message=msg)