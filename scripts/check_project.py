#!/usr/bin/env python3
"""Lightweight release, packaging, and security checks for Meshy Codex Skills."""

from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import zipfile

import check_no_secrets


REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_DIR = REPO_ROOT / "plugins" / "meshy-prompt-studio"
GENERATED_PREFIXES = (".meshy/", "outputs/", "meshy-downloads/", "meshy_assets/")
DOC_FILES = [
    REPO_ROOT / "README.md",
    REPO_ROOT / "SECURITY.md",
    REPO_ROOT / "docs" / "asset-pack-workflow.md",
    PLUGIN_DIR / "README.md",
]
DOCUMENTED_PATHS = [
    ".agents/plugins/marketplace.json",
    "docs/test-mode.md",
    "examples/asset-pack/manifest.example.json",
    "examples/prompts/treasure-chest.prompt.txt",
    "plugins/meshy-prompt-studio/.codex-plugin/plugin.json",
    "plugins/meshy-prompt-studio/.mcp.json",
    "plugins/meshy-prompt-studio/assets/icon.png",
    "plugins/meshy-prompt-studio/assets/logo.png",
    "plugins/meshy-prompt-studio/assets/screenshot-first-run.png",
    "plugins/meshy-prompt-studio/assets/screenshot-dry-run.png",
    "plugins/meshy-prompt-studio/assets/screenshot-recovery.png",
    "plugins/meshy-prompt-studio/mcp/meshy_mcp_server.py",
    "scripts/check_no_secrets.py",
    "scripts/package_plugin.py",
]
MARKDOWN_LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
HEX_COLOR_PATTERN = re.compile(r"#[0-9A-Fa-f]{6}$")
PACKAGE_BASE_MEMBERS = {
    ".codex-plugin/plugin.json",
    ".mcp.json",
    "LICENSE.txt",
    "README.md",
    "mcp/meshy_mcp_server.py",
    "skills/write-meshy-prompts/SKILL.md",
}


def main() -> int:
    checks = [
        check_json_files,
        check_plugin_manifest,
        check_mcp_config,
        check_marketplace_entry,
        check_version_sync,
        check_no_tracked_generated_outputs,
        check_no_private_meshy_keys,
        check_required_docs,
        check_documented_paths_exist,
        check_print_tools_smoke,
        check_package_smoke,
    ]
    failures: list[str] = []
    for check in checks:
        try:
            check()
            print(f"ok: {check.__name__}")
        except AssertionError as exc:
            failures.append(f"{check.__name__}: {exc}")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    return 0


def check_json_files() -> None:
    for path in [
        PLUGIN_DIR / ".codex-plugin" / "plugin.json",
        PLUGIN_DIR / ".mcp.json",
        REPO_ROOT / ".agents" / "plugins" / "marketplace.json",
        REPO_ROOT / "examples" / "asset-pack" / "manifest.example.json",
    ]:
        load_json(path)


