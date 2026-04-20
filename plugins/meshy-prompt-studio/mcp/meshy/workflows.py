"""One-command Meshy asset pack workflows."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from .downloads import flatten_texture_urls, texture_filename
from .errors import MeshyError
from .history import append_history_record, default_history_path
from .presets import WorkflowPreset, enrich_prompt, get_preset
from .validation import (
    MESHY_API_COSTS,
    MESHY_COSTS_AS_OF,
    estimate_text_to_3d_credits,
    extract_balance_value,
    normalize_text_to_3d_preview_payload,
    normalize_text_to_3d_refine_payload,
    normalize_target_formats,
    sanitize_asset_name,
    validate_texture_guidance,
)


def create_text_to_3d_asset_pack(client: Any, arguments: dict[str, Any]) -> dict[str, Any]:
    plan = build_text_to_3d_asset_pack_plan(arguments)
    if plan["dry_run"]:
        return {
            "dry_run": True,
            "asset_name": plan["asset_name"],
            "asset_slug": plan["asset_slug"],
            "asset_dir": str(plan["asset_dir"]),
            "estimated_credits": plan["estimated_credits"],
            "costs_as_of": MESHY_COSTS_AS_OF,
            "cost_table": MESHY_API_COSTS,
            "preview_payload": plan["preview_payload"],
            "refine_payload": plan["refine_payload"],
            "preset": plan["preset"].name,
            "preset_notes": plan["preset"].notes,
            "planned_steps": plan["planned_steps"],
        }

    asset_dir: Path = plan["asset_dir"]
    overwrite = plan["overwrite"]
    if asset_dir.exists() and not overwrite:
        raise MeshyError(f"Asset output folder already exists: {asset_dir}")
    if not plan["confirm_spend"]:
        raise MeshyError(
            "Estimated Meshy API cost requires approval before creating paid tasks. Re-run with confirm_spend=true to proceed.",
            details={
                "estimated_credits": plan["estimated_credits"],
                "costs_as_of": MESHY_COSTS_AS_OF,
                "cost_table": MESHY_API_COSTS,
                "max_spend": plan["max_spend"],
            },
        )

    balance_before_payload = client.get_balance()
    balance_before = extract_balance_value(balance_before_payload)
    min_balance = plan["min_balance"]
    if balance_before is not None and balance_before - plan["estimated_credits"] < min_balance:
        raise MeshyError(
            "Insufficient balance for this workflow budget guard.",
            details={
                "balance": balance_before,
                "estimated_credits": plan["estimated_credits"],
                "costs_as_of": MESHY_COSTS_AS_OF,
                "min_balance": min_balance,
            },
        )

    asset_dir.mkdir(parents=True, exist_ok=True)
    (asset_dir / "textures").mkdir(parents=True, exist_ok=True)

    created_at = utc_now()
    preview_task_id: str | None = None
    refine_task_id: str | None = None
    preview_task: dict[str, Any] | list[Any] | None = None
    refine_task: dict[str, Any] | list[Any] | None = None
    output_files: dict[str, Any] = {"models": {}, "textures": {}}
    missing_optional_assets: list[str] = []

    preview_response = client.create_text_to_3d_preview(plan["preview_payload"])
    preview_task_id = str(preview_response["task_id"])
    preview_task = client.wait_for_task(
        {
            "task_type": "text-to-3d",
            "task_id": preview_task_id,
            "timeout_seconds": plan["timeout_seconds"],
            "poll_interval_seconds": plan["poll_interval_seconds"],
        }
    )

    if isinstance(preview_task, dict):
        download_preview_assets(client, preview_task, asset_dir, overwrite, output_files, missing_optional_assets)

    final_status = task_status(preview_task)
    if final_status == "SUCCEEDED" and plan["refine"]:
        refine_response = client.refine_text_to_3d(plan["refine_payload"] | {"preview_task_id": preview_task_id})
        refine_task_id = str(refine_response["task_id"])
        refine_task = client.wait_for_task(
            {
                "task_type": "text-to-3d",
                "task_id": refine_task_id,
                "timeout_seconds": plan["timeout_seconds"],
                "poll_interval_seconds": plan["poll_interval_seconds"],
            }
        )
        final_status = task_status(refine_task)
        if isinstance(refine_task, dict):
            download_final_assets(client, refine_task, asset_dir, overwrite, output_files, missing_optional_assets)
    elif final_status == "SUCCEEDED":
        promote_preview_model(output_files)

    balance_after_payload = client.get_balance()
    balance_after = extract_balance_value(balance_after_payload)
    credits_spent = None
    if balance_before is not None and balance_after is not None:
        credits_spent = balance_before - balance_after

    manifest = build_manifest(
        plan=plan,
        created_at=created_at,
        preview_task_id=preview_task_id,
        refine_task_id=refine_task_id,
        preview_task=preview_task,
        refine_task=refine_task,
        final_status=final_status,
        output_files=output_files,
        missing_optional_assets=missing_optional_assets,
        balance_before=balance_before,
        balance_after=balance_after,
        credits_spent=credits_spent,
    )
    write_json(asset_dir / "manifest.json", manifest)
    (asset_dir / "prompt.md").write_text(build_prompt_markdown(plan), encoding="utf-8")

    history_record = {
        "created_at": created_at,
        "asset_name": plan["asset_name"],
        "asset_slug": plan["asset_slug"],
        "asset_dir": str(asset_dir),
        "preset": plan["preset"].name,
        "status": final_status,
        "preview_task_id": preview_task_id,
        "refine_task_id": refine_task_id,
        "estimated_credits": plan["estimated_credits"],
        "costs_as_of": MESHY_COSTS_AS_OF,
        "credits_spent": credits_spent,
    }
    append_history_record(plan["history_path"], history_record)

    return {
        "asset_name": plan["asset_name"],
        "asset_slug": plan["asset_slug"],
        "asset_dir": str(asset_dir),
        "manifest_path": str(asset_dir / "manifest.json"),
        "prompt_path": str(asset_dir / "prompt.md"),
        "history_path": str(plan["history_path"]),
        "status": final_status,
        "preview_task_id": preview_task_id,
        "refine_task_id": refine_task_id,
        "estimated_credits": plan["estimated_credits"],
        "costs_as_of": MESHY_COSTS_AS_OF,
        "credits_spent": credits_spent,
        "output_files": output_files,
        "missing_optional_assets": missing_optional_assets,
    }


def build_text_to_3d_asset_pack_plan(arguments: dict[str, Any]) -> dict[str, Any]:
    asset_name = str(arguments.get("asset_name", "")).strip()
    prompt = str(arguments.get("prompt", "")).strip()
    if not asset_name:
        raise MeshyError("asset_name is required.")
    if not prompt:
        raise MeshyError("prompt is required.")

    preset = get_preset(arguments.get("preset", "game_prop"))
    refine = bool(arguments.get("refine", True))
    overwrite = bool(arguments.get("overwrite", False))
    dry_run = bool(arguments.get("dry_run", False))
    output_dir = Path(str(arguments.get("output_dir", "outputs"))).expanduser().resolve()
    asset_slug = sanitize_asset_name(asset_name)
    asset_dir = output_dir / asset_slug
    target_formats = normalize_target_formats(arguments.get("target_formats"), default=preset.target_formats) or [
        "glb"
    ]

    preview_payload: dict[str, Any] = {
        "target_formats": target_formats,
        **preset.preview_defaults,
    }
    for key in (
        "ai_model",
        "auto_size",
        "decimation_mode",
        "moderation",
        "model_type",
        "negative_prompt",
        "origin_at",
        "pose_mode",
        "should_remesh",
        "symmetry_mode",
        "target_polycount",
        "topology",
    ):
        if key in arguments and arguments[key] is not None:
            preview_payload[key] = arguments[key]

    preview_payload = normalize_text_to_3d_preview_payload(preview_payload)
    enriched_prompt = enrich_prompt(prompt, preset, pose_mode=preview_payload.get("pose_mode"))
    preview_payload["prompt"] = enriched_prompt

    refine_payload: dict[str, Any] = {
        "target_formats": target_formats,
        **preset.refine_defaults,
    }
    refine_payload["enable_pbr"] = bool(arguments.get("enable_pbr", refine_payload.get("enable_pbr", True)))
    for key in (
        "ai_model",
        "auto_size",
        "moderation",
        "origin_at",
        "remove_lighting",
        "texture_prompt",
        "texture_image_url",
        "texture_image_path",
    ):
        if key in arguments and arguments[key] is not None:
            refine_payload[key] = arguments[key]

    validate_texture_guidance(refine_payload)
    preview_payload = normalize_text_to_3d_preview_payload(preview_payload)
    refine_payload = normalize_text_to_3d_refine_payload(refine_payload)

    max_spend_value = arguments.get("max_spend", 35)
    max_spend = 35 if max_spend_value is None else int(max_spend_value)
    estimated_credits = estimate_text_to_3d_credits(preview_payload, refine=refine)
    if estimated_credits > max_spend:
        raise MeshyError(
            "Estimated Meshy credit spend exceeds max_spend.",
            details={
                "estimated_credits": estimated_credits,
                "costs_as_of": MESHY_COSTS_AS_OF,
                "max_spend": max_spend,
            },
        )

    planned_steps = ["create_preview", "wait_preview", "download_preview_assets"]
    if refine:
        planned_steps.extend(["create_refine", "wait_refine", "download_final_assets"])
    planned_steps.extend(["write_manifest", "append_history"])

    return {
        "asset_name": asset_name,
        "asset_slug": asset_slug,
        "asset_dir": asset_dir,
        "output_dir": output_dir,
        "history_path": Path(str(arguments.get("history_path") or default_history_path())).expanduser().resolve(),
        "prompt": prompt,
        "enriched_prompt": enriched_prompt,
        "texture_prompt": refine_payload.get("texture_prompt"),
        "preset": preset,
        "preview_payload": preview_payload,
        "refine_payload": refine_payload,
        "target_formats": target_formats,
        "refine": refine,
        "overwrite": overwrite,
        "dry_run": dry_run,
        "max_spend": max_spend,
        "confirm_spend": bool(arguments.get("confirm_spend", False)),
        "min_balance": float(arguments.get("min_balance", 0) or 0),
        "estimated_credits": estimated_credits,
        "poll_interval_seconds": float(arguments.get("poll_interval_seconds", 5)),
        "timeout_seconds": float(arguments.get("timeout_seconds", 900)),
        "planned_steps": planned_steps,
    }


def download_preview_assets(
    client: Any,
    task: dict[str, Any],
    asset_dir: Path,
    overwrite: bool,
    output_files: dict[str, Any],
    missing_optional_assets: list[str],
) -> None:
    thumbnail_url = task.get("thumbnail_url")
    if isinstance(thumbnail_url, str) and thumbnail_url:
        output_files["preview_thumbnail"] = client.download_asset(
            {"url": thumbnail_url, "output_path": str(asset_dir / "preview.png"), "overwrite": overwrite}
        )
    else:
        missing_optional_assets.append("preview.png")

    model_urls = task.get("model_urls") if isinstance(task.get("model_urls"), dict) else {}
    preview_glb = model_urls.get("glb")
    if isinstance(preview_glb, str) and preview_glb:
        output_files["preview_model"] = client.download_asset(
            {"url": preview_glb, "output_path": str(asset_dir / "preview.glb"), "overwrite": overwrite}
        )
    else:
        missing_optional_assets.append("preview.glb")


def download_final_assets(
    client: Any,
    task: dict[str, Any],
    asset_dir: Path,
    overwrite: bool,
    output_files: dict[str, Any],
    missing_optional_assets: list[str],
) -> None:
    model_urls = task.get("model_urls") if isinstance(task.get("model_urls"), dict) else {}
    if not model_urls:
        missing_optional_assets.append("models")
    for target_format, url in model_urls.items():
        if not isinstance(url, str) or not url:
            continue
        if target_format == "mtl":
            output_name = "model.mtl"
        else:
            output_name = f"model.{target_format}"
        output_files["models"][target_format] = client.download_asset(
            {"url": url, "output_path": str(asset_dir / output_name), "overwrite": overwrite}
        )

    texture_urls = flatten_texture_urls(task.get("texture_urls"))
    if not texture_urls:
        missing_optional_assets.append("textures")
        return
    for texture_name, url in texture_urls.items():
        output_files["textures"][texture_name] = client.download_asset(
            {
                "url": url,
                "output_path": str(asset_dir / "textures" / texture_filename(texture_name)),
                "overwrite": overwrite,
            }
        )


def promote_preview_model(output_files: dict[str, Any]) -> None:
    preview_model = output_files.get("preview_model")
    if preview_model and not output_files.get("models"):
        output_files["models"]["glb"] = preview_model


def build_manifest(
    *,
    plan: dict[str, Any],
    created_at: str,
    preview_task_id: str | None,
    refine_task_id: str | None,
    preview_task: dict[str, Any] | list[Any] | None,
    refine_task: dict[str, Any] | list[Any] | None,
    final_status: str,
    output_files: dict[str, Any],
    missing_optional_assets: list[str],
    balance_before: int | float | None,
    balance_after: int | float | None,
    credits_spent: int | float | None,
) -> dict[str, Any]:
    final_task = refine_task if refine_task is not None else preview_task
    model_urls = final_task.get("model_urls", {}) if isinstance(final_task, dict) else {}
    texture_urls = final_task.get("texture_urls", []) if isinstance(final_task, dict) else []
    thumbnail_url = final_task.get("thumbnail_url") if isinstance(final_task, dict) else None
    return {
        "schema_version": "1.0",
        "asset_name": plan["asset_name"],
        "asset_slug": plan["asset_slug"],
        "preset": plan["preset"].name,
        "prompt": plan["prompt"],
        "enriched_prompt": plan["enriched_prompt"],
        "texture_prompt": plan["texture_prompt"],
        "created_at": created_at,
        "downloaded_at": utc_now(),
        "preview_task_id": preview_task_id,
        "refine_task_id": refine_task_id,
        "final_status": final_status,
        "selected_formats": plan["target_formats"],
        "estimated_credits": plan["estimated_credits"],
        "costs_as_of": MESHY_COSTS_AS_OF,
        "cost_table": MESHY_API_COSTS,
        "balance_before": balance_before,
        "balance_after": balance_after,
        "credits_spent": credits_spent,
        "model_urls": model_urls,
        "thumbnail_url": thumbnail_url,
        "texture_urls": texture_urls,
        "output_files": output_files,
        "file_sizes": collect_file_sizes(output_files),
        "missing_optional_assets": sorted(set(missing_optional_assets)),
        "normalized_api_params": {
            "preview": plan["preview_payload"],
            "refine": plan["refine_payload"] if plan["refine"] else None,
        },
        "preview_task": preview_task,
        "refine_task": refine_task,
    }


def collect_file_sizes(output_files: dict[str, Any]) -> dict[str, Any]:
    sizes: dict[str, Any] = {}
    for key, value in output_files.items():
        if isinstance(value, dict) and "path" in value:
            sizes[key] = value.get("bytes")
        elif isinstance(value, dict):
            sizes[key] = {
                sub_key: sub_value.get("bytes")
                for sub_key, sub_value in value.items()
                if isinstance(sub_value, dict)
            }
    return sizes


def build_prompt_markdown(plan: dict[str, Any]) -> str:
    preset: WorkflowPreset = plan["preset"]
    texture_prompt = plan["texture_prompt"] or "None"
    notes = "\n".join(f"- {note}" for note in preset.notes)
    return (
        f"# {plan['asset_name']}\n\n"
        "## Original Prompt\n\n"
        f"{plan['prompt']}\n\n"
        "## Preset-Enriched Prompt\n\n"
        f"{plan['enriched_prompt']}\n\n"
        "## Texture Prompt\n\n"
        f"{texture_prompt}\n\n"
        "## Preset Notes\n\n"
        f"{notes}\n"
    )


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def task_status(task: Any) -> str:
    if isinstance(task, dict):
        return str(task.get("status", "UNKNOWN"))
    return "UNKNOWN"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
