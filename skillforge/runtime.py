from __future__ import annotations

from copy import deepcopy
from typing import Any

from .compiler import CompiledSkill, compile_skill
from .contracts import check_conditions
from .operations import execute_operation
from .types import matches_type


class ExecutionError(RuntimeError):
    pass


def _resolve(value: Any, context: dict[str, Any]) -> Any:
    if isinstance(value, dict) and set(value) == {"$ref"}:
        path = value["$ref"].split(".")
        current: Any = context
        for part in path:
            if not isinstance(current, dict) or part not in current:
                raise ExecutionError(f"reference {value['$ref']!r} cannot be resolved")
            current = current[part]
        return current
    if isinstance(value, dict):
        return {key: _resolve(item, context) for key, item in value.items()}
    if isinstance(value, list):
        return [_resolve(item, context) for item in value]
    return deepcopy(value)


def run_compiled(compiled: CompiledSkill, inputs: dict[str, Any]) -> dict[str, Any]:
    skill = compiled.source
    if not isinstance(inputs, dict):
        raise ExecutionError("inputs must be an object")
    missing = set(skill["inputs"]) - set(inputs)
    extra = set(inputs) - set(skill["inputs"])
    if missing:
        raise ExecutionError(f"missing required inputs: {sorted(missing)}")
    if extra:
        raise ExecutionError(f"unexpected inputs: {sorted(extra)}")
    for name, expected_type in skill["inputs"].items():
        if not matches_type(inputs[name], expected_type):
            raise ExecutionError(f"input {name!r} expects {expected_type}, got {type(inputs[name]).__name__}")

    context: dict[str, Any] = {"input": deepcopy(inputs), "step": {}, "output": {}}
    try:
        check_conditions(skill.get("preconditions", []), context, "precondition")
        for step in compiled.ordered_steps:
            args = _resolve(step.get("args", {}), context)
            context["step"][step["id"]] = execute_operation(step["op"], args)
        outputs = {
            name: _resolve(ref, context)
            for name, ref in skill["output_map"].items()
        }
        for name, expected_type in skill["outputs"].items():
            if not matches_type(outputs[name], expected_type):
                raise ExecutionError(f"output {name!r} expected {expected_type}, got {type(outputs[name]).__name__}")
        context["output"] = outputs
        check_conditions(skill.get("postconditions", []), context, "postcondition")
        return outputs
    except Exception as exc:
        if isinstance(exc, ExecutionError):
            raise
        raise ExecutionError(str(exc)) from exc


def run_skill(skill: dict[str, Any] | CompiledSkill, inputs: dict[str, Any]) -> dict[str, Any]:
    compiled = skill if isinstance(skill, CompiledSkill) else compile_skill(skill)
    return run_compiled(compiled, inputs)
