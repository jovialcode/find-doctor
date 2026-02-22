"""Parse tasks for Airflow."""

from pathlib import Path
from typing import Any

from collector.parser.base import FieldRule, ParserRule
from collector.parser.selector_parser import SelectorParser
from collector.rules.loader import RuleLoader
from collector.rules.models import SiteRule, TargetRule
from collector.storage.local import LocalStorage
from collector.storage.writer import StorageWriter


def _convert_to_parser_rule(target: TargetRule) -> ParserRule:
    """Convert TargetRule to ParserRule.

    Args:
        target: Target rule from YAML

    Returns:
        ParserRule for the parser
    """
    fields = [
        FieldRule(
            name=name,
            selector=field_sel.selector,
            type=field_sel.type,
            attribute=field_sel.attribute,
            default=field_sel.default,
        )
        for name, field_sel in target.selectors.fields.items()
    ]

    return ParserRule(
        name=target.name,
        container=target.selectors.container,
        item=target.selectors.item,
        fields=fields,
    )


def parse_crawled_data(
    site_id: str,
    target_name: str,
    rules_dir: str,
    input_dir: str,
    output_dir: str,
) -> dict[str, Any]:
    """Parse crawled HTML files for a target.

    Args:
        site_id: Site identifier
        target_name: Target name
        rules_dir: Directory containing rule files
        input_dir: Directory containing crawled HTML files
        output_dir: Directory for parsed output

    Returns:
        Parse summary
    """
    # Load rule
    loader = RuleLoader(rules_dir)
    site_rule = loader.load_rule(site_id)

    target = site_rule.get_target(target_name)
    if target is None:
        raise ValueError(f"Target '{target_name}' not found in site '{site_id}'")

    # Create parser
    parser = SelectorParser()
    parser_rule = _convert_to_parser_rule(target)

    # Load storage
    input_storage = LocalStorage(input_dir)
    output_storage = LocalStorage(output_dir)
    writer = StorageWriter(output_storage)

    # Find all HTML files for this target
    html_prefix = f"raw/{site_id}/{target_name}"
    html_files = input_storage.list_files(html_prefix)
    html_files = [f for f in html_files if f.endswith(".html")]

    all_parsed_data: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    for html_file in html_files:
        try:
            html_content = input_storage.load_text(html_file)
            result = parser.parse(html_content, parser_rule, source_url=html_file)

            if result.is_success:
                all_parsed_data.extend(result.data)
            else:
                errors.append({
                    "file": html_file,
                    "errors": list(result.errors),
                })

        except Exception as e:
            errors.append({
                "file": html_file,
                "error": str(e),
            })

    # Save parsed data
    if all_parsed_data:
        writer.save_parsed_data(site_id, target_name, all_parsed_data)

    return {
        "site_id": site_id,
        "target_name": target_name,
        "files_processed": len(html_files),
        "items_parsed": len(all_parsed_data),
        "error_count": len(errors),
        "errors": errors,
    }


def parse_all_targets(
    site_id: str,
    rules_dir: str,
    input_dir: str,
    output_dir: str,
) -> dict[str, Any]:
    """Parse all targets for a site.

    Args:
        site_id: Site identifier
        rules_dir: Directory containing rule files
        input_dir: Directory containing crawled HTML files
        output_dir: Directory for parsed output

    Returns:
        Parse summary for all targets
    """
    # Load rule
    loader = RuleLoader(rules_dir)
    site_rule = loader.load_rule(site_id)

    results: list[dict[str, Any]] = []

    for target in site_rule.targets:
        try:
            result = parse_crawled_data(
                site_id=site_id,
                target_name=target.name,
                rules_dir=rules_dir,
                input_dir=input_dir,
                output_dir=output_dir,
            )
            results.append(result)
        except Exception as e:
            results.append({
                "site_id": site_id,
                "target_name": target.name,
                "error": str(e),
            })

    total_items = sum(r.get("items_parsed", 0) for r in results)
    total_errors = sum(r.get("error_count", 0) for r in results)

    return {
        "site_id": site_id,
        "targets_parsed": len(results),
        "total_items": total_items,
        "total_errors": total_errors,
        "results": results,
    }
