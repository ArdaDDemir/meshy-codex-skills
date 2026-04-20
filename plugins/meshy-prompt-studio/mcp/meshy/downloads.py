"""Asset download and local file helpers."""

from __future__ import annotations

import base64
import mimetypes
import os
from pathlib import Path
from typing import Any
import urllib.parse

from .errors import MeshyError


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
MODEL_EXTENSIONS = {".glb", ".gltf", ".obj", ".fbx", ".stl", ".usdz", ".3mf"}
RIG_MODEL_EXTENSIONS = {".glb"}
TEXTURE_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def file_to_data_uri(path_value: str, allowed_extensions: set[str]) -> str:
    path = Path(path_value).expanduser().resolve()
    if not path.exists() or not path.is_file():
        raise MeshyError(f"File does not exist: {path}")

    extension = path.suffix.lower()
    if extension not in allowed_extensions:
        allowed = ", ".join(sorted(allowed_extensions))
        raise MeshyError(f"Unsupported file extension '{extension}'. Supported: {allowed}")

    mime_type, _ = mimetypes.guess_type(str(path))
    if extension in MODEL_EXTENSIONS and not mime_type:
        mime_type = "application/octet-stream"
    if not mime_type:
        mime_type = "application/octet-stream"

    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def add_file_data_uri(
    payload: dict[str, Any],
    arguments: dict[str, Any],
    *,
    url_key: str,
    path_key: str,
    output_key: str,
    allowed_extensions: set[str],
) -> None:
    has_url = arguments.get(url_key) not in (None, "")
    has_path = arguments.get(path_key) not in (None, "")
    if has_url and has_path:
        raise MeshyError(f"Use either {url_key} or {path_key}, not both.")
    if has_url:
        payload[output_key] = arguments[url_key]
    elif has_path:
        payload[output_key] = file_to_data_uri(arguments[path_key], allowed_extensions)


def resolve_output_path(url: str, output_path: Any | None) -> Path:
    if output_path:
        return Path(str(output_path)).expanduser().resolve()

    output_dir = Path(os.environ.get("MESHY_OUTPUT_DIR", Path.cwd() / "meshy-downloads"))
    parsed = urllib.parse.urlparse(url)
    name = Path(parsed.path).name or "meshy-asset.bin"
    return (output_dir / name).expanduser().resolve()


def flatten_texture_urls(texture_urls: Any) -> dict[str, str]:
    flattened: dict[str, str] = {}
    if isinstance(texture_urls, dict):
        source = [texture_urls]
    elif isinstance(texture_urls, list):
        source = texture_urls
    else:
        source = []

    for item in source:
        if not isinstance(item, dict):
            continue
        for key, value in item.items():
            if isinstance(value, str) and value:
                flattened[str(key)] = value
    return flattened


def texture_filename(texture_name: str) -> str:
    normalized = texture_name.strip().lower().replace("-", "_")
    if normalized in {"basecolor", "base_color", "albedo"}:
        normalized = "base_color"
    safe = "".join(char if char.isalnum() or char in {"_", "-"} else "_" for char in normalized)
    return f"{safe or 'texture'}.png"
