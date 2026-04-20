"""Input normalization and validation for Meshy API calls."""

from __future__ import annotations

import re
from typing import Any

from .errors import MeshyError


SUPPORTED_TARGET_FORMATS = {"glb", "obj", "fbx", "stl", "usdz", "3mf"}
SUPPORTED_MODEL_TYPES = {"standard", "lowpoly"}
SUPPORTED_TOPOLOGIES = {"quad", "triangle"}
SUPPORTED_SYMMETRY_MODES = {"off", "auto", "on"}
SUPPORTED_AI_MODELS = {"meshy-5", "meshy-6", "latest"}
MESHY_COSTS_AS_OF = "2026-04-20"
MESHY_API_COSTS = {
    "text_to_3d_preview_meshy_6": 20,
    "text_to_3d_preview_other": 10,
    "text_to_3d_refine": 10,
    "image_to_3d_meshy_6_without_texture": 20,
    "image_to_3d_meshy_6_with_texture": 30,
    "image_to_3d_other_without_texture": 5,
    "image_to_3d_other_with_texture": 15,
    "multi_image_to_3d_without_texture": 5,
    "multi_image_to_3d_with_texture": 15,
    "retexture": 10,
    "remesh": 5,
    "auto_rigging": 5,
    "animation": 3,
}
POSE_MODE_ALIASES = {
    "": "",
    "apose": "a-pose",
    "a-pose": "a-pose",
    "a pose": "a-pose",
    "a_pose": "a-pose",
    "tpose": "t-pose",
    "t-pose": "t-pose",
    "t pose": "t-pose",
    "t_pose": "t-pose",
}


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


def normalize_pose_mode(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip().lower()
    compact = re.sub(r"[\s_-]+", "", text)
    if compact in {"", "none", "no"}:
        return ""
    normalized = POSE_MODE_ALIASES.get(text) or POSE_MODE_ALIASES.get(compact)
    if normalized is None:
        raise MeshyError("Unsupported pose_mode. Supported values: a-pose, t-pose, or empty.")
    return normalized


def normalize_target_formats(value: Any, *, default: list[str] | None = None) -> list[str] | None:
    if value in (None, ""):
        return list(default) if default is not None else None
    if isinstance(value, str):
        raw_values = [item.strip() for item in value.split(",")]
    else:
        raw_values = list(value)

    formats: list[str] = []
    for raw_value in raw_values:
        target_format = str(raw_value).strip().lower()
        if not target_format:
            continue
        if target_format not in SUPPORTED_TARGET_FORMATS:
            allowed = ", ".join(sorted(SUPPORTED_TARGET_FORMATS))
            raise MeshyError(
                f"Unsupported target format '{raw_value}'. Supported target_formats: {allowed}."
            )
        if target_format not in formats:
            formats.append(target_format)
    if not formats:
        return list(default) if default is not None else None
    return formats


def normalize_choice(
    payload: dict[str, Any],
    key: str,
    allowed: set[str],
    *,
    label: str | None = None,
) -> None:
    if key not in payload or payload[key] in (None, ""):
        return
    value = str(payload[key]).strip().lower()
    if value not in allowed:
        allowed_text = ", ".join(sorted(allowed))
        raise MeshyError(f"Unsupported {label or key} '{payload[key]}'. Supported: {allowed_text}.")
    payload[key] = value


def validate_prompt_length(prompt: Any, *, field_name: str = "prompt") -> None:
    if prompt is None:
        return
    if len(str(prompt)) > 600:
        raise MeshyError(f"{field_name} must be 600 characters or fewer.")


def normalize_text_to_3d_preview_payload(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(payload)
    validate_prompt_length(normalized.get("prompt"))
    if "pose_mode" in normalized:
        normalized["pose_mode"] = normalize_pose_mode(normalized.get("pose_mode"))
    if "target_formats" in normalized:
        normalized["target_formats"] = normalize_target_formats(normalized.get("target_formats"))
    normalize_choice(normalized, "model_type", SUPPORTED_MODEL_TYPES)
    normalize_choice(normalized, "topology", SUPPORTED_TOPOLOGIES)
    normalize_choice(normalized, "symmetry_mode", SUPPORTED_SYMMETRY_MODES)
    normalize_choice(normalized, "ai_model", SUPPORTED_AI_MODELS)
    return normalized


def normalize_text_to_3d_refine_payload(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(payload)
    validate_prompt_length(normalized.get("texture_prompt"), field_name="texture_prompt")
    if "target_formats" in normalized:
        normalized["target_formats"] = normalize_target_formats(normalized.get("target_formats"))
    normalize_choice(normalized, "ai_model", SUPPORTED_AI_MODELS)
    return normalized


def validate_texture_guidance(arguments: dict[str, Any]) -> None:
    has_prompt = arguments.get("texture_prompt") not in (None, "")
    has_image = arguments.get("texture_image_url") not in (None, "") or arguments.get(
        "texture_image_path"
    ) not in (None, "")
    if has_prompt and has_image:
        raise MeshyError("Use either texture_prompt or texture_image_url/texture_image_path, not both.")


def sanitize_asset_name(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[^a-z0-9._-]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-._")
    return text or "asset"


def estimate_text_to_3d_credits(preview_payload: dict[str, Any], *, refine: bool) -> int:
    model_type = str(preview_payload.get("model_type", "standard")).strip().lower()
    ai_model = str(preview_payload.get("ai_model", "latest")).strip().lower()
    preview_credits = (
        MESHY_API_COSTS["text_to_3d_preview_meshy_6"]
        if model_type == "lowpoly" or ai_model in {"latest", "meshy-6", ""}
        else MESHY_API_COSTS["text_to_3d_preview_other"]
    )
    return preview_credits + (MESHY_API_COSTS["text_to_3d_refine"] if refine else 0)


def extract_balance_value(balance_payload: Any) -> int | float | None:
    if isinstance(balance_payload, dict):
        balance = balance_payload.get("balance")
    else:
        balance = balance_payload
    if isinstance(balance, (int, float)):
        return balance
    try:
        return float(balance)
    except (TypeError, ValueError):
        return None
