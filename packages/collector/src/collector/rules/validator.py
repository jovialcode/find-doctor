"""Rule validator for validating parsing rules against a schema."""

import json
from pathlib import Path
from typing import Any

import jsonschema
import yaml

from collector.rules.models import SiteRule


class RuleValidator:
    """Validates parsing rules against a JSON schema."""

    def __init__(self, schema_path: str | Path | None = None) -> None:
        """Initialize the validator.

        Args:
            schema_path: Path to the JSON schema file.
                        If None, uses a default schema.
        """
        if schema_path:
            self.schema = self._load_schema(Path(schema_path))
        else:
            self.schema = self._get_default_schema()

    def _load_schema(self, path: Path) -> dict[str, Any]:
        """Load schema from file.

        Args:
            path: Path to schema file

        Returns:
            Schema dictionary
        """
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _get_default_schema(self) -> dict[str, Any]:
        """Get the default rule schema.

        Returns:
            Default schema dictionary
        """
        return {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "required": ["site", "targets"],
            "properties": {
                "site": {
                    "type": "object",
                    "required": ["id", "name", "base_url"],
                    "properties": {
                        "id": {"type": "string", "minLength": 1},
                        "name": {"type": "string", "minLength": 1},
                        "base_url": {"type": "string", "format": "uri"},
                        "enabled": {"type": "boolean"},
                    },
                },
                "crawler": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "enum": ["http", "browser"]},
                        "rate_limit": {"type": "number", "minimum": 0},
                        "timeout": {"type": "integer", "minimum": 1},
                        "headers": {"type": "object"},
                        "cookies": {"type": "object"},
                    },
                },
                "targets": {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                        "type": "object",
                        "required": ["name", "url_pattern", "selectors"],
                        "properties": {
                            "name": {"type": "string", "minLength": 1},
                            "url_pattern": {"type": "string"},
                            "requires_browser": {"type": "boolean"},
                            "pagination": {
                                "type": "object",
                                "properties": {
                                    "type": {
                                        "type": "string",
                                        "enum": ["page_param", "next_button", "infinite_scroll"],
                                    },
                                    "param": {"type": "string"},
                                    "selector": {"type": "string"},
                                    "max_pages": {"type": "integer", "minimum": 1},
                                    "start_page": {"type": "integer", "minimum": 1},
                                },
                            },
                            "selectors": {
                                "type": "object",
                                "properties": {
                                    "container": {"type": "string"},
                                    "item": {"type": "string"},
                                    "fields": {"type": "object"},
                                },
                            },
                        },
                    },
                },
                "transforms": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["field", "operations"],
                        "properties": {
                            "field": {"type": "string"},
                            "operations": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "required": ["type"],
                                    "properties": {
                                        "type": {"type": "string"},
                                        "pattern": {"type": "string"},
                                        "replacement": {"type": "string"},
                                        "separator": {"type": "string"},
                                        "value": {"type": "string"},
                                        "group": {"type": "integer"},
                                    },
                                },
                            },
                        },
                    },
                },
            },
        }

    def validate_file(self, path: str | Path) -> tuple[bool, list[str]]:
        """Validate a rule file.

        Args:
            path: Path to the YAML rule file

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        path = Path(path)
        errors: list[str] = []

        try:
            with path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except Exception as e:
            return False, [f"Failed to parse YAML: {e}"]

        return self.validate(data)

    def validate(self, data: dict[str, Any]) -> tuple[bool, list[str]]:
        """Validate rule data against the schema.

        Args:
            data: Rule data dictionary

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors: list[str] = []

        try:
            jsonschema.validate(data, self.schema)
        except jsonschema.ValidationError as e:
            errors.append(f"Schema validation error: {e.message}")
            return False, errors

        # Additional semantic validation
        semantic_errors = self._validate_semantics(data)
        errors.extend(semantic_errors)

        return len(errors) == 0, errors

    def _validate_semantics(self, data: dict[str, Any]) -> list[str]:
        """Perform semantic validation beyond schema.

        Args:
            data: Rule data dictionary

        Returns:
            List of error messages
        """
        errors: list[str] = []

        # Check for duplicate target names
        target_names = [t.get("name") for t in data.get("targets", [])]
        duplicates = [name for name in target_names if target_names.count(name) > 1]
        if duplicates:
            errors.append(f"Duplicate target names: {set(duplicates)}")

        # Validate selectors have required fields
        for target in data.get("targets", []):
            selectors = target.get("selectors", {})
            fields = selectors.get("fields", {})

            if not fields:
                errors.append(f"Target '{target.get('name')}' has no fields defined")

            for field_name, field_config in fields.items():
                if isinstance(field_config, dict):
                    if not field_config.get("selector"):
                        errors.append(
                            f"Field '{field_name}' in target '{target.get('name')}' "
                            "missing selector"
                        )

        # Validate pagination config
        for target in data.get("targets", []):
            pagination = target.get("pagination")
            if pagination:
                pag_type = pagination.get("type", "page_param")
                if pag_type == "next_button" and not pagination.get("selector"):
                    errors.append(
                        f"Target '{target.get('name')}' uses next_button pagination "
                        "but no selector specified"
                    )

        return errors

    def validate_rule(self, rule: SiteRule) -> tuple[bool, list[str]]:
        """Validate a SiteRule object.

        Args:
            rule: SiteRule to validate

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors: list[str] = []

        if not rule.id:
            errors.append("Site ID is required")

        if not rule.name:
            errors.append("Site name is required")

        if not rule.base_url:
            errors.append("Site base_url is required")

        if not rule.targets:
            errors.append("At least one target is required")

        for target in rule.targets:
            if not target.name:
                errors.append("Target name is required")
            if not target.url_pattern:
                errors.append(f"Target '{target.name}' missing url_pattern")
            if not target.selectors.fields:
                errors.append(f"Target '{target.name}' has no fields defined")

        return len(errors) == 0, errors
