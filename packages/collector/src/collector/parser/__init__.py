"""Parser module for extracting data from HTML."""

from collector.parser.base import BaseParser, ParseResult
from collector.parser.selector_parser import SelectorParser
from collector.parser.registry import ParserRegistry

__all__ = ["BaseParser", "ParseResult", "SelectorParser", "ParserRegistry"]
