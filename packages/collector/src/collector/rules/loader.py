"""Rule loader for loading parsing rules from YAML files."""

from pathlib import Path
from typing import Any

import yaml

from collector.rules.models import (
    CrawlerConfig,
    FieldSelector,
    PaginationConfig,
    SelectorsConfig,
    SiteRule,
    TargetRule,
    TransformConfig,
    TransformOperation,
)


class RuleLoader:
    """Loads parsing rules from YAML files."""

    def __init__(self, rules_dir: str | Path) -> None:
        """Initialize the rule loader.

        Args:
            rules_dir: Directory containing rule YAML files
        """
        self.rules_dir = Path(rules_dir)

    def load_rule(self, site_id: str) -> SiteRule:
        """Load a rule for a specific site.

        Args:
            site_id: Site identifier

        Returns:
            Parsed SiteRule

        Raises:
            FileNotFoundError: If rule file doesn't exist
            ValueError: If rule is invalid
        """
        # Try different possible file locations
        possible_paths = [
            self.rules_dir / f"{site_id}.yaml",
            self.rules_dir / f"{site_id}.yml",
            self.rules_dir / "hospitals" / f"{site_id}.yaml",
            self.rules_dir / "hospitals" / f"{site_id}.yml",
        ]

        rule_path = None
        for path in possible_paths:
            if path.exists():
                rule_path = path
                break

        if rule_path is None:
            raise FileNotFoundError(f"Rule file not found for site: {site_id}")

        return self.load_from_file(rule_path)

    def load_from_file(self, path: Path | str) -> SiteRule:
        """Load a rule from a YAML file.

        Args:
            path: Path to the YAML file

        Returns:
            Parsed SiteRule
        """
        path = Path(path)
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return self._parse_rule(data)

    def load_all_rules(self) -> list[SiteRule]:
        """Load all rules from the rules directory.

        Returns:
            List of parsed SiteRules
        """
        rules: list[SiteRule] = []

        for yaml_file in self.rules_dir.rglob("*.yaml"):
            try:
                rule = self.load_from_file(yaml_file)
                rules.append(rule)
            except Exception as e:
                print(f"Warning: Failed to load {yaml_file}: {e}")

        for yml_file in self.rules_dir.rglob("*.yml"):
            try:
                rule = self.load_from_file(yml_file)
                rules.append(rule)
            except Exception as e:
                print(f"Warning: Failed to load {yml_file}: {e}")

        return rules

    def _parse_rule(self, data: dict[str, Any]) -> SiteRule:
        """Parse rule data into SiteRule.

        Args:
            data: Raw rule data from YAML

        Returns:
            Parsed SiteRule
        """
        site_data = data.get("site", {})
        crawler_data = data.get("crawler", {})
        targets_data = data.get("targets", [])
        transforms_data = data.get("transforms", [])

        # Parse crawler config
        crawler = CrawlerConfig(
            type=crawler_data.get("type", "http"),
            rate_limit=crawler_data.get("rate_limit", 1.0),
            timeout=crawler_data.get("timeout", 30),
            headers=crawler_data.get("headers", {}),
            cookies=crawler_data.get("cookies", {}),
            ai_extraction_prompt=crawler_data.get("ai_extraction_prompt"),
        )

        # Parse targets
        targets = tuple(self._parse_target(t) for t in targets_data)

        # Parse transforms
        transforms = tuple(self._parse_transform(t) for t in transforms_data)

        return SiteRule(
            id=site_data.get("id", ""),
            name=site_data.get("name", ""),
            base_url=site_data.get("base_url", ""),
            crawler=crawler,
            targets=targets,
            transforms=transforms,
            enabled=site_data.get("enabled", True),
        )

    def _parse_target(self, data: dict[str, Any]) -> TargetRule:
        """Parse target data into TargetRule.

        Args:
            data: Raw target data

        Returns:
            Parsed TargetRule
        """
        selectors_data = data.get("selectors", {})
        pagination_data = data.get("pagination")

        # Parse field selectors
        fields_data = selectors_data.get("fields", {})
        fields: dict[str, FieldSelector] = {}

        for field_name, field_config in fields_data.items():
            if isinstance(field_config, str):
                # Simple selector string
                fields[field_name] = FieldSelector(selector=field_config)
            else:
                # Full config dict
                fields[field_name] = FieldSelector(
                    selector=field_config.get("selector", ""),
                    type=field_config.get("type", "text"),
                    attribute=field_config.get("attribute"),
                    default=field_config.get("default"),
                )

        selectors = SelectorsConfig(
            container=selectors_data.get("container"),
            item=selectors_data.get("item"),
            fields=fields,
        )

        # Parse pagination
        pagination = None
        if pagination_data:
            pagination = PaginationConfig(
                type=pagination_data.get("type", "page_param"),
                param=pagination_data.get("param", "page"),
                selector=pagination_data.get("selector"),
                max_pages=pagination_data.get("max_pages", 10),
                start_page=pagination_data.get("start_page", 1),
            )

        return TargetRule(
            name=data.get("name", ""),
            url_pattern=data.get("url_pattern", ""),
            selectors=selectors,
            pagination=pagination,
            requires_browser=data.get("requires_browser", False),
            extraction_mode=data.get("extraction_mode", "selector"),
        )

    def _parse_transform(self, data: dict[str, Any]) -> TransformConfig:
        """Parse transform data into TransformConfig.

        Args:
            data: Raw transform data

        Returns:
            Parsed TransformConfig
        """
        operations_data = data.get("operations", [])
        operations = tuple(
            TransformOperation(
                type=op.get("type", ""),
                pattern=op.get("pattern"),
                replacement=op.get("replacement"),
                separator=op.get("separator"),
                value=op.get("value"),
                group=op.get("group", 1),
            )
            for op in operations_data
        )

        return TransformConfig(
            field=data.get("field", ""),
            operations=operations,
        )
