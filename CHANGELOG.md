# Changelog

All notable changes to this project should be documented here.

This project follows a lightweight, human-written changelog format inspired by Keep a Changelog.

## Unreleased

## 1.4.0 - 2026-04-20

- Add release packaging for `meshy-prompt-studio-<version>.zip`.
- Add project release/security checks.
- Add Meshy API test-mode documentation and CLI support.
- Add local asset-pack history listing and resume/download helpers.
- Add `--download-existing` and `--open-manifest` recovery helpers.
- Enrich manifests and history records with recovery metadata and clearer failure hints.
- Split secret scanning into `scripts/check_no_secrets.py`.
- Improve plugin marketplace metadata with screenshots, safer first-run prompts, and clearer UX copy.
- Tighten prompt/skill guidance so texture follow-ups stay attached to the current asset and multi-view is preferred when one angle is insufficient.

## 1.3.0 - 2026-04-20

- Improve first-time onboarding and setup documentation.
- Add lightweight CI for syntax checks and tests.
- Add example prompt and manifest files.
- Document Codex App local plugin/MCP setup, API key requirements, and safe test order.
- Fix `riggable_character` prompt enrichment so T-pose overrides do not retain A-pose wording.
- Make Windows download-path tests robust against short-path and long-path differences.

## 1.2.0

- Add Meshy Prompt Studio plugin packaging.
- Add local Meshy API MCP server.
- Add Text to 3D asset-pack workflow with manifests, prompt records, downloads, and history.
- Add tests for credentials, request construction, polling, validation, and asset-pack behavior.
