from contextlib import asynccontextmanager
from logging import getLogger
from pathlib import Path
from typing import Annotated
from json import loads

from fastapi import FastAPI, status, HTTPException, Form
from fastapi.requests import Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi_utils.tasks import repeat_every

from app.notification.engine import notification_handler
from app.rss import check_feeds, load_feeds
from app.handlers import load_handlers
from app.ui import (
    get_entry_content,
    list_entries,
    list_feeds,
    get_handlers,
    get_handler_config,
    get_settings,
)
from app.db import DB
from app.models import GlobalSettings, Themes

logger = getLogger("uvicorn.error")
base_path = Path(__file__).parent

templates = Jinja2Templates(directory=Path(base_path, "templates").resolve())


@repeat_every(seconds=60 * 5, logger=logger)
async def poll_feeds():
    logger.info("Checking feeds for updates")
    await check_feeds()


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_feeds()
    load_handlers()

    await notification_handler.login()
    await poll_feeds()

    yield

    await notification_handler.logout()


app = FastAPI(lifespan=lifespan, title="Precis", openapi_url="/openapi.json")

app.mount(
    "/static",
    StaticFiles(directory=Path(Path(__file__).parent, "static")),
    name="static",
)


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    path = Path(Path(__file__).parent, "static", "icons", "favicon.ico")
    return FileResponse(path)


@app.get("/", response_class=HTMLResponse)
def root(request: Request):

    return templates.TemplateResponse(
        "index.html",
        {"request": request, "settings": get_settings(), "feeds": list_feeds()},
    )


@app.get("/list-entries/{feed_id}", response_class=HTMLResponse)
def list_entries_by_feed(feed_id: str, request: Request):

    return templates.TemplateResponse(
        "entries.html",
        {
            "request": request,
            "settings": get_settings(),
            "entries": list(list_entries(feed_id=feed_id)),
        },
    )


@app.get("/list-entries/", response_class=HTMLResponse)
def list_all_entries(request: Request):

    return templates.TemplateResponse(
        "entries.html",
        {
            "request": request,
            "settings": get_settings(),
            "entries": list(list_entries(feed_id=None)),
        },
    )


@app.get("/read/{feed_entry_id}", response_class=HTMLResponse)
async def read(request: Request, feed_entry_id: str, redrive: bool = False):

    return templates.TemplateResponse(
        "read.html",
        {
            "request": request,
            "content": await get_entry_content(
                feed_entry_id=feed_entry_id, redrive=redrive
            ),
            "settings": get_settings(),
        },
    )


@app.get("/settings/", response_class=HTMLResponse)
async def settings(request: Request):

    return templates.TemplateResponse(
        "settings.html",
        {
            "request": request,
            "themes": Themes._member_names_,
            "settings": get_settings(),
            "notification": get_handlers(),
        },
    )


@app.get("/settings/{handler}", response_class=HTMLResponse)
async def handler_settings(request: Request, handler: str):

    return templates.TemplateResponse(
        "handler_config.html",
        {
            "request": request,
            "handler": get_handler_config(handler=handler),
            "settings": get_settings(),
        },
    )


@app.post("/api/update_handler/", status_code=status.HTTP_200_OK)
async def update_handler(
    handler: Annotated[str, Form()], config: Annotated[str, Form()], request: Request
):
    db = DB()

    try:

        config_dict = loads(config)
        handler_obj = db._make_handler_obj(id=handler, config=config_dict)
        db.upsert_handler(handler=handler_obj)

        return templates.TemplateResponse(
            "handler_config.html",
            {
                "request": request,
                "handler": get_handler_config(handler=handler),
                "update_status": True,
                "settings": get_settings(),
            },
        )
    except Exception as e:

        return templates.TemplateResponse(
            "handler_config.html",
            {
                "request": request,
                "handler": get_handler_config(handler=handler),
                "update_exception": e,
                "settings": get_settings(),
            },
        )


@app.post("/api/update_settings/", status_code=status.HTTP_200_OK)
async def update_settings(
    send_notification: Annotated[bool, Form()],
    theme: Annotated[str, Form()],
    refresh_interval: Annotated[int, Form()],
    request: Request,
):
    db = DB()
    try:
        settings = GlobalSettings(
            send_notification=send_notification,
            theme=theme,
            refresh_interval=refresh_interval,
        )

        db.upsert_settings(settings=settings)
        return templates.TemplateResponse(
            "settings.html",
            {
                "request": request,
                "themes": Themes._member_names_,
                "settings": get_settings(),
                "notification": get_handlers(),
                "update_status": True,
            },
        )
    except Exception as e:

        return templates.TemplateResponse(
            "settings.html",
            {
                "request": request,
                "themes": Themes._member_names_,
                "settings": get_settings(),
                "notification": get_handlers(),
                "update_exception": e,
            },
        )
