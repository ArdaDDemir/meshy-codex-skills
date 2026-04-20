#!/usr/bin/env python3
"""Scan tracked repository files for likely private Meshy secrets."""

from __future__ import annotations

from pathlib import Path
import re
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
PUBLIC_TEST_KEY = "msy_dummy_api_key_for_test_mode_12345678"
SECRET_PATTERN = re.compile(r"msy_[A-Za-z0-9_\\-]{20,}")
ALLOWED_KEYS = {
    PUBLIC_TEST_KEY,
    "msy_your_key_here",
    "msy_test_secret",
    "msy_test_key",
    "msy_from_env",
    "msy_from_file",
}
IGNORED_SUFFIXES = {".png", ".jpg", ".jpeg", ".glb", ".fbx", ".stl", ".3mf", ".usdz", ".zip"}


def main() -> int:
    findings = find_private_meshy_keys(REPO_ROOT, git_ls_files(REPO_ROOT))
    if findings:
        for finding in findings:
            print(f"FAIL: {finding}", file=sys.stderr)
        return 1
    print("ok: no private Meshy API keys found in tracked files")
    return 0


def find_private_meshy_keys(repo_root: Path, tracked_files: list[str]) -> list[str]:
    findings: list[str] = []
    for path in tracked_files:
        full_path = repo_root / path
        if full_path.suffix.lower() in IGNORED_SUFFIXES:
            continue
        text = full_path.read_text(encoding="utf-8", errors="ignore")
        for match in SECRET_PATTERN.findall(text):
            if match not in ALLOWED_KEYS:
                findings.append(f"{path}: {match[:8]}...")
    return findings


def git_ls_files(repo_root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=repo_root,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    )
    return [line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()]


if __name__ == "__main__":
    raise SystemExit(main())
