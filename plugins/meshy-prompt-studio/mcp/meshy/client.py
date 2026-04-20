"""Meshy REST client used by MCP tools, workflows, and CLI commands."""

from __future__ import annotations

import json
import time
from typing import Any
import urllib.error
import urllib.parse
import urllib.request

from .credentials import require_api_key
from .downloads import (
    IMAGE_EXTENSIONS,
    MODEL_EXTENSIONS,
    RIG_MODEL_EXTENSIONS,
    TEXTURE_IMAGE_EXTENSIONS,
    add_file_data_uri,
    file_to_data_uri,
    resolve_output_path,
)
from .errors import MeshyError
from .validation import (
    compact_payload,
    normalize_text_to_3d_preview_payload,
    normalize_text_to_3d_refine_payload,
    normalize_target_formats,
    require_one_of,
    validate_texture_guidance,
)


BASE_URL = "https://api.meshy.ai"
TERMINAL_STATUSES = {"SUCCEEDED", "FAILED", "CANCELED"}

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
            "User-Agent": "meshy-prompt-studio/1.4.0",
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
            "auto_size",
            "decimation_mode",
            "moderation",
            "model_type",
            "negative_prompt",
            "origin_at",
            "pose_mode",
            "prompt",
            "should_remesh",
            "symmetry_mode",
            "target_formats",
            "target_polycount",
            "topology",
        }
        payload = normalize_text_to_3d_preview_payload(compact_payload(arguments, allowed))
        payload["mode"] = "preview"
        return self._create_task("/openapi/v2/text-to-3d", payload, "text-to-3d")

    def refine_text_to_3d(self, arguments: dict[str, Any]) -> dict[str, Any]:
        require_one_of(arguments, "preview_task_id")
        validate_texture_guidance(arguments)
        allowed = {
            "ai_model",
            "auto_size",
            "enable_pbr",
            "moderation",
            "origin_at",
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
        payload = normalize_text_to_3d_refine_payload(payload)
        payload["mode"] = "refine"
        return self._create_task("/openapi/v2/text-to-3d", payload, "text-to-3d")

    def create_image_to_3d(self, arguments: dict[str, Any]) -> dict[str, Any]:
        require_one_of(arguments, "image_url", "image_path")
        validate_texture_guidance(arguments)
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
        payload = normalize_text_to_3d_preview_payload(compact_payload(arguments, allowed))
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
        validate_texture_guidance(arguments)
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
        payload = normalize_text_to_3d_preview_payload(compact_payload(arguments, allowed))
        payload["image_urls"] = image_urls
        return self._create_task("/openapi/v1/multi-image-to-3d", payload, "multi-image-to-3d")

    def remesh(self, arguments: dict[str, Any]) -> dict[str, Any]:
        require_one_of(arguments, "input_task_id", "model_url", "model_path")
        allowed = {"input_task_id", "target_formats", "target_polycount", "topology"}
        payload = compact_payload(arguments, allowed)
        if "target_formats" in payload:
            payload["target_formats"] = normalize_target_formats(payload["target_formats"])
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

    def create_text_to_3d_asset_pack(self, arguments: dict[str, Any]) -> dict[str, Any]:
        from .workflows import create_text_to_3d_asset_pack

        return create_text_to_3d_asset_pack(self, arguments)

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


def client_from_config() -> MeshyClient:
    return MeshyClient(require_api_key())
