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
