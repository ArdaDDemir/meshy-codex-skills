# Meshy Codex Skills

[![CI](https://github.com/ArdaDDemir/meshy-codex-skills/actions/workflows/ci.yml/badge.svg)](https://github.com/ArdaDDemir/meshy-codex-skills/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE.txt)

Meshy Codex Skills is a focused Codex toolkit for planning and generating Meshy 3D assets. It includes:

- A Codex skill, `write-meshy-prompts`, for production-ready Meshy prompt guidance.
- A Codex plugin, **Meshy Prompt Studio**, that bundles the skill with a local MCP server.
- A standard-library Python MCP/CLI workflow for Meshy API tasks, downloads, manifests, and local asset packs.

This project is for game developers, technical artists, tool builders, and Codex users who want repeatable Meshy prompts or a local API-assisted asset workflow.

## Choose Your Path

| Goal | Start here | What you get |
| --- | --- | --- |
| I only want prompt guidance | Install the `write-meshy-prompts` skill | Copy-ready Text to 3D, Image to 3D, texture, rigging, print, and troubleshooting prompts |
| I want the plugin + MCP setup | Install **Meshy Prompt Studio** from `plugins/meshy-prompt-studio` | Codex-visible Meshy API tools, balance checks, task creation, polling, and downloads |
| I want asset packs | Use `meshy_create_text_to_3d_asset_pack` or the local CLI | `outputs/<asset-name>/` with model files, textures, `manifest.json`, `prompt.md`, and history |

## Quickstart

### Requirements

- Codex with skill/plugin support.
- Python 3.10 or newer.
- A Meshy API key only if you want to call the Meshy API. Prompt-only usage does not need a key.
- No third-party Python runtime packages. The MCP server uses the Python standard library.

### 1. Clone and check the project

```bash
git clone https://github.com/ArdaDDemir/meshy-codex-skills.git
cd meshy-codex-skills
python -m unittest discover tests
```

Optional, but safe for future dependency changes:

```bash
python -m pip install -r requirements.txt
```

### 2. Install only the skill

Use Codex skill installer:

```text
$skill-installer install https://github.com/ArdaDDemir/meshy-codex-skills/tree/main/skills/write-meshy-prompts
```

Restart Codex after installing so the new skill is discovered.

Try it:

```text
Use $write-meshy-prompts to create a Meshy prompt pack for a riggable low-poly goblin enemy for Unity.
```

### 3. Install the plugin

The plugin source is:

```text
plugins/meshy-prompt-studio/
```

Its manifest and MCP declaration are:

```text
plugins/meshy-prompt-studio/.codex-plugin/plugin.json
plugins/meshy-prompt-studio/.mcp.json
```

The repository marketplace entry is:

```text
.agents/plugins/marketplace.json
```

After installation, Codex should expose the bundled `write-meshy-prompts` skill and a local MCP server named `meshy-api`.

#### Codex App local install notes

Codex App can use this project in two practical ways:

- As a visible plugin package, when the app discovers `plugins/meshy-prompt-studio/.codex-plugin/plugin.json`.
- As a local MCP server, when `meshy-api` is configured from `plugins/meshy-prompt-studio/.mcp.json` or from Codex config.

During local testing, the MCP server can be active even if the plugin card does not immediately appear in the Codex App UI. Restart Codex after installing or changing plugin files; the app caches plugin and tool discovery at startup.

If the plugin UI card is not visible but you want to verify the backend, run:

```bash
python plugins/meshy-prompt-studio/mcp/meshy_mcp_server.py --print-tools
```

You should see tools such as:

```text
meshy_check_auth
meshy_get_balance
meshy_create_text_to_3d_asset_pack
```

For a direct local MCP fallback, add an absolute path to your Codex config:

```toml
[mcp_servers.meshy-api]
command = "python"
args = ["C:\\path\\to\\meshy-codex-skills\\plugins\\meshy-prompt-studio\\mcp\\meshy_mcp_server.py"]
```

Use your own repository path in the `args` entry. After editing config, fully restart Codex.

### 4. Configure secrets safely

Meshy API access requires a Meshy API key. Prompt-only skill usage works without a key, but the API/MCP system cannot check balance, create tasks, poll tasks, download assets, or run asset-pack workflows until a key is configured. The only safe checks that do not need a key are local commands such as `--print-tools`.

Never commit Meshy API keys. Use one of these options:

```powershell
$env:MESHY_API_KEY = "msy_your_key_here"
```

```bash
export MESHY_API_KEY="msy_your_key_here"
```

Or configure the key through the MCP tool:

```text
Use the Meshy API MCP tool to configure my Meshy API key.
```

You can also configure it from the local CLI without putting the key in a committed file:

```bash
python plugins/meshy-prompt-studio/mcp/meshy_mcp_server.py --configure-api-key-stdin
```

Then paste the key into stdin. The tool stores it locally and does not echo it in the response.

Stored keys live outside the repo:

- Windows: `%APPDATA%/meshy-prompt-studio/credentials.json`
- macOS/Linux: `~/.config/meshy-prompt-studio/credentials.json`

See [.env.example](.env.example) for non-secret environment variables you may want to set locally.

### 5. Minimal working example

Dry-run an asset pack plan without spending Meshy credits:

```bash
python plugins/meshy-prompt-studio/mcp/meshy_mcp_server.py \
  --create-text-asset examples/prompts/treasure-chest.prompt.txt \
  --name treasure-chest \
  --preset low_poly_asset \
  --dry-run
```

When you are ready to create paid Meshy tasks, remove `--dry-run` and add `--confirm-spend`.

## What The Asset Pack Workflow Produces

The asset-pack workflow writes a local folder like this:

```text
outputs/treasure-chest/
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

`manifest.json` records task IDs, normalized API parameters, model and texture URLs, output paths, file sizes, balance before/after, and estimated or actual credit usage.

More detail:

- [Asset pack workflow](docs/asset-pack-workflow.md)
- [Examples](examples/README.md)
- [Plugin README](plugins/meshy-prompt-studio/README.md)

## Common Commands

Check authentication:

```bash
python plugins/meshy-prompt-studio/mcp/meshy_mcp_server.py --check-auth
```

Check balance:

```bash
python plugins/meshy-prompt-studio/mcp/meshy_mcp_server.py --balance
```

Create a dry-run plan:

```bash
python plugins/meshy-prompt-studio/mcp/meshy_mcp_server.py \
  --create-text-asset examples/prompts/treasure-chest.prompt.txt \
  --name treasure-chest \
  --preset low_poly_asset \
  --dry-run
```

Create the asset pack after approving spend:

```bash
python plugins/meshy-prompt-studio/mcp/meshy_mcp_server.py \
  --create-text-asset examples/prompts/treasure-chest.prompt.txt \
  --name treasure-chest \
  --preset low_poly_asset \
  --confirm-spend
```

## Local Testing Findings

These notes came from testing the project in Codex App on Windows:

- Installing the skill and installing the plugin are separate steps. The skill can appear even when the plugin package is not yet installed.
- The MCP tools can be available before the plugin card appears in the UI. Use `--print-tools` or ask Codex for Meshy tools to confirm backend availability.
- A full Codex restart is often required after adding plugin files, editing `config.toml`, or changing MCP server code.
- `dry_run=true` is the safest first asset-pack test because it plans the payload and estimated credits without creating paid Meshy generation tasks.
- `riggable_character` prompts are now pose-aware: if `pose_mode` is overridden to `t-pose`, the preset-enriched prompt uses `T-pose` instead of the default `A-pose`.
- Real API calls should be tested in this order: `--print-tools`, `--check-auth`, `--balance`, asset-pack `--dry-run`, and only then `--confirm-spend`.

## Repository Structure

```text
skills/
  write-meshy-prompts/
plugins/
  meshy-prompt-studio/
    .codex-plugin/plugin.json
    .mcp.json
    mcp/meshy_mcp_server.py
    mcp/meshy/
    skills/write-meshy-prompts/
docs/
  asset-pack-workflow.md
  superpowers/specs/
examples/
  prompts/
  asset-pack/
tests/
```

## Development

Run the test suite:

```bash
python -m unittest discover tests
```

Run a syntax/import smoke check:

```bash
python -m compileall plugins tests
```

Contribution guidance lives in [CONTRIBUTING.md](CONTRIBUTING.md). Release notes are tracked in [CHANGELOG.md](CHANGELOG.md).

## Security Notes

- Meshy API keys are read from `MESHY_API_KEY` or an external credential file.
- Meshy API/MCP workflows require a configured API key. Without one, only prompt-only skill guidance and local schema checks such as `--print-tools` are available.
- Generated outputs are ignored by Git through `.gitignore`.
- The MCP server does not echo configured API keys in tool responses.
- Paid Meshy generation requires an explicit approval flag in the asset-pack workflow.

## Notes

This project is not affiliated with or endorsed by Meshy. Meshy is a trademark of its respective owner.

The skill includes prompt workflow guidance based on official Meshy documentation, Meshy blog posts, and practical community workflow signals collected in April 2026. Official Meshy documentation should be treated as authoritative for current platform behavior.

## License

MIT License. See [LICENSE.txt](LICENSE.txt).
