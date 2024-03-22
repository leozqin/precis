from pathlib import Path
from fastapi import FastAPI
from fastapi_utils.tasks import repeat_every

from contextlib import asynccontextmanager
from logging import getLogger
from tinydb import TinyDB

from rssynthesis.rss import load_feeds, check_feeds

logger = getLogger("uvicorn.error")

db_path = Path(Path(__file__).parent, "../", "db.json").resolve()
db = TinyDB(db_path)

config_path = Path(Path(__file__).parent, "../", "config.yml").resolve()


@repeat_every(seconds=60, logger=logger)
async def poll_feeds():
    logger.info("Checking feeds for updates")
    check_feeds()


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_feeds(config_path=config_path)
    await poll_feeds()

    yield


app = FastAPI(lifespan=lifespan)

