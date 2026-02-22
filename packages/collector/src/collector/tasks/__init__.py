"""Airflow tasks for data collection pipeline."""

from collector.tasks.crawl_task import crawl_site, crawl_target
from collector.tasks.parse_task import parse_crawled_data

__all__ = ["crawl_site", "crawl_target", "parse_crawled_data"]
