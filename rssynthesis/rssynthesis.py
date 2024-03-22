from sys import argv
from yaml import load, SafeLoader
from pathlib import Path
from fastapi import FastAPI

from contextlib import asynccontextmanager
from logging import getLogger
from tinydb import TinyDB

from rssynthesis.rss import load_feeds, check_feeds

logger = getLogger("uvicorn.error")

db_path = Path(Path(__file__).parent, "../", "db.json").resolve()
db = TinyDB(db_path)

config_path = Path(Path(__file__).parent, "../", "config.yml").resolve()


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_feeds(config_path=config_path)
    check_feeds()

    yield


app = FastAPI(lifespan=lifespan)
