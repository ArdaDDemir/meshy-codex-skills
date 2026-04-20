import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
SERVER_PATH = REPO_ROOT / "plugins" / "meshy-prompt-studio" / "mcp" / "meshy_mcp_server.py"
MCP_ROOT = SERVER_PATH.parent


def load_server_module():
    if str(MCP_ROOT) not in sys.path:
        sys.path.insert(0, str(MCP_ROOT))
    spec = importlib.util.spec_from_file_location("meshy_mcp_server", SERVER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeTransport:
    def __init__(self, responses=None, downloads=None):
        self.responses = list(responses or [])
        self.downloads = downloads or {}
        self.requests = []

    def request(self, method, path, api_key, payload=None, query=None):
        self.requests.append(
            {
                "method": method,
                "path": path,
                "api_key": api_key,
                "payload": payload,
                "query": query,
            }
        )
        if not self.responses:
            raise AssertionError(f"No fake response available for {method} {path}")
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    def download(self, url):
        self.requests.append({"method": "DOWNLOAD", "url": url})
        return self.downloads.get(url, f"bytes for {url}".encode("utf-8"))


class AssetPackWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.module = load_server_module()
        self._old_env = dict(os.environ)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._old_env)

    def test_preview_normalizes_pose_mode_and_target_formats_before_api_call(self):
        transport = FakeTransport([{"result": "preview-task-id"}])
        client = self.module.MeshyClient(api_key="msy_test_key", transport=transport)

        client.create_text_to_3d_preview(
            {"prompt": "humanoid teacher", "pose_mode": "A-pose", "target_formats": ["GLB", "fbx"]}
        )

        payload = transport.requests[0]["payload"]
        self.assertEqual(payload["pose_mode"], "a-pose")
        self.assertEqual(payload["target_formats"], ["glb", "fbx"])

    def test_unsupported_target_format_fails_before_api_call(self):
        transport = FakeTransport([{"result": "unused"}])
        client = self.module.MeshyClient(api_key="msy_test_key", transport=transport)

        with self.assertRaises(self.module.MeshyError):
            client.create_text_to_3d_preview({"prompt": "prop", "target_formats": ["blend"]})

        self.assertEqual(transport.requests, [])

    def test_refine_rejects_texture_prompt_and_texture_image_conflict(self):
        transport = FakeTransport([{"result": "unused"}])
        client = self.module.MeshyClient(api_key="msy_test_key", transport=transport)

        with self.assertRaises(self.module.MeshyError):
            client.refine_text_to_3d(
                {
                    "preview_task_id": "preview-id",
                    "texture_prompt": "painted wood",
                    "texture_image_url": "https://assets.meshy.ai/texture.png",
                }
            )

        self.assertEqual(transport.requests, [])

    def test_asset_pack_dry_run_applies_preset_without_sending_requests(self):
        transport = FakeTransport()
        client = self.module.MeshyClient(api_key="msy_test_key", transport=transport)

        result = client.create_text_to_3d_asset_pack(
            {
                "asset_name": "Teacher Hero",
                "prompt": "friendly classroom teacher character",
                "preset": "riggable-character",
                "dry_run": True,
            }
        )

        self.assertTrue(result["dry_run"])
        self.assertEqual(result["estimated_credits"], 30)
        self.assertEqual(result["preview_payload"]["pose_mode"], "a-pose")
        self.assertEqual(result["preview_payload"]["target_formats"], ["glb", "fbx"])
        self.assertIn("A-pose", result["preview_payload"]["prompt"])
        self.assertIn("rig-friendly", result["preset_notes"][0].lower())
        self.assertEqual(transport.requests, [])

    def test_riggable_asset_pack_t_pose_override_updates_prompt_suffix(self):
        transport = FakeTransport()
        client = self.module.MeshyClient(api_key="msy_test_key", transport=transport)

        result = client.create_text_to_3d_asset_pack(
            {
                "asset_name": "Teacher T Pose",
                "prompt": "friendly classroom teacher character",
                "preset": "riggable_character",
                "pose_mode": "T-pose",
                "dry_run": True,
            }
        )

        self.assertTrue(result["dry_run"])
        self.assertEqual(result["preview_payload"]["pose_mode"], "t-pose")
        self.assertIn("T-pose", result["preview_payload"]["prompt"])
        self.assertNotIn("A-pose", result["preview_payload"]["prompt"])
        self.assertEqual(transport.requests, [])

    def test_text_to_3d_other_model_cost_uses_april_2026_pricing(self):
        transport = FakeTransport()
        client = self.module.MeshyClient(api_key="msy_test_key", transport=transport)

        result = client.create_text_to_3d_asset_pack(
            {
                "asset_name": "Legacy Model",
                "prompt": "simple prop",
                "ai_model": "meshy-5",
                "dry_run": True,
            }
        )

        self.assertEqual(result["estimated_credits"], 20)
        self.assertEqual(result["costs_as_of"], "2026-04-20")
        self.assertEqual(transport.requests, [])

    def test_asset_pack_requires_spend_confirmation_before_paid_request(self):
        transport = FakeTransport([{"balance": 9999}])
        client = self.module.MeshyClient(api_key="msy_test_key", transport=transport)

        with TemporaryDirectory() as temp_dir:
            with self.assertRaises(self.module.MeshyError) as context:
                client.create_text_to_3d_asset_pack(
                    {
                        "asset_name": "Needs Approval",
                        "prompt": "small prop",
                        "output_dir": str(Path(temp_dir) / "outputs"),
                    }
                )

        self.assertEqual(context.exception.details["estimated_credits"], 30)
        self.assertEqual(context.exception.details["costs_as_of"], "2026-04-20")
        self.assertEqual(transport.requests, [])

    def test_asset_pack_spend_guard_blocks_before_any_api_request(self):
        transport = FakeTransport([{"balance": 9999}])
        client = self.module.MeshyClient(api_key="msy_test_key", transport=transport)

        with self.assertRaises(self.module.MeshyError):
            client.create_text_to_3d_asset_pack(
                {
                    "asset_name": "too-expensive",
                    "prompt": "small prop",
                    "max_spend": 5,
                }
            )

        self.assertEqual(transport.requests, [])

    def test_text_to_3d_asset_pack_happy_path_writes_manifest_prompt_history_and_assets(self):
        preview_glb = "https://assets.meshy.ai/preview.glb"
        preview_png = "https://assets.meshy.ai/preview.png"
        final_glb = "https://assets.meshy.ai/final.glb"
        base_color = "https://assets.meshy.ai/base-color.png"
        normal = "https://assets.meshy.ai/normal.png"
        responses = [
            {"balance": 1574},
            {"result": "preview-id"},
            {
                "id": "preview-id",
                "status": "SUCCEEDED",
                "progress": 100,
                "model_urls": {"glb": preview_glb},
                "thumbnail_url": preview_png,
                "texture_urls": [],
            },
            {"result": "refine-id"},
            {
                "id": "refine-id",
                "status": "SUCCEEDED",
                "progress": 100,
                "model_urls": {"glb": final_glb},
                "thumbnail_url": "https://assets.meshy.ai/final.png",
                "texture_urls": [{"base_color": base_color, "normal": normal}],
            },
            {"balance": 1544},
        ]
        downloads = {
            preview_glb: b"preview-glb",
            preview_png: b"preview-png",
            final_glb: b"final-glb",
            base_color: b"base-color",
            normal: b"normal",
        }
        transport = FakeTransport(responses, downloads)
        client = self.module.MeshyClient(api_key="msy_test_key", transport=transport)

        with TemporaryDirectory() as temp_dir:
            history_path = Path(temp_dir) / ".meshy" / "history.jsonl"
            result = client.create_text_to_3d_asset_pack(
                {
                    "asset_name": "Teacher Model",
                    "prompt": "friendly classroom teacher character",
                    "texture_prompt": "warm fabric, clean classroom colors",
                    "preset": "game_prop",
                    "confirm_spend": True,
                    "output_dir": str(Path(temp_dir) / "outputs"),
                    "history_path": str(history_path),
                    "poll_interval_seconds": 0,
                    "timeout_seconds": 30,
                }
            )

            asset_dir = Path(result["asset_dir"])
            self.assertEqual((asset_dir / "model.glb").read_bytes(), b"final-glb")
            self.assertEqual((asset_dir / "preview.glb").read_bytes(), b"preview-glb")
            self.assertEqual((asset_dir / "preview.png").read_bytes(), b"preview-png")
            self.assertEqual((asset_dir / "textures" / "base_color.png").read_bytes(), b"base-color")
            self.assertEqual((asset_dir / "textures" / "normal.png").read_bytes(), b"normal")

            manifest = json.loads((asset_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["preview_task_id"], "preview-id")
            self.assertEqual(manifest["refine_task_id"], "refine-id")
            self.assertEqual(manifest["credits_spent"], 30)
            self.assertEqual(manifest["balance_before"], 1574)
            self.assertEqual(manifest["balance_after"], 1544)
            self.assertNotIn("msy_test_key", json.dumps(manifest))
            self.assertIn("friendly classroom teacher character", (asset_dir / "prompt.md").read_text())

            history_records = [json.loads(line) for line in history_path.read_text().splitlines()]
            self.assertEqual(len(history_records), 1)
            self.assertEqual(history_records[0]["asset_name"], "Teacher Model")
            self.assertEqual(history_records[0]["status"], "SUCCEEDED")

        preview_posts = [
            request for request in transport.requests if request.get("method") == "POST" and request["payload"]["mode"] == "preview"
        ]
        refine_posts = [
            request for request in transport.requests if request.get("method") == "POST" and request["payload"]["mode"] == "refine"
        ]
        self.assertEqual(len(preview_posts), 1)
        self.assertEqual(len(refine_posts), 1)
        self.assertEqual(refine_posts[0]["payload"]["preview_task_id"], "preview-id")

    def test_failed_preview_stops_before_refine_and_records_manifest_history(self):
        responses = [
            {"balance": 100},
            {"result": "preview-id"},
            {
                "id": "preview-id",
                "status": "FAILED",
                "progress": 100,
                "task_error": {"message": "bad prompt"},
            },
            {"balance": 80},
        ]
        transport = FakeTransport(responses)
        client = self.module.MeshyClient(api_key="msy_test_key", transport=transport)

        with TemporaryDirectory() as temp_dir:
            history_path = Path(temp_dir) / ".meshy" / "history.jsonl"
            result = client.create_text_to_3d_asset_pack(
                {
                    "asset_name": "Failed Model",
                    "prompt": "bad prompt",
                    "confirm_spend": True,
                    "output_dir": str(Path(temp_dir) / "outputs"),
                    "history_path": str(history_path),
                    "poll_interval_seconds": 0,
                }
            )

            asset_dir = Path(result["asset_dir"])
            manifest = json.loads((asset_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["final_status"], "FAILED")
            self.assertEqual(manifest["refine_task_id"], None)
            self.assertEqual(json.loads(history_path.read_text())["status"], "FAILED")

        refine_posts = [
            request
            for request in transport.requests
            if request.get("method") == "POST" and request.get("payload", {}).get("mode") == "refine"
        ]
        self.assertEqual(refine_posts, [])

    def test_missing_texture_urls_do_not_fail_asset_pack(self):
        final_glb = "https://assets.meshy.ai/final.glb"
        responses = [
            {"balance": 50},
            {"result": "preview-id"},
            {"id": "preview-id", "status": "SUCCEEDED", "model_urls": {}, "texture_urls": []},
            {"result": "refine-id"},
            {"id": "refine-id", "status": "SUCCEEDED", "model_urls": {"glb": final_glb}, "texture_urls": []},
            {"balance": 20},
        ]
        transport = FakeTransport(responses, {final_glb: b"final-glb"})
        client = self.module.MeshyClient(api_key="msy_test_key", transport=transport)

        with TemporaryDirectory() as temp_dir:
            result = client.create_text_to_3d_asset_pack(
                {
                    "asset_name": "No Textures",
                    "prompt": "plain prop",
                    "confirm_spend": True,
                    "output_dir": str(Path(temp_dir) / "outputs"),
                    "history_path": str(Path(temp_dir) / ".meshy" / "history.jsonl"),
                    "poll_interval_seconds": 0,
                }
            )

            manifest = json.loads((Path(result["asset_dir"]) / "manifest.json").read_text())
            self.assertEqual(manifest["final_status"], "SUCCEEDED")
            self.assertIn("textures", manifest["missing_optional_assets"])

    def test_overwrite_false_refuses_existing_asset_folder_before_api_request(self):
        transport = FakeTransport()
        client = self.module.MeshyClient(api_key="msy_test_key", transport=transport)

        with TemporaryDirectory() as temp_dir:
            asset_dir = Path(temp_dir) / "outputs" / "existing"
            asset_dir.mkdir(parents=True)

            with self.assertRaises(self.module.MeshyError):
                client.create_text_to_3d_asset_pack(
                    {
                        "asset_name": "existing",
                        "prompt": "small prop",
                        "confirm_spend": True,
                        "output_dir": str(Path(temp_dir) / "outputs"),
                    }
                )

        self.assertEqual(transport.requests, [])

    def test_cli_create_text_asset_routes_to_asset_pack_workflow(self):
        calls = []

        class FakeClient:
            def create_text_to_3d_asset_pack(self, arguments):
                calls.append(arguments)
                return {"ok": True, "asset_name": arguments["asset_name"], "preset": arguments["preset"]}

        original_client_from_config = self.module.client_from_config
        self.module.client_from_config = lambda: FakeClient()
        try:
            with TemporaryDirectory() as temp_dir:
                prompt_path = Path(temp_dir) / "prompt.txt"
                prompt_path.write_text("wooden teacher desk", encoding="utf-8")
                stdout = io.StringIO()
                with contextlib.redirect_stdout(stdout):
                    exit_code = self.module.main(
                        [
                            "--create-text-asset",
                            str(prompt_path),
                            "--name",
                            "teacher-desk",
                            "--preset",
                            "low_poly_asset",
                            "--output-dir",
                            str(Path(temp_dir) / "outputs"),
                            "--dry-run",
                        ]
                    )
        finally:
            self.module.client_from_config = original_client_from_config

        self.assertEqual(exit_code, 0)
        self.assertEqual(calls[0]["prompt"], "wooden teacher desk")
        self.assertEqual(calls[0]["asset_name"], "teacher-desk")
        self.assertEqual(calls[0]["preset"], "low_poly_asset")
        self.assertTrue(calls[0]["dry_run"])
        self.assertIn('"ok": true', stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
