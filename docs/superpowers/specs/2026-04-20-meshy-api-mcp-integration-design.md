# Meshy API MCP Integration Design

Date: 2026-04-20

## Goal

Upgrade Meshy Prompt Studio from a prompt-only Codex plugin into a plugin that can directly call the Meshy API from Codex through a local MCP server. Users should be able to ask Codex to create Meshy tasks, check status, and download generated assets without leaving the Codex workflow.

## Authentication

Meshy uses API keys passed through the `Authorization: Bearer <api-key>` header. The plugin will not commit or publish API keys. The MCP server will read credentials in this priority order:

1. `MESHY_API_KEY` environment variable.
2. A local credential file outside the repository:
   - Windows: `%APPDATA%/meshy-prompt-studio/credentials.json`
   - macOS/Linux: `~/.config/meshy-prompt-studio/credentials.json`

The server will expose a `meshy_configure_api_key` tool that stores a key in the local credential file. Responses from this tool must never echo the key.

## Plugin Package

The plugin will add:

- `.mcp.json` to declare the local Meshy MCP server.
- `mcp/meshy_mcp_server.py` as a stdio JSON-RPC MCP server using only the Python standard library.
- Tests under `tests/` for credentials, request construction, polling, and local file data URI conversion.

The existing root-level `skills/write-meshy-prompts` folder remains intact. The plugin-bundled copy of the skill remains available under `plugins/meshy-prompt-studio/skills/write-meshy-prompts`.

## MCP Tools

Initial tool set:

- `meshy_configure_api_key`
- `meshy_check_auth`
- `meshy_get_balance`
- `meshy_create_text_to_3d_preview`
- `meshy_refine_text_to_3d`
- `meshy_create_image_to_3d`
- `meshy_create_multi_image_to_3d`
- `meshy_get_task`
- `meshy_list_tasks`
- `meshy_wait_for_task`
- `meshy_download_asset`
- `meshy_remesh`
- `meshy_retexture`
- `meshy_rig_character`
- `meshy_animate_character`

Tools will return JSON text with task IDs, statuses, progress, model URLs, texture URLs, and downloaded file paths where applicable.

## Data Flow

Text to 3D:

1. `meshy_create_text_to_3d_preview` submits a preview task.
2. `meshy_wait_for_task` polls the preview task until it reaches a terminal status.
3. `meshy_refine_text_to_3d` submits a refine task when texture generation is wanted.
4. `meshy_wait_for_task` polls the refine task.
5. `meshy_download_asset` downloads a selected output format.

Image to 3D:

1. `meshy_create_image_to_3d` submits an image task using either a public image URL, data URI, or local image path converted to a data URI.
2. `meshy_wait_for_task` polls the task.
3. `meshy_download_asset` downloads the selected output format.

Post-processing:

- `meshy_remesh` accepts a completed task ID, model URL, or local model path.
- `meshy_retexture` accepts a completed task ID, model URL, or local model path.
- `meshy_rig_character` accepts a completed task ID, GLB URL, or local GLB path.
- `meshy_animate_character` accepts a completed rigging task ID and an animation action ID.

## Error Handling

The server will:

- Return clear errors when no API key is configured.
- Preserve Meshy HTTP status codes and response messages.
- Avoid printing or returning API keys.
- Reject unsupported local file extensions before sending requests.
- Avoid overwriting downloaded files unless `overwrite` is explicitly true.

## Testing

Unit tests will use fake HTTP transports and temporary credential paths. Network calls are not required for the default test suite. A real-key balance check may be run manually after local configuration to verify live authentication without creating paid generation tasks.

## Non-goals

- No public hosting or OAuth proxy in this version.
- No API keys in `plugin.json`, `.mcp.json`, README, tests, or committed files.
- No automatic paid generation during validation.
