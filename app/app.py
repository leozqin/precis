from contextlib import asynccontextmanager
from itertools import chain
from logging import getLogger
from pathlib import Path
from typing import Annotated, Mapping, Sequence

from fastapi import FastAPI, Form, UploadFile, status
from fastapi.requests import Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi_utils.tasks import repeat_every

from app.backend import PrecisBackend
from app.context import GlobalSettings, Themes
from app.logging import HealthCheckFilter
from app.models import Feed, HealthCheck
from app.rss import PrecisRSS
from app.storage.engine import load_storage_config

JSON = "application/json"

logger = getLogger("uvicorn.error")
base_path = Path(__file__).parent

templates = Jinja2Templates(directory=Path(base_path, "templates").resolve())

storage_handler = load_storage_config()

bk = PrecisBackend(db=storage_handler)
rss = PrecisRSS(db=storage_handler)

logger.addFilter(HealthCheckFilter())
getLogger("uvicorn.access").addFilter(HealthCheckFilter())

p_settings: GlobalSettings = storage_handler.get_settings()


@repeat_every(seconds=60 * p_settings.refresh_interval, logger=logger)
async def poll_feeds():
    logger.info("Checking feeds for updates")
    await rss.check_feeds()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await poll_feeds()

    yield


app = FastAPI(lifespan=lifespan, title="Precis", openapi_url="/openapi.json")

app.mount(
    "/static",
    StaticFiles(directory=Path(Path(__file__).parent, "static")),
    name="static",
)

app.mount(
    "/assets",
    StaticFiles(directory=Path(Path(__file__).parent, "assets")),
    name="assets",
)


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    path = Path(Path(__file__).parent, "static", "icons", "favicon.ico")
    return FileResponse(path)


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):

    settings = await bk.get_settings()

    if settings.get("finished_onboarding"):

        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "settings": await bk.get_settings(),
                "feeds": bk.list_feeds(agg=True),
            },
        )

    else:

        return RedirectResponse("/onboarding/")


@app.get("/about")
async def about(
    request: Request, update_status: bool = False, update_exception: str = None
):
    response = {
        "settings": await bk.get_settings(),
        "update_status": update_status,
        "update_exception": update_exception,
        **bk.about(),
    }

    if request.headers.get("accept") == JSON:
        return JSONResponse(content=response, media_type=JSON)
    else:
        return templates.TemplateResponse(
            "about.html", {"request": request, **response}
        )


@app.get("/health", response_model=HealthCheck)
async def health_check(request: Request) -> HealthCheck:

    return bk.health_check()


@app.get("/onboarding/")
async def onboarding(request: Request):
    response = {"settings": await bk.get_settings()}

    if request.headers.get("accept") == JSON:
        return JSONResponse(content=response, media_type=JSON)
    else:
        return templates.TemplateResponse(
            "onboarding.html",
            {"request": request, **response},
        )


@app.get("/list-entries/{feed_id}", response_class=HTMLResponse)
async def list_entries_by_feed(
    feed_id: str, request: Request, refresh_requested: bool = False
):
    response = {
        "settings": await bk.get_settings(),
        "entries": list(bk.list_entries(feed_id=feed_id)),
        "feed": await bk.get_feed_config(id=feed_id),
        "refresh_requested": refresh_requested,
    }

    if request.headers.get("accept") == JSON:
        return JSONResponse(content=response, media_type=JSON)
    else:
        return templates.TemplateResponse(
            "entries.html",
            {"request": request, **response},
        )


@app.get("/recent/", response_class=HTMLResponse)
async def list_recent_feed_entries(request: Request, refresh_requested: bool = False):
    response = {
        "settings": await bk.get_settings(),
        "entries": list(bk.list_entries(feed_id=None, recent=True)),
        "refresh_requested": refresh_requested,
        "recent": True,
    }

    if request.headers.get("accept") == JSON:
        return JSONResponse(content=response, media_type=JSON)
    else:
        return templates.TemplateResponse(
            "entries.html",
            {"request": request, **response},
        )


@app.get("/read/{feed_entry_id}", response_class=HTMLResponse)
async def read(request: Request, feed_entry_id: str, redrive: bool = False):
    response = {
        "content": await bk.get_entry_content(
            feed_entry_id=feed_entry_id, redrive=redrive
        ),
        "settings": await bk.get_settings(),
    }

    if request.headers.get("accept") == JSON:
        return JSONResponse(content=response, media_type=JSON)
    else:
        return templates.TemplateResponse(
            "read.html",
            {"request": request, **response},
        )


