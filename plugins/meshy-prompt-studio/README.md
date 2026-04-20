# Meshy Prompt Studio

Meshy Prompt Studio is a Codex plugin that bundles the `write-meshy-prompts` skill and a local Meshy API MCP server.

It helps Codex create production-ready Meshy prompts, submit Meshy API tasks, poll task status, and download generated assets without leaving the Codex workflow.

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
Use Meshy to create a low-poly treasure chest and download the GLB.
```

```text
Use Meshy to check my API balance.
```

## MCP Tools

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

## Local CLI

Configure an API key from stdin:

```text
python plugins/meshy-prompt-studio/mcp/meshy_mcp_server.py --configure-api-key-stdin
```

Check authentication without creating a paid generation task:

```text
python plugins/meshy-prompt-studio/mcp/meshy_mcp_server.py --check-auth
```

## Package Contents

```text
.codex-plugin/plugin.json
.mcp.json
mcp/meshy_mcp_server.py
skills/write-meshy-prompts/
LICENSE.txt
README.md
```

## License

MIT License. See [LICENSE.txt](LICENSE.txt).