def check_plugin_manifest() -> None:
    manifest = load_json(PLUGIN_DIR / ".codex-plugin" / "plugin.json")
    interface = manifest.get("interface")
    assert manifest.get("name") == "meshy-prompt-studio", "plugin manifest name must be meshy-prompt-studio"
    assert isinstance(manifest.get("version"), str) and manifest["version"], "plugin version is required"
    assert isinstance(interface, dict), "plugin interface block is required"
    for key in ("description", "homepage", "repository", "license", "skills", "mcpServers"):
        assert isinstance(manifest.get(key), str) and manifest[key], f"plugin manifest missing '{key}'"
    for key in (
        "displayName",
        "shortDescription",
        "longDescription",
        "developerName",
        "category",
        "websiteURL",
        "privacyPolicyURL",
        "termsOfServiceURL",
        "brandColor",
        "composerIcon",
        "logo",
    ):
        assert isinstance(interface.get(key), str) and interface[key], f"plugin interface missing '{key}'"
    assert HEX_COLOR_PATTERN.match(interface["brandColor"]), "brandColor must be a #RRGGBB hex value"
    assert interface.get("capabilities") == ["Interactive", "Read", "Write"], "unexpected capabilities list"

    for rel_path in (manifest["skills"], manifest["mcpServers"], interface["composerIcon"], interface["logo"]):
        assert rel_path.startswith("./"), f"path must be plugin-relative: {rel_path}"
        assert (PLUGIN_DIR / rel_path.removeprefix("./")).exists(), f"missing plugin asset/path: {rel_path}"

    prompts = interface.get("defaultPrompt")
    assert isinstance(prompts, list) and 1 <= len(prompts) <= 3, "defaultPrompt must contain 1 to 3 entries"
    for prompt in prompts:
        assert isinstance(prompt, str) and prompt.strip(), "defaultPrompt entries must be non-empty strings"
        assert len(prompt) <= 128, f"defaultPrompt exceeds 128 chars: {prompt!r}"

    screenshots = interface.get("screenshots")
    assert isinstance(screenshots, list) and 2 <= len(screenshots) <= 3, "screenshots must contain 2 or 3 PNG paths"
    for screenshot in screenshots:
        assert isinstance(screenshot, str) and screenshot.startswith("./assets/"), f"bad screenshot path: {screenshot}"
        assert screenshot.endswith(".png"), f"screenshot must be a PNG: {screenshot}"
        assert (PLUGIN_DIR / screenshot.removeprefix("./")).exists(), f"missing screenshot asset: {screenshot}"


def check_mcp_config() -> None:
    payload = load_json(PLUGIN_DIR / ".mcp.json")
    servers = payload.get("mcpServers")
    assert isinstance(servers, dict) and "meshy-api" in servers, "missing mcpServers.meshy-api entry"
    server = servers["meshy-api"]
    assert server.get("command") == "python", "meshy-api MCP server must run with python"
    args = server.get("args")
    assert isinstance(args, list) and len(args) == 1, "meshy-api MCP server must expose a single script arg"
    script_path = str(args[0])
    assert script_path.startswith("./"), "MCP script path must stay plugin-relative"
    assert (PLUGIN_DIR / script_path.removeprefix("./")).exists(), f"missing MCP script path: {script_path}"


def check_marketplace_entry() -> None:
    marketplace = load_json(REPO_ROOT / ".agents" / "plugins" / "marketplace.json")
    plugins = marketplace.get("plugins")
    assert isinstance(plugins, list) and plugins, "marketplace must contain at least one plugin entry"
    plugin = next((item for item in plugins if item.get("name") == "meshy-prompt-studio"), None)
    assert plugin is not None, "marketplace is missing meshy-prompt-studio entry"
    source = plugin.get("source") or {}
    policy = plugin.get("policy") or {}
    assert source.get("source") == "local", "marketplace entry must use local source"
    assert source.get("path") == "./plugins/meshy-prompt-studio", "marketplace path must point at the plugin folder"
    assert (REPO_ROOT / "plugins" / "meshy-prompt-studio").exists(), "marketplace plugin path does not exist"
    assert policy.get("installation") == "AVAILABLE", "unexpected marketplace installation policy"
    assert policy.get("authentication") == "ON_INSTALL", "unexpected marketplace auth policy"
    assert isinstance(plugin.get("category"), str) and plugin["category"], "marketplace category is required"


def check_version_sync() -> None:
    manifest = load_json(PLUGIN_DIR / ".codex-plugin" / "plugin.json")
    version = manifest["version"]
    server_text = (PLUGIN_DIR / "mcp" / "meshy_mcp_server.py").read_text(encoding="utf-8")
    client_text = (PLUGIN_DIR / "mcp" / "meshy" / "client.py").read_text(encoding="utf-8")
    changelog = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert f'"version": "{version}"' in server_text, "MCP serverInfo version does not match plugin manifest"
    assert f"meshy-prompt-studio/{version}" in client_text, "HTTP User-Agent version does not match plugin manifest"
    assert version in changelog, "CHANGELOG should mention the current plugin version"


def check_no_tracked_generated_outputs() -> None:
    tracked = git_ls_files()
    bad = [path for path in tracked if path.startswith(GENERATED_PREFIXES) or "__pycache__/" in path]
    assert not bad, f"generated files are tracked: {bad}"


