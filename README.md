# Meshy Codex Skills

Codex skills for creating production-ready Meshy prompts and workflow guidance for 3D asset generation.

The repository also includes **Meshy Prompt Studio**, a Codex plugin that can call the Meshy API through a local MCP server.

## Skills

### write-meshy-prompts

Create Meshy prompts for:

- Text to 3D
- Image to 3D reference images
- Game-ready static props
- Riggable humanoid characters
- 3D printable models
- Texture and retexture workflows
- Export and production handoff guidance
- Troubleshooting bad Meshy generation results

## Install

Install the skill in Codex with:

```text
$skill-installer install https://github.com/ArdaDDemir/meshy-codex-skills/tree/main/skills/write-meshy-prompts
```

Restart Codex after installing so the new skill is discovered.

## Plugin

This repository also publishes a Codex plugin named **Meshy Prompt Studio**.

The plugin bundles the same `write-meshy-prompts` skill and a local Meshy API MCP server so Codex can write prompts, create Meshy tasks, poll task status, download generated assets, and produce local Text to 3D asset packs with one command.

The plugin manifest is:

```text
plugins/meshy-prompt-studio/.codex-plugin/plugin.json
```

The repository marketplace entry is:

```text
.agents/plugins/marketplace.json
```

The MCP server is declared in:

```text
plugins/meshy-prompt-studio/.mcp.json
```

After installing the plugin in Codex, configure authentication with either:

```text
Use the Meshy API MCP tool to configure my Meshy API key.
```

or set `MESHY_API_KEY` in the local environment before starting Codex.

The MCP server stores configured API keys outside the repository:

```text
%APPDATA%/meshy-prompt-studio/credentials.json
```

on Windows, or:

```text
~/.config/meshy-prompt-studio/credentials.json
```

on macOS/Linux.

Do not commit API keys. The repository does not include any Meshy API credentials.

After authentication, use the plugin with:

```text
Use Meshy to create a low-poly treasure chest asset pack.
```

Direct plugin source:

```text
https://github.com/ArdaDDemir/meshy-codex-skills/tree/main/plugins/meshy-prompt-studio
```

### Asset Pack Workflow

The primary production tool is:

```text
meshy_create_text_to_3d_asset_pack
```

It creates a Text to 3D preview task, waits for completion, optionally creates the refine task, downloads the generated model and texture assets, writes metadata, and appends a local run history.

Default budget guards are conservative:

- `max_spend`: 35 estimated credits
- `min_balance`: 0 credits
- `confirm_spend`: false
- `dry_run`: false
- `overwrite`: false

Real generation, refine, remesh, rigging, animation, and retexture calls can spend Meshy API credits. The asset pack workflow reports the estimated cost first and requires `confirm_spend=true` before it creates paid Meshy tasks. Use `dry_run=true` to preview the planned API payload and estimated credits without sending paid generation requests.

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

Asset packs are written as:

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

`manifest.json` records task IDs, normalized API parameters, model and texture URLs, output paths, file sizes, balance before/after, and credits spent. `.meshy/history.jsonl` stores compact workflow history for future resume/download features.

Copy-paste examples:

```text
Use Meshy to create a Text to 3D asset pack named teacher-model with this prompt: friendly classroom teacher character, clean stylized proportions, warm cardigan, simple readable face. Use preset riggable_character. Tell me the estimated credit cost before spending credits.
```

```text
Use Meshy to create a low-poly asset pack named treasure-chest with this prompt: chunky low-poly wooden treasure chest with metal bands, readable silhouette, game-ready proportions. Use preset low_poly_asset.
```

```text
Use Meshy to create a printable asset pack named desk-organizer with this prompt: compact 3D printable desk organizer with rounded slots, stable base, no thin fragile parts. Use preset printable_model.
```

```text
Use Meshy to dry-run a game prop asset pack named potion-bottle with this prompt: small fantasy potion bottle with cork, glass body, readable silhouette. Use preset game_prop and dry_run=true.
```

Local CLI examples:

```text
python plugins/meshy-prompt-studio/mcp/meshy_mcp_server.py --balance
python plugins/meshy-prompt-studio/mcp/meshy_mcp_server.py --create-text-asset prompt.txt --name teacher --preset riggable_character --confirm-spend
python plugins/meshy-prompt-studio/mcp/meshy_mcp_server.py --create-text-asset prompt.txt --name crate --preset low_poly_asset --dry-run
python plugins/meshy-prompt-studio/mcp/meshy_mcp_server.py --wait TASK_ID --type text-to-3d
python plugins/meshy-prompt-studio/mcp/meshy_mcp_server.py --download TASK_ID --type text-to-3d --out outputs/teacher
python plugins/meshy-prompt-studio/mcp/meshy_mcp_server.py --list-recent text-to-3d
```

## Example Prompts

```text
Use $write-meshy-prompts to create a Meshy prompt pack for a riggable low-poly goblin enemy for Unity.
```

```text
Use $write-meshy-prompts to create separate Meshy prompts for a game-ready treasure chest and a 3D printable version of the same concept.
```

```text
Use $write-meshy-prompts to improve this Meshy prompt for Image to 3D and explain what settings I should use.
```

## Repository Structure

```text
skills/
  write-meshy-prompts/
    SKILL.md
    agents/openai.yaml
    references/meshy-prompt-master-guide.md
    LICENSE.txt
plugins/
  meshy-prompt-studio/
    .codex-plugin/plugin.json
    .mcp.json
    README.md
    LICENSE.txt
    mcp/meshy_mcp_server.py
    mcp/meshy/
    skills/write-meshy-prompts/
.agents/
  plugins/marketplace.json
docs/
  superpowers/specs/
tests/
```

## Notes

This project is not affiliated with or endorsed by Meshy. Meshy is a trademark of its respective owner.

The skill includes prompt workflow guidance based on official Meshy documentation, Meshy blog posts, and practical community workflow signals collected in April 2026. Official Meshy documentation should be treated as authoritative for current platform behavior.

## License

MIT License. See [LICENSE.txt](LICENSE.txt).
