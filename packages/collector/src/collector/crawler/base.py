"""Base crawler interface and data structures."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class CrawlResult:
    """Immutable result of a crawl operation.

    Attributes:
        url: The URL that was crawled
        html: The HTML content of the page
        status_code: HTTP status code
        headers: Response headers
        crawled_at: Timestamp when the crawl occurred
        error: Error message if crawl failed
    """

    url: str
    html: str
    status_code: int
    headers: dict[str, str] = field(default_factory=dict)
    crawled_at: datetime = field(default_factory=datetime.now)
    error: str | None = None

    @property
    def is_success(self) -> bool:
        """Check if the crawl was successful."""
        return 200 <= self.status_code < 300 and self.error is None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "url": self.url,
            "html": self.html,
            "status_code": self.status_code,
            "headers": self.headers,
            "crawled_at": self.crawled_at.isoformat(),
            "error": self.error,
        }


@dataclass
class CrawlRequest:
    """Request parameters for crawling.

    Attributes:
        url: Target URL to crawl
        headers: Custom headers for the request
        timeout: Request timeout in seconds
        retry_count: Number of retries on failure
    """

    url: str
    headers: dict[str, str] = field(default_factory=dict)
    timeout: int = 30
    retry_count: int = 3


class BaseCrawler(ABC):
    """Abstract base class for web crawlers.

    All crawler implementations should inherit from this class and implement
    the fetch method.
    """

    def __init__(
        self,
        rate_limit: float = 1.0,
        timeout: int = 30,
        max_retries: int = 3,
        default_headers: dict[str, str] | None = None,
    ) -> None:
        """Initialize the crawler.

        Args:
            rate_limit: Requests per second limit
            timeout: Default timeout in seconds
            max_retries: Maximum number of retries on failure
            default_headers: Default headers to include in all requests
        """
        self.rate_limit = rate_limit
        self.timeout = timeout
        self.max_retries = max_retries
        self.default_headers = default_headers or {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
        }

    @abstractmethod
    async def fetch(self, url: str, headers: dict[str, str] | None = None) -> CrawlResult:
        """Fetch a URL and return the crawl result.

        Args:
            url: The URL to fetch
            headers: Optional headers to include in the request

        Returns:
            CrawlResult with the HTML content and metadata
        """
        ...

    @abstractmethod
    async def fetch_many(
        self, urls: list[str], headers: dict[str, str] | None = None
    ) -> list[CrawlResult]:
        """Fetch multiple URLs concurrently.

        Args:
            urls: List of URLs to fetch
            headers: Optional headers to include in all requests

        Returns:
            List of CrawlResults
        """
        ...

    @abstractmethod
    async def close(self) -> None:
        """Close the crawler and release resources."""
        ...

    async def __aenter__(self) -> "BaseCrawler":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()
