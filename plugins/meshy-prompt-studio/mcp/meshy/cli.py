"""Command line interface for Meshy Prompt Studio."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Callable

from .client import client_from_config
from .credentials import TEST_MODE_API_KEY, configure_api_key
from .errors import MeshyError
from .history import (
    default_history_path,
    find_history_record,
    iter_history_records,
    latest_task_id,
    manifest_path_from_record,
)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Meshy API MCP server")
    parser.add_argument("--configure-api-key-stdin", action="store_true")
    parser.add_argument("--test-mode", action="store_true", help="Use Meshy's public test mode API key for this CLI run.")
    parser.add_argument("--check-auth", action="store_true")
    parser.add_argument("--print-tools", action="store_true")
    parser.add_argument("--balance", action="store_true")
    parser.add_argument("--create-text-asset")
    parser.add_argument("--name")
    parser.add_argument("--preset", default="game_prop")
    parser.add_argument("--output-dir", default="outputs")
    parser.add_argument("--texture-prompt")
    parser.add_argument("--no-refine", action="store_true")
    parser.add_argument("--target-format", action="append", dest="target_formats")
    parser.add_argument("--max-spend", type=int, default=35)
    parser.add_argument("--min-balance", type=float, default=0)
    parser.add_argument("--confirm-spend", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--poll-interval", type=float, default=5)
    parser.add_argument("--timeout", type=float, default=900)
    parser.add_argument("--wait")
    parser.add_argument("--resume")
    parser.add_argument("--download")
    parser.add_argument("--download-existing")
    parser.add_argument("--out")
    parser.add_argument("--type", default="text-to-3d")
    parser.add_argument("--list-recent")
    parser.add_argument("--history", action="store_true")
    parser.add_argument("--open-manifest")
    parser.add_argument("--history-path")
    return parser.parse_args(argv)


def run_cli(
    argv: list[str],
    *,
    tools: list[dict[str, Any]],
    stdio_runner: Callable[[], None],
    client_factory: Callable[[], Any] = client_from_config,
) -> int:
    args = parse_args(argv)
    if args.test_mode:
        os.environ["MESHY_API_KEY"] = TEST_MODE_API_KEY
    if args.configure_api_key_stdin:
        key = input_stream_text().strip()
        print_json(configure_api_key({"api_key": key}))
        return 0
    if args.print_tools:
        print_json({"tools": tools})
        return 0
    if args.check_auth:
        print_json(client_factory().check_auth())
        return 0
    if args.balance:
        print_json(client_factory().get_balance())
        return 0
    if args.create_text_asset:
        print_json(create_text_asset_from_cli(args, client_factory))
        return 0
    if args.history:
        print_json(list_history_from_cli(args))
        return 0
    if args.wait:
        print_json(
            client_factory().wait_for_task(
                {
                    "task_type": args.type,
                    "task_id": args.wait,
                    "timeout_seconds": args.timeout,
                    "poll_interval_seconds": args.poll_interval,
                }
            )
        )
        return 0
    if args.resume:
        print_json(resume_from_history_cli(args, client_factory))
        return 0
    if args.download or args.download_existing:
        print_json(download_task_from_cli(args, client_factory))
        return 0
    if args.open_manifest:
        print_json(open_manifest_from_history_cli(args))
        return 0
    if args.list_recent:
        print_json(
            client_factory().list_tasks(
                {
                    "task_type": args.list_recent,
                    "page_num": 1,
                    "page_size": 10,
                    "sort_by": "-created_at",
                }
            )
        )
        return 0

    stdio_runner()
    return 0


def create_text_asset_from_cli(
    args: argparse.Namespace,
    client_factory: Callable[[], Any] = client_from_config,
) -> dict[str, Any]:
    prompt_path = Path(args.create_text_asset).expanduser().resolve()
    if not prompt_path.exists() or not prompt_path.is_file():
        raise MeshyError(f"Prompt file does not exist: {prompt_path}")
    asset_name = args.name or prompt_path.stem
    arguments: dict[str, Any] = {
        "asset_name": asset_name,
        "prompt": prompt_path.read_text(encoding="utf-8-sig").strip(),
        "preset": args.preset,
        "output_dir": args.output_dir,
        "texture_prompt": args.texture_prompt,
        "refine": not args.no_refine,
        "target_formats": args.target_formats,
        "max_spend": args.max_spend,
        "min_balance": args.min_balance,
        "confirm_spend": args.confirm_spend,
        "dry_run": args.dry_run,
        "overwrite": args.overwrite,
        "poll_interval_seconds": args.poll_interval,
        "timeout_seconds": args.timeout,
    }
    if args.dry_run:
        from .workflows import dry_run_text_to_3d_asset_pack

        return dry_run_text_to_3d_asset_pack(arguments)
    return client_factory().create_text_to_3d_asset_pack(arguments)


def download_task_from_cli(
    args: argparse.Namespace,
    client_factory: Callable[[], Any] = client_from_config,
) -> dict[str, Any]:
    task_id = str(args.download_existing or args.download or "").strip()
    flag = "--download-existing" if args.download_existing else "--download"
    if not args.out:
        raise MeshyError(f"--out is required with {flag}.")
    client = client_factory()
    task = client.get_task({"task_type": args.type, "task_id": task_id})
    if not isinstance(task, dict):
        raise MeshyError("Task response did not include downloadable assets.", details=task)
    model_urls = task.get("model_urls")
    if not isinstance(model_urls, dict) or not model_urls:
        raise MeshyError("Task does not include model_urls yet.", details=task)
    out_path = Path(args.out).expanduser().resolve()
    downloads: dict[str, Any] = {}
    for target_format, url in model_urls.items():
        if not isinstance(url, str) or not url:
            continue
        output_path = out_path / f"model.{target_format}" if out_path.suffix == "" else out_path
        downloads[target_format] = client.download_asset(
            {"url": url, "output_path": str(output_path), "overwrite": args.overwrite}
        )
        if out_path.suffix != "":
            break
    return {"task_id": task_id, "task_type": args.type, "downloads": downloads}


def list_history_from_cli(args: argparse.Namespace) -> dict[str, Any]:
    history_path = resolve_history_path(args)
    records = iter_history_records(history_path)
    compact_records = [
        {
            "created_at": record.get("created_at"),
            "asset_name": record.get("asset_name"),
            "asset_slug": record.get("asset_slug"),
            "status": record.get("status"),
            "asset_dir": record.get("asset_dir"),
            "preview_task_id": record.get("preview_task_id"),
            "refine_task_id": record.get("refine_task_id"),
            "latest_task_id": latest_task_id(record),
            "manifest_path": record.get("manifest_path"),
            "failure_stage": record.get("failure_stage"),
            "recovery_hint": record.get("recovery_hint"),
            "task_error": record.get("task_error"),
            "estimated_credits": record.get("estimated_credits"),
            "credits_spent": record.get("credits_spent"),
        }
        for record in records
    ]
    return {"history_path": str(history_path), "records": compact_records}


def resume_from_history_cli(
    args: argparse.Namespace,
    client_factory: Callable[[], Any] = client_from_config,
) -> dict[str, Any]:
    history_path = resolve_history_path(args)
    record = find_history_record(history_path, args.resume)
    if record is None:
        raise MeshyError(f"No history record found for '{args.resume}'.", details={"history_path": str(history_path)})

    task_id = latest_task_id(record)
    if not task_id:
        raise MeshyError("History record does not include a task id.", details=record)

    client = client_factory()
    task = client.wait_for_task(
        {
            "task_type": "text-to-3d",
            "task_id": task_id,
            "timeout_seconds": args.timeout,
            "poll_interval_seconds": args.poll_interval,
        }
    )
    if not isinstance(task, dict):
        raise MeshyError("Task response did not include downloadable assets.", details=task)

    asset_dir = Path(str(record.get("asset_dir") or Path(args.output_dir) / str(record.get("asset_slug") or args.resume)))
    downloads = download_task_assets(client, task, asset_dir, args.overwrite)
    return {
        "history_path": str(history_path),
        "matched_asset": record.get("asset_name"),
        "task_id": task_id,
        "status": task.get("status"),
        "asset_dir": str(asset_dir.expanduser().resolve()),
        "manifest_path": str(manifest_path_from_record(record)) if manifest_path_from_record(record) else None,
        "failure_stage": record.get("failure_stage"),
        "recovery_hint": record.get("recovery_hint"),
        "downloads": downloads,
    }


def download_task_assets(client: Any, task: dict[str, Any], out_path: Path, overwrite: bool) -> dict[str, Any]:
    out_path = out_path.expanduser().resolve()
    downloads: dict[str, Any] = {"models": {}, "textures": {}}

    thumbnail_url = task.get("thumbnail_url")
    if isinstance(thumbnail_url, str) and thumbnail_url:
        downloads["thumbnail"] = client.download_asset(
            {"url": thumbnail_url, "output_path": str(out_path / "preview.png"), "overwrite": overwrite}
        )

    model_urls = task.get("model_urls") if isinstance(task.get("model_urls"), dict) else {}
    for target_format, url in model_urls.items():
        if not isinstance(url, str) or not url:
            continue
        downloads["models"][target_format] = client.download_asset(
            {"url": url, "output_path": str(out_path / f"model.{target_format}"), "overwrite": overwrite}
        )

    texture_urls = task.get("texture_urls") if isinstance(task.get("texture_urls"), list | dict) else []
    texture_map: dict[str, str] = {}
    if isinstance(texture_urls, dict):
        texture_map = {str(key): value for key, value in texture_urls.items() if isinstance(value, str) and value}
    else:
        for item in texture_urls:
            if not isinstance(item, dict):
                continue
            for key, value in item.items():
                if isinstance(value, str) and value:
                    texture_map[str(key)] = value
    for texture_name, url in texture_map.items():
        safe_name = "".join(char if char.isalnum() or char in {"_", "-"} else "_" for char in texture_name.lower())
        downloads["textures"][texture_name] = client.download_asset(
            {
                "url": url,
                "output_path": str(out_path / "textures" / f"{safe_name or 'texture'}.png"),
                "overwrite": overwrite,
            }
        )
    return downloads


def resolve_history_path(args: argparse.Namespace) -> Path:
    return Path(args.history_path).expanduser().resolve() if args.history_path else default_history_path()


def open_manifest_from_history_cli(args: argparse.Namespace) -> dict[str, Any]:
    history_path = resolve_history_path(args)
    record = find_history_record(history_path, args.open_manifest)
    if record is None:
        raise MeshyError(
            f"No history record found for '{args.open_manifest}'.",
            details={"history_path": str(history_path)},
        )

    manifest_path = manifest_path_from_record(record)
    if manifest_path is None or not manifest_path.exists():
        raise MeshyError(
            "History record does not point to an existing manifest.",
            details={
                "history_path": str(history_path),
                "manifest_path": str(manifest_path) if manifest_path else None,
                "record": record,
            },
        )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    summary = {
        "asset_name": manifest.get("asset_name"),
        "asset_slug": manifest.get("asset_slug"),
        "final_status": manifest.get("final_status"),
        "failure_stage": manifest.get("failure_stage"),
        "latest_task_id": manifest.get("latest_task_id"),
        "missing_optional_assets": manifest.get("missing_optional_assets"),
        "downloadable_assets": manifest.get("downloadable_assets"),
        "recovery_hint": manifest.get("recovery_hint"),
    }
    return {
        "history_path": str(history_path),
        "matched_asset": record.get("asset_name"),
        "manifest_path": str(manifest_path),
        "summary": summary,
        "manifest": manifest,
    }


def input_stream_text() -> str:
    import sys

    return sys.stdin.read()


def print_json(payload: Any) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=True))
