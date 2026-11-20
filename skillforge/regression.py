from __future__ import annotations

from typing import Any

from .runtime import run_skill
from .contracts import check_conditions


def _stable_key(value: Any) -> str:
    import json
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def run_historical_regression(candidate: dict[str, Any], historical_skills: list[dict[str, Any]]) -> dict[str, Any]:
    """Replay every unique test case ever accepted for this skill against candidate."""
    cases: list[dict[str, Any]] = []
    seen: set[str] = set()
    for historical in historical_skills:
        for test in historical.get("tests", []):
            case = {
                "name": test.get("name", "unnamed"),
                "input": test.get("input", {}),
                "expected": test.get("expected", {}),
                "source_version": historical.get("version"),
                "preconditions": historical.get("preconditions", []),
                "postconditions": historical.get("postconditions", []),
            }
            key = _stable_key({
                "input": case["input"],
                "expected": case["expected"],
                "preconditions": case["preconditions"],
                "postconditions": case["postconditions"],
            })
            if key not in seen:
                seen.add(key)
                cases.append(case)

    results = []
    passed = 0
    for case in cases:
        try:
            contract_context = {"input": case["input"], "output": {}}
            check_conditions(case["preconditions"], contract_context, "historical precondition")
            actual = run_skill(candidate, case["input"])
            contract_context["output"] = actual
            check_conditions(case["postconditions"], contract_context, "historical postcondition")
            ok = actual == case["expected"]
            error = None if ok else "output_mismatch"
        except Exception as exc:
            actual = None
            ok = False
            error = f"{type(exc).__name__}: {exc}"
        passed += int(ok)
        results.append({**case, "actual": actual, "passed": ok, "error": error})

    failed = len(results) - passed
    return {
        "passed": failed == 0,
        "total": len(results),
        "passed_count": passed,
        "failed_count": failed,
        "success_rate": passed / len(results) if results else 1.0,
        "cases": results,
    }
