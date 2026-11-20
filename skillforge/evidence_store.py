from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable


class EvidenceStore:
    """Append-only store for independently verified repair outcomes.

    Records are deliberately explicit about label provenance. Synthetic benchmark
    labels and real validation labels must never be silently mixed.
    """

    SCHEMA_VERSION = "1.0"

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch(exist_ok=True)

    def append(self, record: dict[str, Any]) -> dict[str, Any]:
        item = dict(record)
        item.setdefault("schema_version", self.SCHEMA_VERSION)
        item.setdefault("label_source", "verified_runtime")
        required = {"features", "root_cause_correct", "functional_fix", "no_regression", "solve_distance"}
        missing = required - set(item)
        if missing:
            raise ValueError(f"evidence record missing fields: {sorted(missing)}")
        if not isinstance(item["features"], dict):
            raise TypeError("features must be a dictionary")
        identity = {key: value for key, value in item.items() if key not in {"event_id", "timestamp"}}
        digest = hashlib.sha256(json.dumps(identity, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:20]
        item.setdefault("event_id", digest)
        existing = {row.get("event_id") for row in self.read_all()}
        if item["event_id"] not in existing:
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n")
        return item

    def extend(self, records: Iterable[dict[str, Any]]) -> int:
        count = 0
        for record in records:
            before = len(self.read_all())
            self.append(record)
            count += int(len(self.read_all()) > before)
        return count

    def read_all(self, *, label_source: str | None = None) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        if not self.path.exists():
            return rows
        with self.path.open("r", encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"invalid evidence JSONL at line {line_no}: {exc}") from exc
                if label_source is None or row.get("label_source") == label_source:
                    rows.append(row)
        return rows

    def summary(self) -> dict[str, Any]:
        rows = self.read_all()
        by_source: dict[str, int] = {}
        for row in rows:
            source = row.get("label_source", "unknown")
            by_source[source] = by_source.get(source, 0) + 1
        return {"path": str(self.path), "records": len(rows), "by_label_source": by_source}
