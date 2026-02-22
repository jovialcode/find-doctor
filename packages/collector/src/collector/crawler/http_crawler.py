"""HTTP-based crawler using httpx."""

import asyncio
from datetime import datetime
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from collector.crawler.base import BaseCrawler, CrawlResult


class HttpCrawler(BaseCrawler):
    """HTTP crawler using httpx for async requests.

    This crawler is suitable for pages that don't require JavaScript rendering.
    """

    def __init__(
        self,
        rate_limit: float = 1.0,
        timeout: int = 30,
        max_retries: int = 3,
        default_headers: dict[str, str] | None = None,
        follow_redirects: bool = True,
    ) -> None:
        """Initialize the HTTP crawler.

        Args:
            rate_limit: Requests per second limit
            timeout: Default timeout in seconds
            max_retries: Maximum number of retries on failure
            default_headers: Default headers to include in all requests
            follow_redirects: Whether to follow HTTP redirects
        """
        super().__init__(rate_limit, timeout, max_retries, default_headers)
        self.follow_redirects = follow_redirects
        self._client: httpx.AsyncClient | None = None
        self._semaphore: asyncio.Semaphore | None = None
        self._last_request_time: float = 0

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                follow_redirects=self.follow_redirects,
                headers=self.default_headers,
            )
        return self._client

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

    async def fetch(self, url: str, headers: dict[str, str] | None = None) -> CrawlResult:
        """Fetch a URL and return the crawl result.

        Args:
            url: The URL to fetch
            headers: Optional headers to include in the request

        Returns:
            CrawlResult with the HTML content and metadata
        """
        await self._rate_limit_wait()

        client = await self._get_client()
        merged_headers = {**self.default_headers, **(headers or {})}

        try:
            response = await self._fetch_with_retry(client, url, merged_headers)
            return CrawlResult(
                url=url,
                html=response.text,
                status_code=response.status_code,
                headers=dict(response.headers),
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

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def _fetch_with_retry(
        self,
        client: httpx.AsyncClient,
        url: str,
        headers: dict[str, str],
    ) -> httpx.Response:
        """Fetch URL with retry logic.

        Args:
            client: HTTP client
            url: URL to fetch
            headers: Request headers

        Returns:
            HTTP response
        """
        return await client.get(url, headers=headers)

    async def fetch_many(
        self, urls: list[str], headers: dict[str, str] | None = None
    ) -> list[CrawlResult]:
        """Fetch multiple URLs concurrently with rate limiting.

        Args:
            urls: List of URLs to fetch
            headers: Optional headers to include in all requests

        Returns:
            List of CrawlResults in the same order as input URLs
        """
        if self._semaphore is None:
            # Limit concurrent requests
            max_concurrent = max(1, int(self.rate_limit * 5))
            self._semaphore = asyncio.Semaphore(max_concurrent)

        async def fetch_with_semaphore(url: str) -> CrawlResult:
            async with self._semaphore:  # type: ignore
                return await self.fetch(url, headers)

        tasks = [fetch_with_semaphore(url) for url in urls]
        return await asyncio.gather(*tasks)

    async def close(self) -> None:
        """Close the HTTP client and release resources."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
