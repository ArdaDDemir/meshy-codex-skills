# Meshy Prompt Studio

Meshy Prompt Studio is the plugin package in this repository. It bundles the `write-meshy-prompts` skill with a local Meshy API MCP server so Codex can write prompts, create Meshy tasks, poll status, download files, and build local Text to 3D asset packs.

## What It Includes

```text
.codex-plugin/plugin.json
.mcp.json
mcp/meshy_mcp_server.py
mcp/meshy/
skills/write-meshy-prompts/
LICENSE.txt
README.md
```

## Install

Install this plugin from the repository marketplace entry or directly from this folder:

```text
plugins/meshy-prompt-studio/
```

Plugin metadata:

```text
plugins/meshy-prompt-studio/.codex-plugin/plugin.json
```

MCP server declaration:

```text
plugins/meshy-prompt-studio/.mcp.json
```

After installation, Codex should expose:

- The bundled `write-meshy-prompts` skill.
- A local MCP server named `meshy-api`.
- Meshy tools such as `meshy_get_balance`, `meshy_create_text_to_3d_preview`, and `meshy_create_text_to_3d_asset_pack`.

### Codex App Local Setup

For local Codex App testing, there are two useful checks:

1. Plugin package discovery:

```text
plugins/meshy-prompt-studio/.codex-plugin/plugin.json
```

2. MCP server discovery:

```text
plugins/meshy-prompt-studio/.mcp.json
```

The Codex App UI may cache plugin discovery. If the skill appears but the plugin card does not, fully restart Codex and verify the MCP server directly:

```bash
python plugins/meshy-prompt-studio/mcp/meshy_mcp_server.py --print-tools
```

If needed, add the MCP server directly to Codex config with an absolute path:

```toml
[mcp_servers.meshy-api]
command = "python"
args = ["C:\\path\\to\\meshy-codex-skills\\plugins\\meshy-prompt-studio\\mcp\\meshy_mcp_server.py"]
```

Use your own local repository path. After editing config, restart Codex before checking the UI again.

## Requirements

- Python 3.10 or newer.
- No third-party Python runtime packages.
- A Meshy API key for live API calls.

## Authentication

Meshy API access requires a Meshy API key. Prompt-only skill usage works without a key, but the MCP API tools cannot check balance, create tasks, poll tasks, download assets, or run asset-pack workflows until a key is configured. Local schema checks such as `--print-tools` do not need a key.

Use one of these approaches:

```powershell
$env:MESHY_API_KEY = "msy_your_key_here"
```

```bash
export MESHY_API_KEY="msy_your_key_here"
```

Or configure the key through Codex:

```text
Use the Meshy API MCP tool to configure my Meshy API key.
```

Or configure it through the local CLI without committing secrets:

```bash
python plugins/meshy-prompt-studio/mcp/meshy_mcp_server.py --configure-api-key-stdin
```

Paste the key into stdin when prompted or when piping input. The response does not echo the key.

Configured keys are stored outside the repository:

- Windows: `%APPDATA%/meshy-prompt-studio/credentials.json`
- macOS/Linux: `~/.config/meshy-prompt-studio/credentials.json`

The configure tool never echoes the API key back in its response.

## Quick Checks

Print MCP tool schemas:

```bash
python plugins/meshy-prompt-studio/mcp/meshy_mcp_server.py --print-tools
```

Check auth:

```bash
python plugins/meshy-prompt-studio/mcp/meshy_mcp_server.py --check-auth
```

Check balance:

```bash
python plugins/meshy-prompt-studio/mcp/meshy_mcp_server.py --balance
```

Check the API integration with Meshy test mode:

```bash
python plugins/meshy-prompt-studio/mcp/meshy_mcp_server.py --test-mode --check-auth
```

Test mode verifies request handling and sample responses. It is not a substitute for real generation with your own Meshy API key.

## Asset Pack Workflow

Use `meshy_create_text_to_3d_asset_pack` when Codex should run the full Text to 3D loop: preview, wait, optional refine, downloads, manifest, prompt file, and history.

Dry-run from the CLI:

```bash
python plugins/meshy-prompt-studio/mcp/meshy_mcp_server.py \
  --create-text-asset examples/prompts/treasure-chest.prompt.txt \
  --name treasure-chest \
  --preset low_poly_asset \
  --dry-run
```

Create after approving spend:

```bash
python plugins/meshy-prompt-studio/mcp/meshy_mcp_server.py \
  --create-text-asset examples/prompts/treasure-chest.prompt.txt \
  --name treasure-chest \
  --preset low_poly_asset \
  --confirm-spend
```

Supported presets:

- `game_prop`
- `low_poly_asset`
- `riggable_character`
- `printable_model`

See [../../docs/asset-pack-workflow.md](../../docs/asset-pack-workflow.md) for budget guards, output layout, and detailed CLI examples.

Local history helpers:

```bash
python plugins/meshy-prompt-studio/mcp/meshy_mcp_server.py --history
python plugins/meshy-prompt-studio/mcp/meshy_mcp_server.py --resume treasure-chest
python plugins/meshy-prompt-studio/mcp/meshy_mcp_server.py --download-existing TASK_ID --type text-to-3d --out outputs/teacher
python plugins/meshy-prompt-studio/mcp/meshy_mcp_server.py --open-manifest treasure-chest
```

## MCP Tools

- `meshy_configure_api_key`
- `meshy_check_auth`
- `meshy_get_balance`
- `meshy_create_text_to_3d_asset_pack`
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

## Release Package

Build a distributable plugin zip from the repository root:

```bash
python scripts/package_plugin.py
```

Tagged GitHub releases upload `meshy-prompt-studio-<version>.zip` through CI.

## Example Prompts

```text
Run the safe Meshy first-run flow: print tools, test mode auth, then a dry-run plan.
```

```text
Create a dry-run low-poly prop asset pack and show estimated credits before any paid task.
```

```text
If I ask for texture after a generated model, continue from that asset instead of creating a new mesh.
```

## Safety Notes

- Prompt-only usage does not spend credits.
- Live Meshy API calls can spend credits.
- The asset-pack workflow requires `confirm_spend=true` before paid task creation.
- Test in this order: `--print-tools`, `--check-auth`, `--balance`, asset-pack `--dry-run`, then `--confirm-spend` only after reviewing the plan.
- If `pose_mode` is set to `t-pose`, the `riggable_character` preset keeps the enriched prompt consistent with T-pose.
- Meshy test mode is for integration testing only; use your own Meshy API key for real generation.
- Texture follow-up requests should stay attached to the active asset when possible; do not create a fresh mesh unless the user changes targets.
- When front view alone is not enough, prefer 3 to 4 clean reference angles and `meshy_create_multi_image_to_3d`.
- Do not commit credentials, generated assets, `.meshy/`, `outputs/`, or `meshy-downloads/`.

## License

MIT License. See [LICENSE.txt](LICENSE.txt).
