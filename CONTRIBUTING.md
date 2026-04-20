# Contributing

Thanks for helping improve Meshy Codex Skills. The project is intentionally small: a prompt skill, a Codex plugin, a local Python MCP server, examples, and tests.

## Local Setup

Requirements:

- Python 3.10 or newer.
- No third-party runtime dependencies.
- A Meshy API key only for live API calls. Tests use fake transports and do not need a key.

Set up and test:

```bash
git clone https://github.com/ArdaDDemir/meshy-codex-skills.git
cd meshy-codex-skills
python -m pip install -r requirements.txt
python -m compileall plugins scripts tests
python -m unittest discover tests
python scripts/check_project.py
python scripts/package_plugin.py
```

## Development Notes

- Keep the root skill and plugin-bundled skill aligned when changing `write-meshy-prompts`.
- Prefer Python standard-library code unless a dependency clearly pays for itself.
- Keep paid Meshy operations behind explicit confirmation.
- Keep test-mode messaging honest: it validates integration flow, not real generation.
- Do not commit generated assets, API keys, credential files, or local run history.
- Add or update tests for behavior changes in the MCP server, CLI, validation, or workflows.

## Pull Request Checklist

- The README or plugin docs are updated when user-facing behavior changes.
- `python -m unittest discover tests` passes.
- `python -m compileall plugins scripts tests` passes.
- `python scripts/check_no_secrets.py` passes.
- `python scripts/check_project.py` passes.
- Secrets and generated outputs are not included.
- Changes preserve the existing skill + plugin + MCP architecture unless the PR explains why a larger change is needed.
