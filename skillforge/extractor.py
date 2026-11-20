from __future__ import annotations

from copy import deepcopy
from typing import Any


class ExtractionError(ValueError):
    pass


def extract_skill_from_trace(
    trace: dict[str, Any],
    *,
    skill_id: str,
    name: str,
    input_schema: dict[str, str],
    output_schema: dict[str, str],
    output_map: dict[str, dict[str, str]],
    tests: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Convert a structured, successful execution trace into a candidate Skill IR.

    V0.1 intentionally accepts structured operation traces. It does not pretend to
    infer robust abstractions from arbitrary natural-language logs; that is a later
    LLM-assisted extraction stage.
    """
    steps = trace.get("steps")
    if not isinstance(steps, list) or not steps:
        raise ExtractionError("trace must contain a non-empty 'steps' array")
    for step in steps:
        if not isinstance(step, dict) or not {"id", "op", "args"}.issubset(step):
            raise ExtractionError("each trace step requires id, op, and args")
    return {
        "schema_version": "0.1",
        "id": skill_id,
        "version": "0.1.0",
        "name": name,
        "description": "Extracted from a structured successful execution trace.",
        "inputs": deepcopy(input_schema),
        "outputs": deepcopy(output_schema),
        "steps": deepcopy(steps),
        "output_map": deepcopy(output_map),
        "preconditions": [],
        "postconditions": [],
        "tests": deepcopy(tests or []),
        "provenance": {
            "method": "structured_trace_extraction",
            "trace_id": trace.get("trace_id", "unknown"),
            "source_task": trace.get("task_id", "unknown"),
        },
    }
