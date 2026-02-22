"""Collector package for web crawling and parsing hospital/doctor data."""

from collector.crawler.base import BaseCrawler, CrawlResult
from collector.crawler.http_crawler import HttpCrawler
from collector.parser.base import BaseParser
from collector.parser.selector_parser import SelectorParser

__all__ = [
    "BaseCrawler",
    "CrawlResult",
    "HttpCrawler",
    "BaseParser",
    "SelectorParser",
]
