# Examples

These examples are intentionally small and safe to commit. They show the shape of a Meshy Prompt Studio workflow without including generated model files or API secrets.

## Prompt Example

Use the sample prompt with a dry run:

```bash
python plugins/meshy-prompt-studio/mcp/meshy_mcp_server.py \
  --create-text-asset examples/prompts/treasure-chest.prompt.txt \
  --name treasure-chest \
  --preset low_poly_asset \
  --dry-run
```

The dry run prints the planned Meshy payload, estimated credits, selected preset, and output directory. It does not call paid Meshy generation endpoints.

## Asset Pack Example

`examples/asset-pack/manifest.example.json` is a small representative manifest. Real manifests include Meshy task IDs, model URLs, texture URLs, local file paths, file sizes, balances, and normalized API parameters.

Generated asset files should stay in `outputs/`, `.meshy/`, or `meshy-downloads/`; those paths are ignored by Git.