def check_no_private_meshy_keys() -> None:
    findings = check_no_secrets.find_private_meshy_keys(REPO_ROOT, git_ls_files())
    assert not findings, "possible private Meshy API keys found: " + ", ".join(findings)


def check_required_docs() -> None:
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    plugin_readme = (PLUGIN_DIR / "README.md").read_text(encoding="utf-8")
    asset_workflow = (REPO_ROOT / "docs" / "asset-pack-workflow.md").read_text(encoding="utf-8")
    security = (REPO_ROOT / "SECURITY.md").read_text(encoding="utf-8")

    for text, label in ((readme, "README.md"), (plugin_readme, "plugin README")):
        assert "--print-tools" in text, f"{label} missing safe tool-list check"
        assert "--dry-run" in text, f"{label} missing dry-run guidance"
        assert "--test-mode --check-auth" in text, f"{label} missing test-mode first run guidance"
        assert "not real generation" in text.lower() or "real generation" in text.lower(), (
            f"{label} should clarify test mode versus real generation"
        )

    assert "--download-existing" in asset_workflow, "asset-pack workflow doc missing --download-existing"
    assert "--open-manifest" in asset_workflow, "asset-pack workflow doc missing --open-manifest"
    assert "Release Checklist" in security, "SECURITY.md missing release checklist"


def check_documented_paths_exist() -> None:
    for rel_path in DOCUMENTED_PATHS:
        assert (REPO_ROOT / rel_path).exists(), f"documented path does not exist: {rel_path}"

    for doc_path in DOC_FILES:
        text = doc_path.read_text(encoding="utf-8")
        for raw_ref in MARKDOWN_LINK_PATTERN.findall(text):
            reference = raw_ref.strip().strip("<>")
            if not reference or "://" in reference or reference.startswith("#") or reference.startswith("mailto:"):
                continue
            reference = reference.split("#", 1)[0]
            candidate = (doc_path.parent / reference).resolve()
            assert candidate.exists(), f"{doc_path.relative_to(REPO_ROOT)} references missing local path: {reference}"


def check_print_tools_smoke() -> None:
    result = subprocess.run(
        [sys.executable, str(PLUGIN_DIR / "mcp" / "meshy_mcp_server.py"), "--print-tools"],
        cwd=REPO_ROOT,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    )
    payload = json.loads(result.stdout)
    tools = payload.get("tools")
    assert isinstance(tools, list) and tools, "--print-tools must return a non-empty tool list"
    tool_names = {tool.get("name") for tool in tools if isinstance(tool, dict)}
    for tool_name in ("meshy_create_multi_image_to_3d", "meshy_refine_text_to_3d", "meshy_retexture"):
        assert tool_name in tool_names, f"missing expected MCP tool: {tool_name}"


def check_package_smoke() -> None:
    manifest = load_json(PLUGIN_DIR / ".codex-plugin" / "plugin.json")
    expected_zip = f"{manifest['name']}-{manifest['version']}.zip"
    with tempfile.TemporaryDirectory() as temp_dir:
        subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "package_plugin.py"), "--out-dir", temp_dir],
            cwd=REPO_ROOT,
            check=True,
            stdout=subprocess.PIPE,
            text=True,
        )
        zip_path = Path(temp_dir) / expected_zip
        assert zip_path.exists(), f"package zip not created: {zip_path}"
        with zipfile.ZipFile(zip_path) as archive:
            members = set(archive.namelist())

    expected_members = set(PACKAGE_BASE_MEMBERS)
    interface = manifest["interface"]
    for rel_path in [interface["composerIcon"], interface["logo"], *interface["screenshots"]]:
        expected_members.add(rel_path.removeprefix("./"))

    missing = sorted(member for member in expected_members if member not in members)
    assert not missing, f"package zip missing expected files: {missing}"
    assert not any("__pycache__/" in member for member in members), "package zip should not include __pycache__"


def load_json(path: Path) -> dict | list:
    return json.loads(path.read_text(encoding="utf-8"))


def git_ls_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    )
    return [line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()]


if __name__ == "__main__":
    raise SystemExit(main())
