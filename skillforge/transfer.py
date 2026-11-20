from __future__ import annotations

from typing import Any

from .compiler import compile_skill
from .runtime import run_compiled


def evaluate_transfer(skill: dict[str, Any], tasks: list[dict[str, Any]], source_task_ids: set[str]) -> dict[str, Any]:
    """Evaluate a fixed skill on source and held-out target tasks.

    This V0.1 evaluator measures procedural transfer on deterministic tasks. It is
    not a substitute for SkillFlow/AFTER or model-based agent evaluation.
    """
    compiled = compile_skill(skill)
    rows = []
    for task in tasks:
        expected = task["expected"]
        try:
            actual = run_compiled(compiled, task["input"])
            passed = actual == expected
            error = None
        except Exception as exc:
            actual = None
            passed = False
            error = str(exc)
        rows.append({
            "task_id": task["id"],
            "split": "source" if task["id"] in source_task_ids else "held_out",
            "passed": passed,
            "actual": actual,
            "expected": expected,
            "error": error,
        })
    source = [row for row in rows if row["split"] == "source"]
    held_out = [row for row in rows if row["split"] == "held_out"]
    return {
        "skill_id": skill["id"],
        "source_success_rate": _rate(source),
        "held_out_success_rate": _rate(held_out),
        "overall_success_rate": _rate(rows),
        "rows": rows,
    }


def evaluate_identity_baseline(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for task in tasks:
        value = task["input"].get("text")
        actual = {"slug": value}
        rows.append({"task_id": task["id"], "passed": actual == task["expected"], "actual": actual, "expected": task["expected"]})
    return {"baseline": "identity_no_skill", "success_rate": _rate(rows), "rows": rows}


def _rate(rows: list[dict[str, Any]]) -> float:
    return round(sum(1 for row in rows if row["passed"]) / len(rows), 4) if rows else 0.0


def evaluate_single_space_baseline(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    """A deliberately simple heuristic baseline: strip, lowercase, replace ASCII spaces.

    It does not collapse tabs/newlines or repeated whitespace. This is a more
    informative control than identity-only while remaining clearly weaker than
    the learned split/join procedure.
    """
    rows = []
    for task in tasks:
        value = task["input"].get("text", "")
        actual = {"slug": value.strip().lower().replace(" ", "-")}
        rows.append({"task_id": task["id"], "passed": actual == task["expected"], "actual": actual, "expected": task["expected"]})
    return {"baseline": "strip_lower_replace_ascii_space", "success_rate": _rate(rows), "rows": rows}