@app.get("/settings/", response_class=HTMLResponse)
async def settings(
    request: Request, update_status: bool = False, update_exception: str = None
):
    response = {
        "themes": Themes._member_names_,
        "content_handler_choices": await bk.list_content_handler_choices(),
        "summarization_handler_choices": await bk.list_summarization_handler_choices(),
        "notification_handler_choices": await bk.list_notification_handler_choices(),
        "settings": await bk.get_settings(),
        "notification": bk.get_handlers(),
        "update_status": update_status,
        "update_exception": update_exception,
    }

    if request.headers.get("accept") == JSON:
        return JSONResponse(content=response, media_type=JSON)
    else:
        return templates.TemplateResponse(
            "settings.html", {"request": request, **response}
        )


@app.get("/settings/{handler}", response_class=HTMLResponse)
async def handler_settings(
    request: Request,
    handler: str,
    update_status: bool = False,
    update_exception: str = None,
):
    response = {
        "handler": bk.get_handler_config(handler=handler),
        "schema": bk.get_handler_schema(handler=handler),
        "settings": await bk.get_settings(),
        "update_status": update_status,
        "update_exception": update_exception,
    }

    if request.headers.get("accept") == JSON:
        return JSONResponse(content=response, media_type=JSON)
    else:
        return templates.TemplateResponse(
            "handler_config.html", {"request": request, **response}
        )


