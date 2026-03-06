"""Crawl tasks for Airflow."""

import asyncio
from pathlib import Path
from typing import Any

from collector.crawler import AIAgentCrawler, BrowserCrawler, CrawlResult, HttpCrawler
from core.config.settings import get_settings
from collector.rules.loader import RuleLoader
from collector.rules.models import SiteRule, TargetRule
from collector.storage.local import LocalStorage
from collector.storage.writer import StorageWriter


async def _crawl_url(
    url: str,
    site_rule: SiteRule,
    use_browser: bool = False,
) -> CrawlResult:
    """Crawl a single URL.

    Args:
        url: URL to crawl
        site_rule: Site rule with crawler config
        use_browser: Whether to use browser crawler

    Returns:
        Crawl result
    """
    crawler_config = site_rule.crawler

    if crawler_config.type == "ai_agent":
        settings = get_settings()
        async with AIAgentCrawler(
            api_key=settings.anthropic_api_key or None,
            rate_limit=crawler_config.rate_limit,
            timeout=crawler_config.timeout,
            extraction_prompt=crawler_config.ai_extraction_prompt,
        ) as crawler:
            return await crawler.fetch(url)
    elif use_browser or crawler_config.type == "browser":
        async with BrowserCrawler(
            rate_limit=crawler_config.rate_limit,
            timeout=crawler_config.timeout,
            default_headers=crawler_config.headers or None,
        ) as crawler:
            return await crawler.fetch(url)
    else:
        async with HttpCrawler(
            rate_limit=crawler_config.rate_limit,
            timeout=crawler_config.timeout,
            default_headers=crawler_config.headers or None,
        ) as crawler:
            return await crawler.fetch(url)


async def _crawl_urls(
    urls: list[str],
    site_rule: SiteRule,
    use_browser: bool = False,
) -> list[CrawlResult]:
    """Crawl multiple URLs.

    Args:
        urls: List of URLs to crawl
        site_rule: Site rule with crawler config
        use_browser: Whether to use browser crawler

    Returns:
        List of crawl results
    """
    crawler_config = site_rule.crawler

    if crawler_config.type == "ai_agent":
        settings = get_settings()
        async with AIAgentCrawler(
            api_key=settings.anthropic_api_key or None,
            rate_limit=crawler_config.rate_limit,
            timeout=crawler_config.timeout,
            extraction_prompt=crawler_config.ai_extraction_prompt,
        ) as crawler:
            return await crawler.fetch_many(urls)
    elif use_browser or crawler_config.type == "browser":
        async with BrowserCrawler(
            rate_limit=crawler_config.rate_limit,
            timeout=crawler_config.timeout,
            default_headers=crawler_config.headers or None,
        ) as crawler:
            return await crawler.fetch_many(urls)
    else:
        async with HttpCrawler(
            rate_limit=crawler_config.rate_limit,
            timeout=crawler_config.timeout,
            default_headers=crawler_config.headers or None,
        ) as crawler:
            return await crawler.fetch_many(urls)


def _generate_urls(target: TargetRule, base_url: str, params: dict[str, Any]) -> list[str]:
    """Generate URLs for a target with pagination.

    Args:
        target: Target rule
        base_url: Site base URL
        params: URL parameters

    Returns:
        List of URLs to crawl
    """
    urls: list[str] = []

    # Format the URL pattern with provided params
    url_pattern = target.url_pattern
    try:
        formatted_url = url_pattern.format(**params)
    except KeyError:
        formatted_url = url_pattern

    # Make absolute URL
    if formatted_url.startswith("/"):
        base = base_url.rstrip("/")
        formatted_url = f"{base}{formatted_url}"

    # Handle pagination
    if target.pagination:
        pag = target.pagination
        if pag.type == "page_param":
            for page in range(pag.start_page, pag.start_page + pag.max_pages):
                separator = "&" if "?" in formatted_url else "?"
                paginated_url = f"{formatted_url}{separator}{pag.param}={page}"
                urls.append(paginated_url)
        else:
            urls.append(formatted_url)
    else:
        urls.append(formatted_url)

    return urls


def crawl_target(
    site_id: str,
    target_name: str,
    rules_dir: str,
    output_dir: str,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Crawl a specific target for a site.

    Args:
        site_id: Site identifier
        target_name: Target name
        rules_dir: Directory containing rule files
        output_dir: Directory for output files
        params: Optional URL parameters

    Returns:
        Crawl summary
    """
    # Load rule
    loader = RuleLoader(rules_dir)
    site_rule = loader.load_rule(site_id)

    target = site_rule.get_target(target_name)
    if target is None:
        raise ValueError(f"Target '{target_name}' not found in site '{site_id}'")

    # Generate URLs
    urls = _generate_urls(target, site_rule.base_url, params or {})

    # Crawl URLs
    results = asyncio.run(_crawl_urls(urls, site_rule, target.requires_browser))

    # Save results
    storage = LocalStorage(output_dir)
    writer = StorageWriter(storage)

    crawled_urls: list[str] = []
    errors: list[dict[str, Any]] = []

    for result in results:
        if result.is_success:
            writer.save_raw_html(site_id, target_name, result.url, result.html)
            crawled_urls.append(result.url)
        else:
            errors.append({
                "url": result.url,
                "error": result.error,
                "status_code": result.status_code,
            })

    # Save manifest
    writer.save_crawl_manifest(site_id, crawled_urls, errors)

    return {
        "site_id": site_id,
        "target_name": target_name,
        "total_urls": len(urls),
        "success_count": len(crawled_urls),
        "error_count": len(errors),
    }


def crawl_site(
    site_id: str,
    rules_dir: str,
    output_dir: str,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Crawl all targets for a site.

    Args:
        site_id: Site identifier
        rules_dir: Directory containing rule files
        output_dir: Directory for output files
        params: Optional URL parameters

    Returns:
        Crawl summary for all targets
    """
    # Load rule
    loader = RuleLoader(rules_dir)
    site_rule = loader.load_rule(site_id)

    results: list[dict[str, Any]] = []

    for target in site_rule.targets:
        try:
            result = crawl_target(
                site_id=site_id,
                target_name=target.name,
                rules_dir=rules_dir,
                output_dir=output_dir,
                params=params,
            )
            results.append(result)
        except Exception as e:
            results.append({
                "site_id": site_id,
                "target_name": target.name,
                "error": str(e),
            })

    return {
        "site_id": site_id,
        "targets_crawled": len(results),
        "results": results,
    }
