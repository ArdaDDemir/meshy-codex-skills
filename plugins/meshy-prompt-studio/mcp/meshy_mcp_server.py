#!/usr/bin/env python3
"""Local MCP server for the Meshy API.

This server intentionally uses only the Python standard library so the plugin
can run without an install step. It supports stdio JSON-RPC MCP calls and a
small CLI for local credential setup and auth checks.
"""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
from pathlib import Path
import sys
import time
from typing import Any
import urllib.error
import urllib.parse
import urllib.request


BASE_URL = "https://api.meshy.ai"
APP_NAME = "meshy-prompt-studio"
TERMINAL_STATUSES = {"SUCCEEDED", "FAILED", "CANCELED"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
MODEL_EXTENSIONS = {".glb", ".gltf", ".obj", ".fbx", ".stl"}
RIG_MODEL_EXTENSIONS = {".glb"}
TEXTURE_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}

TASK_ENDPOINTS = {
    "text-to-3d": "/openapi/v2/text-to-3d",
    "image-to-3d": "/openapi/v1/image-to-3d",
    "multi-image-to-3d": "/openapi/v1/multi-image-to-3d",
    "remesh": "/openapi/v1/remesh",
    "retexture": "/openapi/v1/retexture",
    "rigging": "/openapi/v1/rigging",
    "animation": "/openapi/v1/animations",
    "animations": "/openapi/v1/animations",
}


