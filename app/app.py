from contextlib import asynccontextmanager
from json import loads
from logging import getLogger
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, Form, status
from fastapi.requests import Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi_utils.tasks import repeat_every

from app.backend import (
    get_entry_content,
    get_feed_config,
    get_handler_config,
    get_handler_schema,
    get_handlers,
    get_settings,
    list_entries,
    list_feeds,
)
from app.backend import update_feed as bk_update_feed
from app.backend import update_handler as bk_update_handler
from app.backend import update_settings as bk_update_settings
from app.content.engine import ContentRetrievalEngine
from app.handlers import load_handlers
from app.models import Feed, Themes
from app.notification.engine import NotificationEngine, notification_handler
from app.rss import check_feeds, load_feeds
from app.settings import GlobalSettings
from app.summarization.engine import SummarizationEngine

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
async def root(request: Request):

    settings = await get_settings()

    if settings.get("finished_onboarding"):

        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "settings": await get_settings(),
                "feeds": list_feeds(agg=True),
            },
        )

    else:

        return RedirectResponse("/onboarding/")


@app.get("/onboarding/", response_class=HTMLResponse)
async def onboarding(request: Request):

    return templates.TemplateResponse(
        "onboarding.html",
        {
            "request": request,
            "settings": await get_settings(),
        },
    )


@app.get("/list-entries/{feed_id}", response_class=HTMLResponse)
async def list_entries_by_feed(feed_id: str, request: Request):

    return templates.TemplateResponse(
        "entries.html",
        {
            "request": request,
            "settings": await get_settings(),
            "entries": list(list_entries(feed_id=feed_id)),
            "feed": await get_feed_config(id=feed_id),
        },
    )


@app.get("/list-entries/", response_class=HTMLResponse)
async def list_all_entries(request: Request):

    return templates.TemplateResponse(
        "entries.html",
        {
            "request": request,
            "settings": await get_settings(),
            "entries": list(list_entries(feed_id=None)),
            "feed": {},
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
            "settings": await get_settings(),
        },
    )


@app.get("/settings/", response_class=HTMLResponse)
async def settings(request: Request):

    return templates.TemplateResponse(
        "settings.html",
        {
            "request": request,
            "themes": Themes._member_names_,
            "content_handler_choices": list(ContentRetrievalEngine.handlers.keys()),
            "summarization_handler_choices": list(SummarizationEngine.handlers.keys()),
            "notification_handler_choices": list(NotificationEngine.handlers.keys()),
            "settings": await get_settings(),
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
            "schema": get_handler_schema(handler=handler),
            "settings": await get_settings(),
        },
    )


@app.post("/api/update_handler/", status_code=status.HTTP_200_OK)
async def update_handler(
    handler: Annotated[str, Form()], config: Annotated[str, Form()], request: Request
):

    try:
        await bk_update_handler(handler=handler, config=config)

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
                "settings": await get_settings(),
            },
        )


@app.post("/api/update_settings/", status_code=status.HTTP_200_OK)
async def update_settings(
    theme: Annotated[str, Form()],
    refresh_interval: Annotated[int, Form()],
    request: Request,
    send_notification: Annotated[bool, Form()] = False,
):
    try:
        settings = GlobalSettings(
            send_notification=send_notification,
            theme=theme,
            refresh_interval=refresh_interval,
        )

        await bk_update_settings(settings=settings)

        return templates.TemplateResponse(
            "settings.html",
            {
                "request": request,
                "themes": Themes._member_names_,
                "settings": await get_settings(),
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
                "settings": await get_settings(),
                "notification": get_handlers(),
                "update_exception": e,
            },
        )


@app.post("/api/update_feed/", status_code=status.HTTP_200_OK)
async def update_feed(
    name: Annotated[str, Form()],
    url: Annotated[str, Form()],
    category: Annotated[str, Form()],
    request: Request,
    notify_destination: Annotated[str, Form()] = None,
    notify: Annotated[bool, Form()] = False,
    preview_only: Annotated[bool, Form()] = False,
    onboarding_flow: Annotated[bool, Form()] = False,
):
    try:
        feed = Feed(
            name=name,
            url=url,
            category=category,
            notify=notify,
            notify_destination=notify_destination,
            preview_only=preview_only,
        )

        await bk_update_feed(feed=feed, onboarding_flow=onboarding_flow)

        return RedirectResponse(
            request.url_for("feed_settings", id=feed.id).include_query_params(
                update_status=True
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )
    except Exception as e:
        return RedirectResponse(
            request.url_for("feed_settings", id=feed.id).include_query_params(
                update_exception=e
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )


@app.get("/feeds/", response_class=HTMLResponse)
async def feeds(request: Request):

    return templates.TemplateResponse(
        "feeds.html",
        {
            "request": request,
            "settings": await get_settings(),
            "feeds": list_feeds(agg=False),
        },
    )


@app.get("/feeds/{id}", response_class=HTMLResponse)
async def feed_settings(
    request: Request, id: str, update_status: bool = False, update_exception: str = None
):

    return templates.TemplateResponse(
        "feed_config.html",
        {
            "request": request,
            "settings": await get_settings(),
            "feed": await get_feed_config(id=id),
            "update_status": update_status,
            "update_exception": update_exception,
        },
    )


@app.get("/feeds/new/", response_class=HTMLResponse)
async def new_feed(request: Request, onboarding_flow: bool = False):

    return templates.TemplateResponse(
        "feed_config.html",
        {
            "request": request,
            "settings": await get_settings(),
            "feed": {},
            "onboarding_flow": onboarding_flow,
        },
    )
