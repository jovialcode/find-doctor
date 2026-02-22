"""Data models for parsing rules."""

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass(frozen=True)
class FieldSelector:
    """Field extraction configuration.

    Attributes:
        selector: CSS selector or XPath
        type: Field type (text, text_list, url, attribute, html)
        attribute: Attribute name for attribute/url types
        default: Default value if not found
    """

    selector: str
    type: Literal["text", "text_list", "url", "attribute", "html"] = "text"
    attribute: str | None = None
    default: Any = None


@dataclass(frozen=True)
class TransformOperation:
    """Transformation operation for extracted values.

    Attributes:
        type: Transform type (strip, regex_extract, regex_replace, split, join, etc.)
        pattern: Regex pattern for regex operations
        replacement: Replacement string for regex_replace
        separator: Separator for split/join operations
        value: Value for prefix/suffix operations
        group: Group number for regex_extract
    """

    type: str
    pattern: str | None = None
    replacement: str | None = None
    separator: str | None = None
    value: str | None = None
    group: int = 1


@dataclass(frozen=True)
class PaginationConfig:
    """Pagination configuration.

    Attributes:
        type: Pagination type (page_param, next_button, infinite_scroll)
        param: Query parameter name for page_param type
        selector: CSS selector for next_button type
        max_pages: Maximum number of pages to crawl
        start_page: Starting page number
    """

    type: Literal["page_param", "next_button", "infinite_scroll"] = "page_param"
    param: str = "page"
    selector: str | None = None
    max_pages: int = 10
    start_page: int = 1


@dataclass(frozen=True)
class SelectorsConfig:
    """Selectors configuration for a target.

    Attributes:
        container: CSS selector for the container element
        item: CSS selector for individual items
        fields: Dictionary of field name to FieldSelector
    """

    container: str | None = None
    item: str | None = None
    fields: dict[str, FieldSelector] = field(default_factory=dict)


@dataclass(frozen=True)
class TargetRule:
    """Rule for a crawl target.

    Attributes:
        name: Target name/identifier
        url_pattern: URL pattern with placeholders
        selectors: Selector configuration
        pagination: Optional pagination config
        requires_browser: Whether browser rendering is needed
    """

    name: str
    url_pattern: str
    selectors: SelectorsConfig
    pagination: PaginationConfig | None = None
    requires_browser: bool = False


@dataclass(frozen=True)
class CrawlerConfig:
    """Crawler configuration for a site.

    Attributes:
        type: Crawler type (http or browser)
        rate_limit: Requests per second
        timeout: Request timeout in seconds
        headers: Custom headers
        cookies: Cookies to include
    """

    type: Literal["http", "browser"] = "http"
    rate_limit: float = 1.0
    timeout: int = 30
    headers: dict[str, str] = field(default_factory=dict)
    cookies: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class TransformConfig:
    """Transform configuration for post-processing.

    Attributes:
        field: Field name to transform
        operations: List of transform operations
    """

    field: str
    operations: tuple[TransformOperation, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class SiteRule:
    """Complete parsing rule for a site.

    Attributes:
        id: Unique site identifier
        name: Site display name
        base_url: Base URL of the site
        crawler: Crawler configuration
        targets: List of crawl targets
        transforms: List of transform configurations
        enabled: Whether the site is enabled for crawling
    """

    id: str
    name: str
    base_url: str
    crawler: CrawlerConfig = field(default_factory=CrawlerConfig)
    targets: tuple[TargetRule, ...] = field(default_factory=tuple)
    transforms: tuple[TransformConfig, ...] = field(default_factory=tuple)
    enabled: bool = True

    def get_target(self, name: str) -> TargetRule | None:
        """Get a target by name.

        Args:
            name: Target name

        Returns:
            Target rule or None if not found
        """
        for target in self.targets:
            if target.name == name:
                return target
        return None
