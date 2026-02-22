"""Browser-based crawler using Playwright for JavaScript rendering."""

import asyncio
from datetime import datetime
from typing import Any

from collector.crawler.base import BaseCrawler, CrawlResult


class BrowserCrawler(BaseCrawler):
    """Browser crawler using Playwright for JavaScript-rendered pages.

    This crawler launches a headless browser to render pages that require
    JavaScript execution.
    """

    def __init__(
        self,
        rate_limit: float = 0.5,
        timeout: int = 30,
        max_retries: int = 3,
        default_headers: dict[str, str] | None = None,
        headless: bool = True,
        wait_for_selector: str | None = None,
        wait_timeout: int = 10000,
    ) -> None:
        """Initialize the browser crawler.

        Args:
            rate_limit: Requests per second limit (lower for browser)
            timeout: Default timeout in seconds
            max_retries: Maximum number of retries on failure
            default_headers: Default headers to include
            headless: Whether to run browser in headless mode
            wait_for_selector: Optional CSS selector to wait for before capturing
            wait_timeout: Timeout in ms for wait_for_selector
        """
        super().__init__(rate_limit, timeout, max_retries, default_headers)
        self.headless = headless
        self.wait_for_selector = wait_for_selector
        self.wait_timeout = wait_timeout
        self._browser: Any = None
        self._context: Any = None
        self._semaphore: asyncio.Semaphore | None = None
        self._last_request_time: float = 0

    async def _get_browser(self) -> Any:
        """Get or create the browser instance."""
        if self._browser is None:
            from playwright.async_api import async_playwright

            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=self.headless)
            self._context = await self._browser.new_context(
                user_agent=self.default_headers.get("User-Agent", ""),
                extra_http_headers={
                    k: v for k, v in self.default_headers.items() if k != "User-Agent"
                },
            )
        return self._browser

    async def _rate_limit_wait(self) -> None:
        """Wait to respect rate limiting."""
        if self.rate_limit <= 0:
            return

        min_interval = 1.0 / self.rate_limit
        now = asyncio.get_event_loop().time()
        elapsed = now - self._last_request_time

        if elapsed < min_interval:
            await asyncio.sleep(min_interval - elapsed)

        self._last_request_time = asyncio.get_event_loop().time()

    async def fetch(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        wait_for_selector: str | None = None,
    ) -> CrawlResult:
        """Fetch a URL using browser and return the crawl result.

        Args:
            url: The URL to fetch
            headers: Optional headers to include in the request
            wait_for_selector: Optional CSS selector to wait for

        Returns:
            CrawlResult with the rendered HTML content and metadata
        """
        await self._rate_limit_wait()
        await self._get_browser()

        try:
            page = await self._context.new_page()

            if headers:
                await page.set_extra_http_headers(headers)

            response = await page.goto(url, timeout=self.timeout * 1000)

            # Wait for selector if specified
            selector = wait_for_selector or self.wait_for_selector
            if selector:
                try:
                    await page.wait_for_selector(selector, timeout=self.wait_timeout)
                except Exception:
                    pass  # Continue even if selector not found

            # Get the rendered HTML
            html = await page.content()
            status_code = response.status if response else 0

            await page.close()

            return CrawlResult(
                url=url,
                html=html,
                status_code=status_code,
                headers={},
                crawled_at=datetime.now(),
            )
        except Exception as e:
            return CrawlResult(
                url=url,
                html="",
                status_code=0,
                crawled_at=datetime.now(),
                error=str(e),
            )

    async def fetch_many(
        self, urls: list[str], headers: dict[str, str] | None = None
    ) -> list[CrawlResult]:
        """Fetch multiple URLs using browser with rate limiting.

        Args:
            urls: List of URLs to fetch
            headers: Optional headers to include in all requests

        Returns:
            List of CrawlResults in the same order as input URLs
        """
        if self._semaphore is None:
            # Limit concurrent browser tabs
            max_concurrent = max(1, int(self.rate_limit * 3))
            self._semaphore = asyncio.Semaphore(max_concurrent)

        async def fetch_with_semaphore(url: str) -> CrawlResult:
            async with self._semaphore:  # type: ignore
                return await self.fetch(url, headers)

        tasks = [fetch_with_semaphore(url) for url in urls]
        return await asyncio.gather(*tasks)

    async def close(self) -> None:
        """Close the browser and release resources."""
        if self._context is not None:
            await self._context.close()
            self._context = None
        if self._browser is not None:
            await self._browser.close()
            self._browser = None
        if hasattr(self, "_playwright") and self._playwright is not None:
            await self._playwright.stop()
            self._playwright = None
