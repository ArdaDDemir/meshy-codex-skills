"""JSONL history helpers for Meshy workflows."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def default_history_path() -> Path:
    return Path.cwd() / ".meshy" / "history.jsonl"


def append_history_record(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def iter_history_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            records.append({"line": line_number, "error": "invalid_json", "raw": line})
            continue
        if isinstance(record, dict):
            records.append(record)
    return records


def find_history_record(path: Path, query: str) -> dict[str, Any] | None:
    normalized_query = query.strip().lower()
    if not normalized_query:
        return None
    for record in reversed(iter_history_records(path)):
        candidates = [
            record.get("asset_name"),
            record.get("asset_slug"),
            record.get("preview_task_id"),
            record.get("refine_task_id"),
        ]
        for candidate in candidates:
            if str(candidate or "").strip().lower() == normalized_query:
                return record
    return None


def latest_task_id(record: dict[str, Any]) -> str | None:
    for key in ("latest_task_id", "refine_task_id", "preview_task_id"):
        value = str(record.get(key) or "").strip()
        if value:
            return value
    return None


def manifest_path_from_record(record: dict[str, Any]) -> Path | None:
    manifest_path = str(record.get("manifest_path") or "").strip()
    if manifest_path:
        return Path(manifest_path).expanduser().resolve()

    asset_dir = str(record.get("asset_dir") or "").strip()
    if asset_dir:
        return (Path(asset_dir).expanduser().resolve() / "manifest.json").resolve()
    return None
