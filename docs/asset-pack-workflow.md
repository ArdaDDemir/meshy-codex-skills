# Asset Pack Workflow

The asset-pack workflow is the production-oriented part of Meshy Prompt Studio. It turns one Text to 3D prompt into a local package with downloaded assets, metadata, and a prompt record.

Use it when you want Codex or the local CLI to handle the full loop:

1. Create a Text to 3D preview task.
2. Wait for the preview task to finish.
3. Download preview assets when available.
4. Optionally create and wait for a refine task.
5. Download final models and texture maps when available.
6. Write `manifest.json`, `prompt.md`, and `.meshy/history.jsonl`.

## Primary Tool

```text
meshy_create_text_to_3d_asset_pack
```

Required fields:

- `asset_name`
- `prompt`

Useful optional fields:

- `preset`
- `output_dir`
- `texture_prompt`
- `refine`
- `target_formats`
- `enable_pbr`
- `max_spend`
- `min_balance`
- `confirm_spend`
- `dry_run`
- `overwrite`
- `poll_interval_seconds`
- `timeout_seconds`

## Presets

| Preset | Best for | Defaults |
| --- | --- | --- |
| `game_prop` | General static game props | GLB output, refine on, PBR textures on |
| `low_poly_asset` | Mobile, stylized, or performance-sensitive assets | `model_type=lowpoly`, GLB output, refine on |
| `riggable_character` | Humanoid characters intended for later rigging | A-pose, symmetry on, GLB and FBX output where supported |
| `printable_model` | 3D print-oriented objects | STL and 3MF output, print-safe prompt hints, PBR off |

## Budget Guards

Real Meshy generation, refine, remesh, rigging, animation, and retexture calls can spend API credits. The asset-pack workflow is intentionally conservative:

- `max_spend`: `35`
- `min_balance`: `0`
- `confirm_spend`: `false`
- `dry_run`: `false`
- `overwrite`: `false`

The workflow reports the estimated cost and refuses paid generation unless `confirm_spend=true` is provided. Use `dry_run=true` to inspect planned payloads without creating paid tasks.

Cost reference used by the plugin as of 2026-04-20:

| Operation | Estimated credits |
| --- | ---: |
| Text to 3D preview, Meshy 6 models | 20 |
| Text to 3D preview, other models | 10 |
| Text to 3D refine | 10 |
| Image to 3D, Meshy 6 models without texture | 20 |
| Image to 3D, Meshy 6 models with texture | 30 |
| Image to 3D, other models without texture | 5 |
| Image to 3D, other models with texture | 15 |
| Multi Image to 3D without texture | 5 |
| Multi Image to 3D with texture | 15 |
| Retexture | 10 |
| Remesh | 5 |
| Auto-rigging | 5 |
| Animation | 3 |

## Output Layout

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

Some files are optional because Meshy task responses vary by model, selected target formats, and task status. Missing optional files are recorded in `manifest.json`.

## Local CLI Examples

Dry-run a planned asset pack:

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

Check balance:

```bash
python plugins/meshy-prompt-studio/mcp/meshy_mcp_server.py --balance
```

Wait for an existing task:

```bash
python plugins/meshy-prompt-studio/mcp/meshy_mcp_server.py --wait TASK_ID --type text-to-3d
```

Download a completed task:

```bash
python plugins/meshy-prompt-studio/mcp/meshy_mcp_server.py --download TASK_ID --type text-to-3d --out outputs/teacher
```

Download a completed task using the clearer recovery alias:

```bash
python plugins/meshy-prompt-studio/mcp/meshy_mcp_server.py --download-existing TASK_ID --type text-to-3d --out outputs/teacher
```

List recent tasks:

```bash
python plugins/meshy-prompt-studio/mcp/meshy_mcp_server.py --list-recent text-to-3d
```

List local workflow history:

```bash
python plugins/meshy-prompt-studio/mcp/meshy_mcp_server.py --history
```

Resume a known asset pack from `.meshy/history.jsonl`, wait for its latest task, and download available assets:

```bash
python plugins/meshy-prompt-studio/mcp/meshy_mcp_server.py --resume treasure-chest
```

Open the recorded manifest summary for a known asset name, slug, or task id:

```bash
python plugins/meshy-prompt-studio/mcp/meshy_mcp_server.py --open-manifest treasure-chest
```

The recorded `manifest.json` and `.meshy/history.jsonl` now keep recovery-oriented fields such as:

- `latest_task_id`
- `manifest_path`
- `failure_stage`
- `task_error`
- `recovery_hint`
- `downloadable_assets`

## Safety Checklist

- Run `--dry-run` before your first paid task.
- Use `--test-mode` for API integration checks that should not consume credits.
- Treat `--test-mode` as an integration check only. It does not mean a real asset was generated.
- Keep `MESHY_API_KEY` out of source-controlled files.
- Use `max_spend` and `min_balance` for budget protection.
- Keep generated `outputs/`, `.meshy/`, and `meshy-downloads/` out of Git.
- Inspect the downloaded model in Blender or your target engine before treating it as production-ready.
