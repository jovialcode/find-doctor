"""Rules management router."""

from pathlib import Path
from typing import Any

import yaml
from fastapi import APIRouter, HTTPException, UploadFile, status

from admin_api.schemas.rule import RuleResponse, RuleValidationResponse

router = APIRouter()

# Default rules directory (configurable)
RULES_DIR = Path("rules/hospitals")


@router.get("/", response_model=list[RuleResponse])
async def list_rules() -> list[dict[str, Any]]:
    """List all parsing rules.

    Returns:
        List of rules with basic info
    """
    rules: list[dict[str, Any]] = []

    if not RULES_DIR.exists():
        return rules

    for rule_file in RULES_DIR.glob("*.yaml"):
        try:
            with rule_file.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            site_info = data.get("site", {})
            rules.append({
                "id": site_info.get("id", rule_file.stem),
                "name": site_info.get("name", ""),
                "base_url": site_info.get("base_url", ""),
                "enabled": site_info.get("enabled", True),
                "file_path": str(rule_file),
                "targets_count": len(data.get("targets", [])),
            })
        except Exception:
            continue

    return rules


@router.get("/{rule_id}", response_model=dict[str, Any])
async def get_rule(rule_id: str) -> dict[str, Any]:
    """Get a rule by ID.

    Args:
        rule_id: Rule/site identifier

    Returns:
        Full rule data

    Raises:
        HTTPException: If rule not found
    """
    rule_path = RULES_DIR / f"{rule_id}.yaml"

    if not rule_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rule '{rule_id}' not found",
        )

    with rule_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@router.post("/validate", response_model=RuleValidationResponse)
async def validate_rule(file: UploadFile) -> dict[str, Any]:
    """Validate a rule file.

    Args:
        file: YAML rule file to validate

    Returns:
        Validation result
    """
    if not file.filename or not file.filename.endswith((".yaml", ".yml")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a YAML file",
        )

    content = await file.read()

    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as e:
        return {
            "valid": False,
            "errors": [f"YAML parse error: {e}"],
        }

    # Basic validation
    errors: list[str] = []

    if "site" not in data:
        errors.append("Missing 'site' section")
    else:
        site = data["site"]
        if not site.get("id"):
            errors.append("Missing site.id")
        if not site.get("name"):
            errors.append("Missing site.name")
        if not site.get("base_url"):
            errors.append("Missing site.base_url")

    if "targets" not in data or not data["targets"]:
        errors.append("Missing or empty 'targets' section")
    else:
        for i, target in enumerate(data["targets"]):
            if not target.get("name"):
                errors.append(f"Target {i}: missing name")
            if not target.get("url_pattern"):
                errors.append(f"Target {i}: missing url_pattern")
            if not target.get("selectors", {}).get("fields"):
                errors.append(f"Target {i}: missing selectors.fields")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
    }


@router.post("/{rule_id}", status_code=status.HTTP_201_CREATED)
async def create_rule(rule_id: str, file: UploadFile) -> dict[str, Any]:
    """Create or update a rule.

    Args:
        rule_id: Rule/site identifier
        file: YAML rule file

    Returns:
        Created/updated rule info

    Raises:
        HTTPException: If validation fails
    """
    if not file.filename or not file.filename.endswith((".yaml", ".yml")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a YAML file",
        )

    content = await file.read()

    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid YAML: {e}",
        )

    # Ensure rules directory exists
    RULES_DIR.mkdir(parents=True, exist_ok=True)

    # Save rule file
    rule_path = RULES_DIR / f"{rule_id}.yaml"
    rule_path.write_bytes(content)

    return {
        "id": rule_id,
        "file_path": str(rule_path),
        "message": "Rule created successfully",
    }


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(rule_id: str) -> None:
    """Delete a rule.

    Args:
        rule_id: Rule/site identifier

    Raises:
        HTTPException: If rule not found
    """
    rule_path = RULES_DIR / f"{rule_id}.yaml"

    if not rule_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rule '{rule_id}' not found",
        )

    rule_path.unlink()
