"""Base parser interface and data structures."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class ParseResult:
    """Immutable result of a parse operation.

    Attributes:
        source_url: The URL the HTML was fetched from
        data: Extracted data as a list of dictionaries
        parsed_at: Timestamp when the parse occurred
        errors: List of errors encountered during parsing
    """

    source_url: str
    data: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    parsed_at: datetime = field(default_factory=datetime.now)
    errors: tuple[str, ...] = field(default_factory=tuple)

    @property
    def is_success(self) -> bool:
        """Check if parsing was successful."""
        return len(self.data) > 0

    @property
    def item_count(self) -> int:
        """Get the number of items parsed."""
        return len(self.data)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "source_url": self.source_url,
            "data": list(self.data),
            "parsed_at": self.parsed_at.isoformat(),
            "errors": list(self.errors),
        }


@dataclass
class FieldRule:
    """Rule for extracting a single field.

    Attributes:
        name: Field name
        selector: CSS selector or XPath
        type: Field type (text, text_list, url, attribute)
        attribute: Attribute name for attribute type
        default: Default value if not found
        transform: List of transformation operations
    """

    name: str
    selector: str
    type: str = "text"
    attribute: str | None = None
    default: Any = None
    transform: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class ParserRule:
    """Complete parsing rule for a target.

    Attributes:
        name: Rule name/identifier
        container: CSS selector for the container element
        item: CSS selector for individual items within container
        fields: List of field extraction rules
        pagination: Pagination configuration
    """

    name: str
    container: str | None = None
    item: str | None = None
    fields: list[FieldRule] = field(default_factory=list)
    pagination: dict[str, Any] | None = None


class BaseParser(ABC):
    """Abstract base class for HTML parsers.

    All parser implementations should inherit from this class and implement
    the parse method.
    """

    @abstractmethod
    def parse(self, html: str, rule: ParserRule, source_url: str = "") -> ParseResult:
        """Parse HTML using the given rule.

        Args:
            html: HTML content to parse
            rule: Parsing rule to apply
            source_url: Source URL for the HTML

        Returns:
            ParseResult with extracted data
        """
        ...

    @abstractmethod
    def parse_single(
        self, html: str, fields: list[FieldRule], source_url: str = ""
    ) -> ParseResult:
        """Parse HTML for a single item (e.g., detail page).

        Args:
            html: HTML content to parse
            fields: List of field rules to apply
            source_url: Source URL for the HTML

        Returns:
            ParseResult with single extracted item
        """
        ...