@app.post("/api/update_handler/", status_code=status.HTTP_200_OK)
async def update_handler(
    handler: Annotated[str, Form()], config: Annotated[str, Form()], request: Request
):

    try:
        await bk.update_handler(handler=handler, config=config)

        return RedirectResponse(
            request.url_for("handler_settings", handler=handler).include_query_params(
                update_status=True, handler=handler
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )
    except Exception as e:

        return RedirectResponse(
            request.url_for("handler_settings", handler=handler).include_query_params(
                update_exception=e
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )


@app.get("/api/refresh_feed/{feed_id}", status_code=status.HTTP_200_OK)
async def refresh_feed(feed_id: str, request: Request):

    await rss.check_feed_by_id(id=feed_id)

    return RedirectResponse(
        request.url_for("list_entries_by_feed", feed_id=feed_id).include_query_params(
            refresh_requested=True
        ),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@app.get("/api/delete_feed/{feed_id}", status_code=status.HTTP_200_OK)
async def delete_feed(feed_id: str, request: Request):

    await bk.delete_feed(feed_id=feed_id)

    return RedirectResponse(
        request.url_for("feeds"),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@app.post("/api/update_settings/", status_code=status.HTTP_200_OK)
async def update_settings(
    theme: Annotated[str, Form()],
    refresh_interval: Annotated[int, Form()],
    request: Request,
    send_notification: Annotated[bool, Form()] = False,
    notification: Annotated[str, Form()] = None,
    content: Annotated[str, Form()] = None,
    summarization: Annotated[str, Form()] = None,
    reading_speed: Annotated[int, Form()] = None,
    finished_onboarding: Annotated[bool, Form()] = False,
    recent_hours: Annotated[int, Form()] = None,
):
    try:
        settings = GlobalSettings(
            send_notification=send_notification,
            theme=theme,
            refresh_interval=refresh_interval,
            notification_handler_key=notification,
            summarization_handler_key=summarization,
            content_retrieval_handler_key=content,
            reading_speed=reading_speed,
            finished_onboarding=finished_onboarding,
            recent_hours=recent_hours,
            db=storage_handler,
        )

        logger.info(settings)

        await bk.update_settings(settings=settings)

        return RedirectResponse(
            request.url_for("settings").include_query_params(update_status=True),
            status_code=status.HTTP_303_SEE_OTHER,
        )
    except Exception as e:

        return RedirectResponse(
            request.url_for("settings").include_query_params(update_exception=e),
            status_code=status.HTTP_303_SEE_OTHER,
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
    refresh_enabled: Annotated[bool, Form()] = False,
):
    try:
        feed = Feed(
            name=name,
            url=url,
            category=category,
            notify=notify,
            notify_destination=notify_destination,
            preview_only=preview_only,
            refresh_enabled=refresh_enabled,
        )

        await bk.update_feed(feed=feed)

        return RedirectResponse(
            request.url_for("feed_settings", id=feed.id).include_query_params(
                update_status=True
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )
    except Exception as e:
        if feed.validate():
            return RedirectResponse(
                request.url_for("feed_settings", id=feed.id).include_query_params(
                    update_exception=e
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )
        else:
            return RedirectResponse(
                request.url_for("new_feed").include_query_params(update_exception=e),
                status_code=status.HTTP_303_SEE_OTHER,
            )


@app.get("/api/export_opml/", status_code=status.HTTP_200_OK)
async def export_opml(request: Request):

    write_path, file_name = await rss.feeds_to_opml()

    return FileResponse(path=write_path, filename=file_name)


@app.get("/api/backup/", status_code=status.HTTP_200_OK)
async def backup(request: Request):

    write_path, file_name = await rss.backup()

    return FileResponse(path=write_path, filename=file_name)


@app.post("/api/restore/", status_code=status.HTTP_200_OK)
async def restore(request: Request, file: UploadFile):

    try:
        await rss.restore(file=file.file)

        return RedirectResponse(
            request.url_for("about").include_query_params(update_status=True),
            status_code=status.HTTP_303_SEE_OTHER,
        )
    except Exception as e:
        return RedirectResponse(
            request.url_for("about").include_query_params(update_exception=e),
            status_code=status.HTTP_303_SEE_OTHER,
        )


@app.post("/api/import_opml/", status_code=status.HTTP_200_OK)
async def import_opml(request: Request, file: UploadFile):

    try:
        await rss.opml_to_feeds(file=file.file)

        return RedirectResponse(
            request.url_for("feeds").include_query_params(update_status=True),
            status_code=status.HTTP_303_SEE_OTHER,
        )
    except Exception as e:

        return RedirectResponse(
            request.url_for("feeds").include_query_params(update_exception=e),
            status_code=status.HTTP_303_SEE_OTHER,
        )


@app.get("/feeds/", response_class=HTMLResponse)
async def feeds(
    request: Request, update_status: bool = False, update_exception: str = None
):

    return templates.TemplateResponse(
        "feeds.html",
        {
            "request": request,
            "settings": await bk.get_settings(),
            "feeds": bk.list_feeds(agg=False),
            "update_status": update_status,
            "update_exception": update_exception,
        },
    )


@app.get("/feeds/{id}", response_class=HTMLResponse)
async def feed_settings(
    request: Request, id: str, update_status: bool = False, update_exception: str = None
):
    response = {
        "settings": await bk.get_settings(),
        "feed": await bk.get_feed_config(id=id),
        "update_status": update_status,
        "update_exception": update_exception,
    }

    if request.headers.get("accept") == JSON:
        return JSONResponse(content=response, media_type=JSON)
    else:
        return templates.TemplateResponse(
            "feed_config.html", {"request": request, **response}
        )


@app.get("/feeds/new/", response_class=HTMLResponse)
async def new_feed(request: Request, update_exception: str = None):
    response = {
        "settings": await bk.get_settings(),
        "feed": {},
        "update_exception": update_exception,
    }

    if request.headers.get("accept") == JSON:
        return JSONResponse(content=response, media_type=JSON)
    else:
        return templates.TemplateResponse(
            "feed_config.html", {"request": request, **response}
        )


# Utility APIs - mostly used to orchestrate tests, but available for whatever


@app.get("/util/list-feeds", status_code=status.HTTP_200_OK)
async def list_feeds(request: Request) -> Sequence[Mapping]:

    return bk.list_feeds()


@app.get("/util/list-feed-entries", status_code=status.HTTP_200_OK)
async def list_feed_entries(request: Request) -> Sequence[Mapping]:

    all_feeds = bk.list_feeds()

    entries = [list(bk.list_entries(feed["id"])) for feed in all_feeds]

    return list(chain.from_iterable(entries))


@app.get("/util/list-handlers", status_code=status.HTTP_200_OK)
async def list_handlers(request: Request) -> Sequence[Mapping]:

    handlers = bk.get_handlers()

    # config might have secrets so we only return if its configured
    return [
        {
            "name": handler["type"],
            "type": handler["handler_type"],
            "configured": True if handler.get("config") else False,
        }
        for handler in handlers
    ]