class MeshyError(Exception):
    """Error type returned through MCP tool calls."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        details: Any | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"message": self.message}
        if self.status_code is not None:
            payload["status_code"] = self.status_code
        if self.details is not None:
            payload["details"] = self.details
        return payload


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


def compact_payload(arguments: dict[str, Any], allowed_keys: set[str]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for key in allowed_keys:
        if key not in arguments:
            continue
        value = arguments[key]
        if value is None:
            continue
        payload[key] = value
    return payload


def require_one_of(arguments: dict[str, Any], *keys: str) -> None:
    if not any(arguments.get(key) not in (None, "") for key in keys):
        raise MeshyError(f"One of {', '.join(keys)} is required.")


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


class MeshyHttpTransport:
    """HTTP transport for Meshy REST endpoints."""

    def __init__(self, base_url: str = BASE_URL, timeout_seconds: int = 60) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def request(
        self,
        method: str,
        path: str,
        api_key: str,
        payload: dict[str, Any] | None = None,
        query: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[Any]:
        url = self.base_url + path
        if query:
            query_string = urllib.parse.urlencode(query, doseq=True)
            url = f"{url}?{query_string}"

        data = None
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "User-Agent": "meshy-prompt-studio/1.1.0",
        }
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                body = response.read()
        except urllib.error.HTTPError as exc:
            body = exc.read()
            details = _decode_json_body(body)
            message = _extract_error_message(details) or f"Meshy API returned HTTP {exc.code}."
            raise MeshyError(message, status_code=exc.code, details=details) from exc
        except urllib.error.URLError as exc:
            raise MeshyError(f"Could not reach Meshy API: {exc.reason}") from exc

        if not body:
            return {}
        return _decode_json_body(body)

    def download(self, url: str) -> bytes:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme != "https":
            raise MeshyError("Only https asset URLs are supported.")

        try:
            with urllib.request.urlopen(url, timeout=self.timeout_seconds) as response:
                return response.read()
        except urllib.error.HTTPError as exc:
            details = _decode_json_body(exc.read())
            message = _extract_error_message(details) or f"Asset download returned HTTP {exc.code}."
            raise MeshyError(message, status_code=exc.code, details=details) from exc
        except urllib.error.URLError as exc:
            raise MeshyError(f"Could not download asset: {exc.reason}") from exc


def _decode_json_body(body: bytes) -> Any:
    if not body:
        return {}
    text = body.decode("utf-8", errors="replace")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"raw": text}


def _extract_error_message(details: Any) -> str | None:
    if isinstance(details, dict):
        for key in ("message", "error", "detail"):
            value = details.get(key)
            if isinstance(value, str) and value:
                return value
        task_error = details.get("task_error")
        if isinstance(task_error, dict):
            value = task_error.get("message")
            if isinstance(value, str) and value:
                return value
    return None


class MeshyClient:
    """Small Meshy API client used by MCP tools and tests."""

    def __init__(self, api_key: str, transport: Any | None = None) -> None:
        self.api_key = api_key
        self.transport = transport or MeshyHttpTransport()

    def get_balance(self) -> dict[str, Any] | list[Any]:
        return self.transport.request("GET", "/openapi/v1/balance", self.api_key)

    def check_auth(self) -> dict[str, Any]:
        balance = self.get_balance()
        return {"ok": True, "balance": balance.get("balance") if isinstance(balance, dict) else balance}

    def create_text_to_3d_preview(self, arguments: dict[str, Any]) -> dict[str, Any]:
        require_one_of(arguments, "prompt")
        allowed = {
            "ai_model",
            "art_style",
            "moderation",
            "model_type",
            "negative_prompt",
            "pose_mode",
            "prompt",
            "should_remesh",
            "symmetry_mode",
            "target_formats",
            "target_polycount",
            "topology",
            "auto_size",
        }
        payload = compact_payload(arguments, allowed)
        payload["mode"] = "preview"
        return self._create_task("/openapi/v2/text-to-3d", payload, "text-to-3d")

    def refine_text_to_3d(self, arguments: dict[str, Any]) -> dict[str, Any]:
        require_one_of(arguments, "preview_task_id")
        allowed = {
            "ai_model",
            "auto_size",
            "enable_pbr",
            "moderation",
            "preview_task_id",
            "remove_lighting",
            "target_formats",
            "texture_prompt",
        }
        payload = compact_payload(arguments, allowed)
        add_file_data_uri(
            payload,
            arguments,
            url_key="texture_image_url",
            path_key="texture_image_path",
            output_key="texture_image_url",
            allowed_extensions=TEXTURE_IMAGE_EXTENSIONS,
        )
        payload["mode"] = "refine"
        return self._create_task("/openapi/v2/text-to-3d", payload, "text-to-3d")

    def create_image_to_3d(self, arguments: dict[str, Any]) -> dict[str, Any]:
        require_one_of(arguments, "image_url", "image_path")
        allowed = {
            "ai_model",
            "auto_size",
            "enable_pbr",
            "image_enhancement",
            "moderation",
            "model_type",
            "pose_mode",
            "remove_lighting",
            "save_pre_remeshed_model",
            "should_remesh",
            "symmetry_mode",
            "target_formats",
            "target_polycount",
            "texture_prompt",
            "topology",
        }
        payload = compact_payload(arguments, allowed)
        add_file_data_uri(
            payload,
            arguments,
            url_key="image_url",
            path_key="image_path",
            output_key="image_url",
            allowed_extensions=IMAGE_EXTENSIONS,
        )
        add_file_data_uri(
            payload,
            arguments,
            url_key="texture_image_url",
            path_key="texture_image_path",
            output_key="texture_image_url",
            allowed_extensions=TEXTURE_IMAGE_EXTENSIONS,
        )
        return self._create_task("/openapi/v1/image-to-3d", payload, "image-to-3d")

    def create_multi_image_to_3d(self, arguments: dict[str, Any]) -> dict[str, Any]:
        image_urls = list(arguments.get("image_urls") or [])
        image_paths = list(arguments.get("image_paths") or [])
        if image_urls and image_paths:
            raise MeshyError("Use either image_urls or image_paths, not both.")
        if image_paths:
            image_urls = [file_to_data_uri(path, IMAGE_EXTENSIONS) for path in image_paths]
        if not 1 <= len(image_urls) <= 4:
            raise MeshyError("image_urls or image_paths must include 1 to 4 images.")

        allowed = {
            "ai_model",
            "auto_size",
            "enable_pbr",
            "image_enhancement",
            "moderation",
            "model_type",
            "pose_mode",
            "remove_lighting",
            "save_pre_remeshed_model",
            "should_remesh",
            "symmetry_mode",
            "target_formats",
            "target_polycount",
            "texture_prompt",
            "topology",
        }
        payload = compact_payload(arguments, allowed)
        payload["image_urls"] = image_urls
        return self._create_task("/openapi/v1/multi-image-to-3d", payload, "multi-image-to-3d")

    def remesh(self, arguments: dict[str, Any]) -> dict[str, Any]:
        require_one_of(arguments, "input_task_id", "model_url", "model_path")
        allowed = {"input_task_id", "target_formats", "target_polycount", "topology"}
        payload = compact_payload(arguments, allowed)
        add_file_data_uri(
            payload,
            arguments,
            url_key="model_url",
            path_key="model_path",
            output_key="model_url",
            allowed_extensions=MODEL_EXTENSIONS,
        )
        return self._create_task("/openapi/v1/remesh", payload, "remesh")

    def retexture(self, arguments: dict[str, Any]) -> dict[str, Any]:
        require_one_of(arguments, "input_task_id", "model_url", "model_path")
        require_one_of(arguments, "text_style_prompt", "image_style_url", "image_style_path")
        allowed = {"input_task_id", "text_style_prompt", "enable_pbr"}
        payload = compact_payload(arguments, allowed)
        add_file_data_uri(
            payload,
            arguments,
            url_key="model_url",
            path_key="model_path",
            output_key="model_url",
            allowed_extensions=MODEL_EXTENSIONS,
        )
        add_file_data_uri(
            payload,
            arguments,
            url_key="image_style_url",
            path_key="image_style_path",
            output_key="image_style_url",
            allowed_extensions=TEXTURE_IMAGE_EXTENSIONS,
        )
        return self._create_task("/openapi/v1/retexture", payload, "retexture")

    def rig_character(self, arguments: dict[str, Any]) -> dict[str, Any]:
        require_one_of(arguments, "input_task_id", "model_url", "model_path")
        allowed = {"input_task_id", "height_meters"}
        payload = compact_payload(arguments, allowed)
        add_file_data_uri(
            payload,
            arguments,
            url_key="model_url",
            path_key="model_path",
            output_key="model_url",
            allowed_extensions=RIG_MODEL_EXTENSIONS,
        )
        add_file_data_uri(
            payload,
            arguments,
            url_key="texture_image_url",
            path_key="texture_image_path",
            output_key="texture_image_url",
            allowed_extensions={".png"},
        )
        return self._create_task("/openapi/v1/rigging", payload, "rigging")

    def animate_character(self, arguments: dict[str, Any]) -> dict[str, Any]:
        require_one_of(arguments, "rig_task_id")
        if arguments.get("action_id") is None:
            raise MeshyError("action_id is required.")
        payload = compact_payload(arguments, {"rig_task_id", "action_id", "post_process"})
        return self._create_task("/openapi/v1/animations", payload, "animation")

    def get_task(self, arguments: dict[str, Any]) -> dict[str, Any] | list[Any]:
        task_type = str(arguments.get("task_type", "")).strip()
        task_id = str(arguments.get("task_id", "")).strip()
        if not task_type or not task_id:
            raise MeshyError("task_type and task_id are required.")
        endpoint = self._endpoint_for(task_type)
        return self.transport.request("GET", f"{endpoint}/{task_id}", self.api_key)

    def list_tasks(self, arguments: dict[str, Any]) -> dict[str, Any] | list[Any]:
        task_type = str(arguments.get("task_type", "")).strip()
        if not task_type:
            raise MeshyError("task_type is required.")
        endpoint = self._endpoint_for(task_type)
        query = compact_payload(arguments, {"page_num", "page_size", "sort_by"})
        return self.transport.request("GET", endpoint, self.api_key, query=query)

    def wait_for_task(self, arguments: dict[str, Any]) -> dict[str, Any] | list[Any]:
        timeout_seconds = float(arguments.get("timeout_seconds", 900))
        poll_interval_seconds = float(arguments.get("poll_interval_seconds", 5))
        started = time.monotonic()
        last_task: dict[str, Any] | list[Any] | None = None

        while True:
            last_task = self.get_task(arguments)
            status = last_task.get("status") if isinstance(last_task, dict) else None
            if status in TERMINAL_STATUSES:
                return last_task
            if time.monotonic() - started >= timeout_seconds:
                raise MeshyError(
                    f"Timed out waiting for task after {timeout_seconds:g} seconds.",
                    details=last_task,
                )
            if poll_interval_seconds > 0:
                time.sleep(poll_interval_seconds)

    def download_asset(self, arguments: dict[str, Any]) -> dict[str, Any]:
        url = str(arguments.get("url", "")).strip()
        if not url:
            raise MeshyError("url is required.")
        output_path = resolve_output_path(url, arguments.get("output_path"))
        overwrite = bool(arguments.get("overwrite", False))
        if output_path.exists() and not overwrite:
            raise MeshyError(f"Output file already exists: {output_path}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(self.transport.download(url))
        return {"path": str(output_path), "bytes": output_path.stat().st_size}

    def _create_task(
        self,
        endpoint: str,
        payload: dict[str, Any],
        task_type: str,
    ) -> dict[str, Any]:
        response = self.transport.request("POST", endpoint, self.api_key, payload=payload)
        if not isinstance(response, dict) or "result" not in response:
            raise MeshyError("Meshy API did not return a task id.", details=response)
        return {"task_id": response["result"], "task_type": task_type}

    def _endpoint_for(self, task_type: str) -> str:
        endpoint = TASK_ENDPOINTS.get(task_type)
        if not endpoint:
            allowed = ", ".join(sorted(TASK_ENDPOINTS))
            raise MeshyError(f"Unsupported task_type '{task_type}'. Supported: {allowed}")
        return endpoint


def resolve_output_path(url: str, output_path: Any | None) -> Path:
    if output_path:
        return Path(str(output_path)).expanduser().resolve()

    output_dir = Path(os.environ.get("MESHY_OUTPUT_DIR", Path.cwd() / "meshy-downloads"))
    parsed = urllib.parse.urlparse(url)
    name = Path(parsed.path).name or "meshy-asset.bin"
    return (output_dir / name).expanduser().resolve()


def client_from_config() -> MeshyClient:
    return MeshyClient(require_api_key())


def tool_content(payload: Any) -> dict[str, Any]:
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(payload, indent=2, ensure_ascii=False),
            }
        ]
    }


def tool_error(error: MeshyError) -> dict[str, Any]:
    return {
        "isError": True,
        "content": [
            {
                "type": "text",
                "text": json.dumps(error.to_dict(), indent=2, ensure_ascii=False),
            }
        ],
    }


def dispatch_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    try:
        if name == "meshy_configure_api_key":
            return tool_content(configure_api_key(arguments))

        client = client_from_config()
        handlers = {
            "meshy_check_auth": lambda _: client.check_auth(),
            "meshy_get_balance": lambda _: client.get_balance(),
            "meshy_create_text_to_3d_preview": lambda args: client.create_text_to_3d_preview(args),
            "meshy_refine_text_to_3d": lambda args: client.refine_text_to_3d(args),
            "meshy_create_image_to_3d": lambda args: client.create_image_to_3d(args),
            "meshy_create_multi_image_to_3d": lambda args: client.create_multi_image_to_3d(args),
            "meshy_get_task": lambda args: client.get_task(args),
            "meshy_list_tasks": lambda args: client.list_tasks(args),
            "meshy_wait_for_task": lambda args: client.wait_for_task(args),
            "meshy_download_asset": lambda args: client.download_asset(args),
            "meshy_remesh": lambda args: client.remesh(args),
            "meshy_retexture": lambda args: client.retexture(args),
            "meshy_rig_character": lambda args: client.rig_character(args),
            "meshy_animate_character": lambda args: client.animate_character(args),
        }
        handler = handlers.get(name)
        if handler is None:
            raise MeshyError(f"Unknown tool: {name}")
        return tool_content(handler(arguments))
    except MeshyError as exc:
        return tool_error(exc)
    except Exception as exc:  # Defensive boundary for MCP tool calls.
        return tool_error(MeshyError(f"Unexpected Meshy MCP server error: {exc}"))


def tool_schema(
    name: str,
    description: str,
    properties: dict[str, Any],
    required: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "name": name,
        "description": description,
        "inputSchema": {
            "type": "object",
            "properties": properties,
            "required": required or [],
            "additionalProperties": True,
        },
    }


TOOLS = [
    tool_schema(
        "meshy_configure_api_key",
        "Store a Meshy API key in a local credential file outside the repository. The key is never echoed back.",
        {"api_key": {"type": "string", "description": "Meshy API key starting with msy."}},
        ["api_key"],
    ),
    tool_schema("meshy_check_auth", "Verify Meshy API authentication by reading account balance.", {}),
    tool_schema("meshy_get_balance", "Retrieve the current Meshy API credit balance.", {}),
    tool_schema(
        "meshy_create_text_to_3d_preview",
        "Create a Meshy Text to 3D preview task.",
        {
            "prompt": {"type": "string"},
            "target_formats": {"type": "array", "items": {"type": "string"}},
            "model_type": {"type": "string"},
            "ai_model": {"type": "string"},
            "pose_mode": {"type": "string"},
            "should_remesh": {"type": "boolean"},
            "target_polycount": {"type": "integer"},
            "topology": {"type": "string"},
            "moderation": {"type": "boolean"},
        },
        ["prompt"],
    ),
    tool_schema(
        "meshy_refine_text_to_3d",
        "Create a Meshy Text to 3D refine task from a succeeded preview task.",
        {
            "preview_task_id": {"type": "string"},
            "texture_prompt": {"type": "string"},
            "texture_image_url": {"type": "string"},
            "texture_image_path": {"type": "string"},
            "enable_pbr": {"type": "boolean"},
            "target_formats": {"type": "array", "items": {"type": "string"}},
        },
        ["preview_task_id"],
    ),
    tool_schema(
        "meshy_create_image_to_3d",
        "Create a Meshy Image to 3D task from an image URL, data URI, or local image path.",
        {
            "image_url": {"type": "string"},
            "image_path": {"type": "string"},
            "texture_prompt": {"type": "string"},
            "target_formats": {"type": "array", "items": {"type": "string"}},
            "image_enhancement": {"type": "boolean"},
            "remove_lighting": {"type": "boolean"},
            "pose_mode": {"type": "string"},
            "model_type": {"type": "string"},
            "moderation": {"type": "boolean"},
        },
    ),
    tool_schema(
        "meshy_create_multi_image_to_3d",
        "Create a Meshy Multi-Image to 3D task from 1 to 4 image URLs or local image paths.",
        {
            "image_urls": {"type": "array", "items": {"type": "string"}},
            "image_paths": {"type": "array", "items": {"type": "string"}},
            "texture_prompt": {"type": "string"},
            "target_formats": {"type": "array", "items": {"type": "string"}},
        },
    ),
    tool_schema(
        "meshy_get_task",
        "Retrieve a Meshy task by task type and task ID.",
        {"task_type": {"type": "string"}, "task_id": {"type": "string"}},
        ["task_type", "task_id"],
    ),
    tool_schema(
        "meshy_list_tasks",
        "List Meshy tasks for a supported task type.",
        {
            "task_type": {"type": "string"},
            "page_num": {"type": "integer"},
            "page_size": {"type": "integer"},
            "sort_by": {"type": "string"},
        },
        ["task_type"],
    ),
    tool_schema(
        "meshy_wait_for_task",
        "Poll a Meshy task until it succeeds, fails, is canceled, or times out.",
        {
            "task_type": {"type": "string"},
            "task_id": {"type": "string"},
            "timeout_seconds": {"type": "number"},
            "poll_interval_seconds": {"type": "number"},
        },
        ["task_type", "task_id"],
    ),
    tool_schema(
        "meshy_download_asset",
        "Download a Meshy asset URL to a local path.",
        {
            "url": {"type": "string"},
            "output_path": {"type": "string"},
            "overwrite": {"type": "boolean"},
        },
        ["url"],
    ),
    tool_schema(
        "meshy_remesh",
        "Create a Meshy remesh task from a completed task ID, model URL, or local model path.",
        {
            "input_task_id": {"type": "string"},
            "model_url": {"type": "string"},
            "model_path": {"type": "string"},
            "target_formats": {"type": "array", "items": {"type": "string"}},
            "target_polycount": {"type": "integer"},
            "topology": {"type": "string"},
        },
    ),
    tool_schema(
        "meshy_retexture",
        "Create a Meshy retexture task from a completed task ID, model URL, or local model path.",
        {
            "input_task_id": {"type": "string"},
            "model_url": {"type": "string"},
            "model_path": {"type": "string"},
            "text_style_prompt": {"type": "string"},
            "image_style_url": {"type": "string"},
            "image_style_path": {"type": "string"},
            "enable_pbr": {"type": "boolean"},
        },
    ),
    tool_schema(
        "meshy_rig_character",
        "Create a Meshy auto-rigging task for a textured humanoid character.",
        {
            "input_task_id": {"type": "string"},
            "model_url": {"type": "string"},
            "model_path": {"type": "string"},
            "height_meters": {"type": "number"},
            "texture_image_url": {"type": "string"},
            "texture_image_path": {"type": "string"},
        },
    ),
    tool_schema(
        "meshy_animate_character",
        "Create a Meshy animation task from a succeeded rigging task ID and animation action ID.",
        {
            "rig_task_id": {"type": "string"},
            "action_id": {"type": "integer"},
            "post_process": {"type": "object"},
        },
        ["rig_task_id", "action_id"],
    ),
]


def handle_json_rpc(request: dict[str, Any]) -> dict[str, Any] | None:
    method = request.get("method")
    request_id = request.get("id")

    if method == "notifications/initialized":
        return None
    if method == "initialize":
        return json_rpc_result(
            request_id,
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "meshy-api", "version": "1.1.0"},
            },
        )
    if method == "tools/list":
        return json_rpc_result(request_id, {"tools": TOOLS})
    if method == "tools/call":
        params = request.get("params") or {}
        name = params.get("name")
        arguments = params.get("arguments") or {}
        return json_rpc_result(request_id, dispatch_tool(name, arguments))

    if request_id is None:
        return None
    return json_rpc_error(request_id, -32601, f"Method not found: {method}")


def json_rpc_result(request_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def json_rpc_error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def run_stdio_server() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            response = handle_json_rpc(request)
        except Exception as exc:
            response = json_rpc_error(None, -32700, f"Invalid request: {exc}")
        if response is not None:
            sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
            sys.stdout.flush()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Meshy API MCP server")
    parser.add_argument("--configure-api-key-stdin", action="store_true")
    parser.add_argument("--check-auth", action="store_true")
    parser.add_argument("--print-tools", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        if args.configure_api_key_stdin:
            key = sys.stdin.read().strip()
            print(json.dumps(configure_api_key({"api_key": key}), indent=2))
            return 0
        if args.check_auth:
            print(json.dumps(client_from_config().check_auth(), indent=2))
            return 0
        if args.print_tools:
            print(json.dumps({"tools": TOOLS}, indent=2))
            return 0
        run_stdio_server()
        return 0
    except MeshyError as exc:
        print(json.dumps(exc.to_dict(), indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
