from __future__ import annotations

from typing import Any

SUPPORTED_TYPES = {"string", "integer", "number", "boolean", "object", "array", "any"}


def type_name(value: Any) -> str:
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    if value is None:
        return "null"
    return "unknown"


def is_compatible(actual: str, expected: str) -> bool:
    if expected == "any" or actual == "any":
        return True
    if actual == expected:
        return True
    return actual == "integer" and expected == "number"


def matches_type(value: Any, expected: str) -> bool:
    actual = type_name(value)
    return is_compatible(actual, expected)
