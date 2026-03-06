"""Crawler module for fetching web pages."""

from collector.crawler.base import BaseCrawler, CrawlResult
from collector.crawler.http_crawler import HttpCrawler
from collector.crawler.browser_crawler import BrowserCrawler
from collector.crawler.ai_agent_crawler import AIAgentCrawler

__all__ = ["BaseCrawler", "CrawlResult", "HttpCrawler", "BrowserCrawler", "AIAgentCrawler"]
