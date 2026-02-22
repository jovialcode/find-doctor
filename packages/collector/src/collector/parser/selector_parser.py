"""CSS/XPath selector-based parser using parsel."""

import re
from datetime import datetime
from typing import Any
from urllib.parse import urljoin

from parsel import Selector

from collector.parser.base import BaseParser, FieldRule, ParseResult, ParserRule


class SelectorParser(BaseParser):
    """Parser using CSS and XPath selectors via parsel.

    This parser supports both CSS selectors and XPath expressions for
    extracting data from HTML.
    """

    def parse(self, html: str, rule: ParserRule, source_url: str = "") -> ParseResult:
        """Parse HTML using the given rule.

        Args:
            html: HTML content to parse
            rule: Parsing rule to apply
            source_url: Source URL for the HTML

        Returns:
            ParseResult with extracted data
        """
        errors: list[str] = []
        items: list[dict[str, Any]] = []

        try:
            selector = Selector(text=html)

            # Get container if specified
            if rule.container:
                containers = selector.css(rule.container)
                if not containers:
                    errors.append(f"Container not found: {rule.container}")
                    return ParseResult(
                        source_url=source_url,
                        data=tuple(),
                        errors=tuple(errors),
                    )
                container = containers[0]
            else:
                container = selector

            # Get items
            if rule.item:
                item_elements = container.css(rule.item)
            else:
                item_elements = [container]

            # Extract data from each item
            for item_el in item_elements:
                item_data: dict[str, Any] = {}
                for field in rule.fields:
                    try:
                        value = self._extract_field(item_el, field, source_url)
                        item_data[field.name] = value
                    except Exception as e:
                        errors.append(f"Error extracting {field.name}: {e}")
                        item_data[field.name] = field.default

                if item_data:
                    items.append(item_data)

        except Exception as e:
            errors.append(f"Parse error: {e}")

        return ParseResult(
            source_url=source_url,
            data=tuple(items),
            parsed_at=datetime.now(),
            errors=tuple(errors),
        )

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
        errors: list[str] = []
        item_data: dict[str, Any] = {}

        try:
            selector = Selector(text=html)

            for field in fields:
                try:
                    value = self._extract_field(selector, field, source_url)
                    item_data[field.name] = value
                except Exception as e:
                    errors.append(f"Error extracting {field.name}: {e}")
                    item_data[field.name] = field.default

        except Exception as e:
            errors.append(f"Parse error: {e}")

        data = (item_data,) if item_data else tuple()

        return ParseResult(
            source_url=source_url,
            data=data,
            parsed_at=datetime.now(),
            errors=tuple(errors),
        )

    def _extract_field(
        self, element: Selector, field: FieldRule, base_url: str
    ) -> Any:
        """Extract a single field value from an element.

        Args:
            element: Parsel Selector element
            field: Field extraction rule
            base_url: Base URL for resolving relative URLs

        Returns:
            Extracted and transformed value
        """
        # Determine if selector is XPath or CSS
        is_xpath = field.selector.startswith("//") or field.selector.startswith("./")

        if is_xpath:
            selected = element.xpath(field.selector)
        else:
            selected = element.css(field.selector)

        if not selected:
            return field.default

        # Extract based on type
        if field.type == "text":
            value = selected[0].css("::text").get()
            if value is None:
                value = selected[0].get()
                # Strip HTML tags if we got raw HTML
                if value and "<" in value:
                    value = re.sub(r"<[^>]+>", "", value)
            value = value.strip() if value else field.default

        elif field.type == "text_list":
            if is_xpath:
                values = selected.xpath("string()").getall()
            else:
                values = selected.css("::text").getall()
            value = [v.strip() for v in values if v.strip()]

        elif field.type == "url":
            attr = field.attribute or "href"
            raw_url = selected[0].attrib.get(attr)
            if raw_url and base_url:
                value = urljoin(base_url, raw_url)
            else:
                value = raw_url or field.default

        elif field.type == "attribute":
            if field.attribute:
                value = selected[0].attrib.get(field.attribute, field.default)
            else:
                value = field.default

        elif field.type == "html":
            value = selected[0].get()

        else:
            value = selected[0].get()

        # Apply transforms
        if field.transform:
            value = self._apply_transforms(value, field.transform)

        return value

    def _apply_transforms(self, value: Any, transforms: list[dict[str, Any]]) -> Any:
        """Apply a series of transformations to a value.

        Args:
            value: Value to transform
            transforms: List of transformation operations

        Returns:
            Transformed value
        """
        for transform in transforms:
            transform_type = transform.get("type")

            if transform_type == "strip":
                if isinstance(value, str):
                    value = value.strip()
                elif isinstance(value, list):
                    value = [v.strip() if isinstance(v, str) else v for v in value]

            elif transform_type == "regex_extract":
                pattern = transform.get("pattern", "")
                group = transform.get("group", 1)
                if isinstance(value, str):
                    match = re.search(pattern, value)
                    if match:
                        try:
                            value = match.group(group)
                        except IndexError:
                            pass

            elif transform_type == "regex_replace":
                pattern = transform.get("pattern", "")
                replacement = transform.get("replacement", "")
                if isinstance(value, str):
                    value = re.sub(pattern, replacement, value)

            elif transform_type == "split":
                separator = transform.get("separator", ",")
                if isinstance(value, str):
                    value = [v.strip() for v in value.split(separator)]

            elif transform_type == "join":
                separator = transform.get("separator", ", ")
                if isinstance(value, list):
                    value = separator.join(str(v) for v in value)

            elif transform_type == "lowercase":
                if isinstance(value, str):
                    value = value.lower()

            elif transform_type == "uppercase":
                if isinstance(value, str):
                    value = value.upper()

            elif transform_type == "prefix":
                prefix = transform.get("value", "")
                if isinstance(value, str):
                    value = prefix + value

            elif transform_type == "suffix":
                suffix = transform.get("value", "")
                if isinstance(value, str):
                    value = value + suffix

        return value
