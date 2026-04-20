# Meshy Prompt Studio

Meshy Prompt Studio is a Codex plugin that bundles the `write-meshy-prompts` skill and a local Meshy API MCP server.

It helps Codex create production-ready Meshy prompts, submit Meshy API tasks, poll task status, download generated assets, and produce local Text to 3D asset packs without leaving the Codex workflow.

Use it for:

- Text to 3D model prompts
- Image to 3D reference prompts
- Texture and retexture prompts
- Game-ready static props
- Riggable humanoid characters
- 3D printable models
- Export and production handoff guidance
- Troubleshooting Meshy generation results
- Direct Meshy API task creation through MCP
- One-command Text to 3D asset packs with manifests and run history

## Install

The plugin manifest lives at:

```text
plugins/meshy-prompt-studio/.codex-plugin/plugin.json
```

The repository marketplace entry lives at:

```text
.agents/plugins/marketplace.json
```

The MCP server config lives at:

```text
plugins/meshy-prompt-studio/.mcp.json
```

Codex plugin tooling can install this plugin from the repository marketplace entry. The plugin exposes the bundled `write-meshy-prompts` skill and a local MCP server named `meshy-api` after installation.

## Authentication

Meshy uses API keys. The MCP server sends the key with:

```text
Authorization: Bearer <MESHY_API_KEY>
```

Configure the key inside Codex with the `meshy_configure_api_key` MCP tool, or set `MESHY_API_KEY` in the local environment before starting Codex.

The MCP server stores configured keys outside this repository:

```text
%APPDATA%/meshy-prompt-studio/credentials.json
```

on Windows, or:

```text
~/.config/meshy-prompt-studio/credentials.json
```

on macOS/Linux.

Never commit Meshy API keys. This plugin does not store credentials in `.mcp.json`, `plugin.json`, README files, tests, or source-controlled files.

## Usage

```text
Use $write-meshy-prompts to create a Meshy prompt pack for a riggable game character.
```

```text
Use $write-meshy-prompts to write Image to 3D and texture prompts for this prop.
```

```text
Use $write-meshy-prompts to turn this concept into separate game and 3D print prompts.
```

```text
Use Meshy to create a low-poly treasure chest asset pack.
```

```text
Use Meshy to check my API balance.
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

## Text to 3D Asset Packs

Use `meshy_create_text_to_3d_asset_pack` when Codex should run the full production loop:

1. Create a Text to 3D preview task.
2. Wait until the preview reaches a terminal status.
3. Download preview thumbnail and preview GLB when available.
4. Create and wait for the refine task when `refine=true`.
5. Download the final model, thumbnail, and texture maps when available.
6. Write `manifest.json`, `prompt.md`, and append `.meshy/history.jsonl`.

Supported presets:

- `game_prop`: GLB output, refine on, PBR textures on, no pose mode.
- `low_poly_asset`: `model_type=lowpoly`, GLB output, refine on.
- `riggable_character`: `pose_mode=a-pose`, GLB and FBX outputs, rig-friendly prompt hints.
- `printable_model`: STL and 3MF outputs, print-safe geometry hints.

Default budget guards:

- `max_spend=35`
- `min_balance=0`
- `confirm_spend=false`
- `dry_run=false`
- `overwrite=false`

Real generation, refine, remesh, rigging, animation, and retexture calls can spend Meshy API credits. The asset pack workflow reports the estimated cost first and requires `confirm_spend=true` before it creates paid Meshy tasks. Use `dry_run=true` to inspect planned payloads and estimated credits before creating paid generation tasks.

API cost reference used by the plugin as of 2026-04-20:

```text
Text to 3D preview, Meshy 6 models: 20 credits
Text to 3D preview, other models: 10 credits
Text to 3D refine: 10 credits
Image to 3D, Meshy 6 models: 20 credits without texture, 30 credits with texture
Image to 3D, other models: 5 credits without texture, 15 credits with texture
Multi Image to 3D: 5 credits without texture, 15 credits with texture
Retexture: 10 credits
Remesh: 5 credits
Auto-Rigging: 5 credits
Animation: 3 credits
```

Asset pack structure:

```text
outputs/<asset-name>/
  model.glb
  preview.glb
  preview.png
  textures/
    base_color.png
    normal.png
    roughness.png
    metallic.png
  manifest.json
  prompt.md
```

`manifest.json` includes task IDs, prompt data, normalized API parameters, model URLs, texture URLs, output file paths, file sizes, balance before/after, and credits spent.

Examples:

```text
Use Meshy to create a Text to 3D asset pack named teacher-model with this prompt: friendly classroom teacher character, clean stylized proportions, warm cardigan, simple readable face. Use preset riggable_character. Tell me the estimated credit cost before spending credits.
```

```text
Use Meshy to create a low-poly asset pack named treasure-chest with this prompt: chunky low-poly wooden treasure chest with metal bands, readable silhouette, game-ready proportions. Use preset low_poly_asset.
```

```text
Use Meshy to create a printable asset pack named desk-organizer with this prompt: compact 3D printable desk organizer with rounded slots, stable base, no thin fragile parts. Use preset printable_model.
```

## Local CLI

Configure an API key from stdin:

```text
python plugins/meshy-prompt-studio/mcp/meshy_mcp_server.py --configure-api-key-stdin
```

Check authentication without creating a paid generation task:

```text
python plugins/meshy-prompt-studio/mcp/meshy_mcp_server.py --check-auth
```

Check balance:

```text
python plugins/meshy-prompt-studio/mcp/meshy_mcp_server.py --balance
```

Create an asset pack from a prompt file:

```text
python plugins/meshy-prompt-studio/mcp/meshy_mcp_server.py --create-text-asset prompt.txt --name teacher --preset riggable_character --confirm-spend
```

Dry-run a planned asset pack without a paid generation request:

```text
python plugins/meshy-prompt-studio/mcp/meshy_mcp_server.py --create-text-asset prompt.txt --name crate --preset low_poly_asset --dry-run
```

Wait for, download, and list tasks:

```text
python plugins/meshy-prompt-studio/mcp/meshy_mcp_server.py --wait TASK_ID --type text-to-3d
python plugins/meshy-prompt-studio/mcp/meshy_mcp_server.py --download TASK_ID --type text-to-3d --out outputs/teacher
python plugins/meshy-prompt-studio/mcp/meshy_mcp_server.py --list-recent text-to-3d
```

## Package Contents

```text
.codex-plugin/plugin.json
.mcp.json
mcp/meshy_mcp_server.py
mcp/meshy/
skills/write-meshy-prompts/
LICENSE.txt
README.md
```

## License

MIT License. See [LICENSE.txt](LICENSE.txt).
