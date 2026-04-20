# Security

Meshy Prompt Studio is a local Codex plugin and MCP server. It can call the Meshy API when you configure a Meshy API key.

## API Keys

- Do not commit Meshy API keys.
- Prefer `MESHY_API_KEY` in your shell environment or the `meshy_configure_api_key` MCP tool.
- Stored credentials live outside the repository:
  - Windows: `%APPDATA%/meshy-prompt-studio/credentials.json`
  - macOS/Linux: `~/.config/meshy-prompt-studio/credentials.json`
- The configure tool does not echo the key back in responses.

## Test Mode

Meshy documents a public test mode API key for integration testing. It does not consume credits and returns sample task responses. Use it only for development and switch to your own API key for real production use.

```bash
python plugins/meshy-prompt-studio/mcp/meshy_mcp_server.py --test-mode --check-auth
```

Official Meshy references:

- https://docs.meshy.ai/en/api/quick-start
- https://docs.meshy.ai/en/api/changelog

Treat test mode as an API plumbing check only. It is not real generation and should not be described as production output.

## Generated Files

Generated models, textures, and local task history should not be committed. The repository ignores:

- `.meshy/`
- `outputs/`
- `meshy-downloads/`
- `meshy_assets/`

Run the project security check before releases:

```bash
python scripts/check_project.py
```

Or run the secret scan on its own:

```bash
python scripts/check_no_secrets.py
```

## Release Checklist

- Run `python -m unittest discover tests`.
- Run `python scripts/check_no_secrets.py`.
- Run `python scripts/check_project.py`.
- Confirm `--print-tools`, `--test-mode --check-auth`, and `--dry-run` are still the documented safe first-run path.
- Confirm no generated assets or local credential files are staged for commit.

## Reporting Issues

Open a GitHub issue if you find a security-sensitive bug in the local workflow, credential handling, or packaging. Do not include private API keys, generated private assets, or account-specific Meshy task URLs in public issues.
