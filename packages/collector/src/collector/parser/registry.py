"""Parser registry for managing parser instances."""

from typing import Type

from collector.parser.base import BaseParser
from collector.parser.selector_parser import SelectorParser


class ParserRegistry:
    """Registry for parser implementations.

    Allows registration and retrieval of parser classes by name.
    """

    _parsers: dict[str, Type[BaseParser]] = {
        "selector": SelectorParser,
    }

    @classmethod
    def register(cls, name: str, parser_class: Type[BaseParser]) -> None:
        """Register a parser class.

        Args:
            name: Name to register the parser under
            parser_class: Parser class to register
        """
        cls._parsers[name] = parser_class

    @classmethod
    def get(cls, name: str) -> BaseParser:
        """Get a parser instance by name.

        Args:
            name: Name of the parser

        Returns:
            Parser instance

        Raises:
            KeyError: If parser name is not registered
        """
        if name not in cls._parsers:
            raise KeyError(f"Parser '{name}' not found. Available: {list(cls._parsers.keys())}")
        return cls._parsers[name]()

    @classmethod
    def list_parsers(cls) -> list[str]:
        """List all registered parser names.

        Returns:
            List of parser names
        """
        return list(cls._parsers.keys())
