"""Credential storage for Meshy Prompt Studio.

The credential file intentionally lives outside the repository so API keys do
not get committed with plugin source files.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .errors import MeshyError


APP_NAME = "meshy-prompt-studio"


def credential_path() -> Path:
    override = os.environ.get("MESHY_CREDENTIALS_PATH")
    if override:
        return Path(override).expanduser()

    if os.name == "nt":
        app_data = os.environ.get("APPDATA")
        base = Path(app_data) if app_data else Path.home() / "AppData" / "Roaming"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))

    return base / APP_NAME / "credentials.json"


def configure_api_key(arguments: dict[str, Any]) -> dict[str, Any]:
    api_key = str(arguments.get("api_key", "")).strip()
    if not api_key:
        raise MeshyError("api_key is required.")
    if not api_key.startswith("msy"):
        raise MeshyError("Meshy API keys should start with 'msy'.")

    path = credential_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"api_key": api_key}, indent=2) + "\n", encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass

    return {
        "configured": True,
        "credential_path": str(path),
        "source": "credential_file",
        "message": "Meshy API key configured locally. The key is not included in this response.",
    }


def resolve_api_key() -> str | None:
    env_key = os.environ.get("MESHY_API_KEY", "").strip()
    if env_key:
        return env_key

    path = credential_path()
    if not path.exists():
        return None

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MeshyError(f"Could not read Meshy credentials from {path}: {exc}") from exc

    api_key = str(payload.get("api_key", "")).strip()
    return api_key or None


def require_api_key() -> str:
    api_key = resolve_api_key()
    if not api_key:
        raise MeshyError(
            "No Meshy API key configured. Set MESHY_API_KEY or call meshy_configure_api_key."
        )
    return api_key
