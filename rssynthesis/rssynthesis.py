from pathlib import Path
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi_utils.tasks import repeat_every

from contextlib import asynccontextmanager
from logging import getLogger
from tinydb import TinyDB

from rssynthesis.rss import load_feeds, check_feeds
from rssynthesis.ui import list_feeds

logger = getLogger("uvicorn.error")
base_path = Path(__file__).parent

db_path = Path(base_path, "../", "db.json").resolve()
db = TinyDB(db_path)

config_path = Path(base_path, "../", "feeds.yml").resolve()

templates = Jinja2Templates(directory=Path(base_path, "templates").resolve())


@repeat_every(seconds=60, logger=logger)
async def poll_feeds():
    logger.info("Checking feeds for updates")
    check_feeds()


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_feeds(config_path=config_path)
    await poll_feeds()

    yield


app = FastAPI(lifespan=lifespan, title="RSSynthesis", openapi_url="/openapi.json")


@app.get("/")
def root():

    return templates.TemplateResponse(
        "index.html", {"request": {}, "feeds": list_feeds()}
    )
