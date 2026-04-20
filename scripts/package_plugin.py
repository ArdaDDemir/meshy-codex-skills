#!/usr/bin/env python3
"""Package the Meshy Prompt Studio plugin as a release zip."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import zipfile


REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_DIR = REPO_ROOT / "plugins" / "meshy-prompt-studio"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Package Meshy Prompt Studio")
    parser.add_argument("--out-dir", default="dist")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_path = PLUGIN_DIR / ".codex-plugin" / "plugin.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    name = manifest["name"]
    version = manifest["version"]

    out_dir = (REPO_ROOT / args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    zip_path = out_dir / f"{name}-{version}.zip"
    if zip_path.exists():
        zip_path.unlink()

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(PLUGIN_DIR.rglob("*")):
            if should_skip(path):
                continue
            archive.write(path, path.relative_to(PLUGIN_DIR).as_posix())

    print(json.dumps({"package": str(zip_path), "bytes": zip_path.stat().st_size}, indent=2))
    return 0


def should_skip(path: Path) -> bool:
    parts = set(path.parts)
    if path.is_dir():
        return True
    if "__pycache__" in parts:
        return True
    if path.suffix in {".pyc", ".pyo"}:
        return True
    return False


if __name__ == "__main__":
    raise SystemExit(main())
