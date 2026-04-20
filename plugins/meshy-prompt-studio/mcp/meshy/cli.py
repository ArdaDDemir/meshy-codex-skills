"""Command line interface for Meshy Prompt Studio."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable

from .client import client_from_config
from .credentials import configure_api_key
from .errors import MeshyError


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Meshy API MCP server")
    parser.add_argument("--configure-api-key-stdin", action="store_true")
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
    parser.add_argument("--download")
    parser.add_argument("--out")
    parser.add_argument("--type", default="text-to-3d")
    parser.add_argument("--list-recent")
    return parser.parse_args(argv)


def run_cli(
    argv: list[str],
    *,
    tools: list[dict[str, Any]],
    stdio_runner: Callable[[], None],
    client_factory: Callable[[], Any] = client_from_config,
) -> int:
    args = parse_args(argv)
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
    if args.download:
        print_json(download_task_from_cli(args, client_factory))
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
    return client_factory().create_text_to_3d_asset_pack(arguments)


def download_task_from_cli(
    args: argparse.Namespace,
    client_factory: Callable[[], Any] = client_from_config,
) -> dict[str, Any]:
    if not args.out:
        raise MeshyError("--out is required with --download.")
    client = client_factory()
    task = client.get_task({"task_type": args.type, "task_id": args.download})
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
    return {"task_id": args.download, "task_type": args.type, "downloads": downloads}


def input_stream_text() -> str:
    import sys

    return sys.stdin.read()


def print_json(payload: Any) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=True))
