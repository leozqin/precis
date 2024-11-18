from __future__ import annotations

from logging import getLogger

from playwright.async_api import Playwright, Route, async_playwright

from app.constants import USER_AGENT
from app.handlers import ContentRetrievalHandler

logger = getLogger("uvicorn.error")


class PlaywrightContentRetriever(ContentRetrievalHandler):
    id = "playwright"

    @staticmethod
    async def _block_common_with_script(route: Route):
        excluded_resource_types = ["stylesheet", "image", "font"]
        if route.request.resource_type in excluded_resource_types:
            await route.abort()
        else:
            await route.continue_()

    @staticmethod
    async def _block_common(route: Route):
        excluded_resource_types = ["stylesheet", "image", "font", "script"]
        if route.request.resource_type in excluded_resource_types:
            await route.abort()
        else:
            await route.continue_()

    @staticmethod
    async def _retrieve(url: str, playright: Playwright, use_script: bool = False):
        browser = await playright.chromium.launch()
        page = await browser.new_page(user_agent=USER_AGENT)

        retriever = (
            PlaywrightContentRetriever._block_common_with_script
            if use_script
            else PlaywrightContentRetriever._block_common
        )

        await page.route("**/*", retriever)
        await page.goto(url)

        await page.wait_for_load_state("domcontentloaded")

        return await page.content()

    async def get_html(self, url: str, use_script: bool = False) -> str:
        async with async_playwright() as pw:
            return await self._retrieve(url=url, playright=pw, use_script=use_script)
