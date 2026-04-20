#!/usr/bin/env python3
"""Local MCP server for the Meshy API.

This entry point intentionally stays thin: transport, validation, downloads,
workflow orchestration, credential storage, and CLI handling live in focused
modules under the local ``meshy`` package.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

MCP_ROOT = Path(__file__).resolve().parent
if str(MCP_ROOT) not in sys.path:
    sys.path.insert(0, str(MCP_ROOT))

from meshy.cli import parse_args, run_cli
from meshy.client import (
    MeshyClient,
    MeshyHttpTransport,
    client_from_config,
)
from meshy.credentials import (
    configure_api_key,
    credential_path,
    require_api_key,
    resolve_api_key,
)
from meshy.downloads import (
    file_to_data_uri,
    resolve_output_path,
)
from meshy.errors import MeshyError


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
            "meshy_create_text_to_3d_asset_pack": lambda args: client.create_text_to_3d_asset_pack(args),
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
    except Exception as exc:
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


TEXT_TO_3D_FORMATS = ["glb", "obj", "fbx", "stl", "usdz", "3mf"]

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
        "meshy_create_text_to_3d_asset_pack",
        "Create a complete Text to 3D asset pack: preview, wait, optional refine, downloads, manifest, prompt, and history.",
        {
            "asset_name": {"type": "string"},
            "prompt": {"type": "string"},
            "preset": {
                "type": "string",
                "description": "game_prop, low_poly_asset, riggable_character, or printable_model.",
            },
            "output_dir": {"type": "string"},
            "texture_prompt": {"type": "string"},
            "refine": {"type": "boolean"},
            "target_formats": {
                "type": "array",
                "items": {"type": "string", "enum": TEXT_TO_3D_FORMATS},
            },
            "enable_pbr": {"type": "boolean"},
            "max_spend": {"type": "integer", "description": "Maximum estimated Meshy credits to allow."},
            "min_balance": {"type": "number", "description": "Minimum balance to keep after estimated spend."},
            "confirm_spend": {
                "type": "boolean",
                "description": "Must be true before the workflow creates paid Meshy generation tasks.",
            },
            "dry_run": {"type": "boolean"},
            "overwrite": {"type": "boolean"},
            "poll_interval_seconds": {"type": "number"},
            "timeout_seconds": {"type": "number"},
        },
        ["asset_name", "prompt"],
    ),
    tool_schema(
        "meshy_create_text_to_3d_preview",
        "Create a Meshy Text to 3D preview task.",
        {
            "prompt": {"type": "string"},
            "target_formats": {"type": "array", "items": {"type": "string", "enum": TEXT_TO_3D_FORMATS}},
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
            "target_formats": {"type": "array", "items": {"type": "string", "enum": TEXT_TO_3D_FORMATS}},
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
            "target_formats": {"type": "array", "items": {"type": "string", "enum": TEXT_TO_3D_FORMATS}},
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
            "target_formats": {"type": "array", "items": {"type": "string", "enum": TEXT_TO_3D_FORMATS}},
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
            "target_formats": {"type": "array", "items": {"type": "string", "enum": TEXT_TO_3D_FORMATS}},
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
                "serverInfo": {"name": "meshy-api", "version": "1.3.0"},
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


def main(argv: list[str] | None = None) -> int:
    try:
        return run_cli(
            argv or sys.argv[1:],
            tools=TOOLS,
            stdio_runner=run_stdio_server,
            client_factory=client_from_config,
        )
    except MeshyError as exc:
        print(json.dumps(exc.to_dict(), indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
