from __future__ import annotations

from typing import Any

from .types import matches_type


class ContractError(ValueError):
    pass


def get_path(context: dict[str, Any], path: str) -> Any:
    parts = path.split(".")
    current: Any = context
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            raise ContractError(f"contract path {path!r} does not exist")
    return current


def check_condition(condition: dict[str, Any], context: dict[str, Any]) -> bool:
    path = condition.get("path")
    op = condition.get("op")
    if not isinstance(path, str) or not isinstance(op, str):
        raise ContractError("condition requires string 'path' and 'op'")
    value = get_path(context, path)
    target = condition.get("value")
    if op == "non_empty":
        return value is not None and value != "" and value != [] and value != {}
    if op == "is_type":
        return matches_type(value, str(target))
    if op == "eq":
        return value == target
    if op == "ne":
        return value != target
    if op == "gte":
        return value >= target
    if op == "lte":
        return value <= target
    if op == "contains":
        return target in value
    if op == "lowercase":
        return isinstance(value, str) and value == value.lower()
    if op == "no_whitespace":
        return isinstance(value, str) and not any(ch.isspace() for ch in value)
    raise ContractError(f"unsupported contract operator {op!r}")


def check_conditions(conditions: list[dict[str, Any]], context: dict[str, Any], stage: str) -> None:
    for index, condition in enumerate(conditions):
        try:
            passed = check_condition(condition, context)
        except (TypeError, ContractError) as exc:
            raise ContractError(f"{stage} condition #{index + 1} invalid: {exc}") from exc
        if not passed:
            raise ContractError(f"{stage} condition #{index + 1} failed: {condition}")
