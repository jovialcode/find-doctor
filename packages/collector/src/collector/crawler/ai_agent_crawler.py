"""AI Agent crawler using browser-use and Claude API."""

import logging
from datetime import datetime
from typing import Any

from collector.crawler.base import BaseCrawler, CrawlResult

logger = logging.getLogger(__name__)


class AIAgentCrawler(BaseCrawler):
    """Crawler that uses browser-use + Claude API to understand pages and extract data.

    This crawler leverages an AI agent to navigate complex pages,
    handle dynamic content, and extract structured data that
    traditional selectors cannot handle.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "claude-sonnet-4-20250514",
        rate_limit: float = 0.2,
        timeout: int = 120,
        max_retries: int = 2,
        default_headers: dict[str, str] | None = None,
        extraction_prompt: str | None = None,
    ) -> None:
        """Initialize the AI Agent crawler.

        Args:
            api_key: Anthropic API key (falls back to env ANTHROPIC_API_KEY)
            model: Claude model to use
            rate_limit: Requests per second limit (low for AI agent)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries on failure
            default_headers: Default headers for requests
            extraction_prompt: Custom prompt for data extraction
        """
        super().__init__(
            rate_limit=rate_limit,
            timeout=timeout,
            max_retries=max_retries,
            default_headers=default_headers,
        )
        self._api_key = api_key
        self._model = model
        self._extraction_prompt = extraction_prompt
        self._agent: Any = None
        self._browser: Any = None

    async def _ensure_agent(self) -> Any:
        """Lazily initialize the browser-use agent."""
        if self._agent is not None:
            return self._agent

        from browser_use import Agent
        from langchain_anthropic import ChatAnthropic

        llm = ChatAnthropic(
            model_name=self._model,
            api_key=self._api_key,
            timeout=self._timeout if hasattr(self, "_timeout") else self.timeout,
        )

        self._agent = Agent(
            task="Navigate to the given URL and extract the page content.",
            llm=llm,
        )

        return self._agent

    async def fetch(self, url: str, headers: dict[str, str] | None = None) -> CrawlResult:
        """Fetch a URL using the AI agent.

        The agent navigates to the URL, waits for content to load,
        and returns the rendered HTML.

        Args:
            url: The URL to fetch
            headers: Optional headers (not directly used by browser-use)

        Returns:
            CrawlResult with the page HTML
        """
        try:
            agent = await self._ensure_agent()

            task = f"Go to {url} and extract the full page content."
            if self._extraction_prompt:
                task = f"Go to {url}. {self._extraction_prompt}"

            result = await agent.run(task=task)

            html = ""
            if hasattr(result, "extracted_content") and result.extracted_content:
                html = result.extracted_content
            elif hasattr(result, "final_result") and result.final_result:
                html = str(result.final_result)
            else:
                html = str(result)

            return CrawlResult(
                url=url,
                html=html,
                status_code=200,
                crawled_at=datetime.now(),
            )

        except Exception as e:
            logger.exception("AI agent crawl failed for %s", url)
            return CrawlResult(
                url=url,
                html="",
                status_code=500,
                error=str(e),
                crawled_at=datetime.now(),
            )

    async def fetch_many(
        self, urls: list[str], headers: dict[str, str] | None = None
    ) -> list[CrawlResult]:
        """Fetch multiple URLs sequentially with the AI agent.

        AI agent tasks are executed sequentially due to high cost
        and resource requirements.

        Args:
            urls: List of URLs to fetch
            headers: Optional headers

        Returns:
            List of CrawlResults
        """
        results: list[CrawlResult] = []
        for url in urls:
            result = await self.fetch(url, headers)
            results.append(result)
        return results

    async def extract_structured(
        self,
        url: str,
        schema: dict[str, Any],
        prompt: str | None = None,
    ) -> dict[str, Any]:
        """Extract structured data from a URL using AI.

        Args:
            url: The URL to extract data from
            schema: Expected data schema (field names and descriptions)
            prompt: Custom extraction prompt

        Returns:
            Extracted structured data
        """
        schema_desc = ", ".join(f"{k}: {v}" for k, v in schema.items())
        extraction_prompt = prompt or (
            f"Extract the following fields: {schema_desc}. "
            "Return the data as a JSON object."
        )

        agent = await self._ensure_agent()

        task = f"Go to {url}. {extraction_prompt}"
        result = await agent.run(task=task)

        if hasattr(result, "extracted_content") and result.extracted_content:
            import json

            try:
                return json.loads(result.extracted_content)
            except (json.JSONDecodeError, TypeError):
                pass

        return {"raw": str(result)}

    async def close(self) -> None:
        """Close the AI agent and release resources."""
        if self._browser is not None:
            try:
                await self._browser.close()
            except Exception:
                pass
            self._browser = None
        self._agent = None
