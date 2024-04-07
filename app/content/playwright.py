from playwright.async_api import Playwright, Route, async_playwright

from app.models import ContentRetriever


class PlaywrightContentRetriever(ContentRetriever):
    @staticmethod
    async def _block_common(route: Route):
        excluded_resource_types = ["stylesheet", "script", "image", "font"]
        if route.request.resource_type in excluded_resource_types:
            await route.abort()
        else:
            await route.continue_()

    @staticmethod
    async def _retrieve(url: str, playright: Playwright):
        browser = await playright.chromium.launch()
        page = await browser.new_page()

        await page.route("**/*", PlaywrightContentRetriever._block_common)
        await page.goto(url)

        await page.wait_for_load_state("domcontentloaded")

        return await page.content()

    async def get_content(self, url: str) -> str:
        async with async_playwright() as pw:
            return await self._retrieve(url=url, playright=pw)
