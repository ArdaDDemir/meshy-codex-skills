import base64
import importlib.util
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
    def __init__(self, responses):
        self.responses = list(responses)
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
            raise AssertionError("No fake response available")
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    def download(self, url):
        self.requests.append({"method": "DOWNLOAD", "url": url})
        return b"glb-bytes"


class MeshyMcpServerTests(unittest.TestCase):
    def setUp(self):
        self.module = load_server_module()
        self._old_env = dict(os.environ)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._old_env)

    def test_configure_api_key_stores_key_outside_repo_without_echoing_it(self):
        with TemporaryDirectory() as temp_dir:
            credential_path = Path(temp_dir) / "credentials.json"
            os.environ["MESHY_CREDENTIALS_PATH"] = str(credential_path)
            secret = "msy_test_secret"

            result = self.module.configure_api_key({"api_key": secret})

            self.assertEqual(result["credential_path"], str(credential_path))
            self.assertTrue(result["configured"])
            self.assertNotIn(secret, json.dumps(result))
            stored = json.loads(credential_path.read_text())
            self.assertEqual(stored["api_key"], secret)

    def test_env_api_key_takes_priority_over_credential_file(self):
        with TemporaryDirectory() as temp_dir:
            credential_path = Path(temp_dir) / "credentials.json"
            os.environ["MESHY_CREDENTIALS_PATH"] = str(credential_path)
            os.environ["MESHY_API_KEY"] = "msy_from_env"
            credential_path.write_text(json.dumps({"api_key": "msy_from_file"}))

            self.assertEqual(self.module.resolve_api_key(), "msy_from_env")

    def test_default_credential_path_resolves_outside_repo(self):
        os.environ.pop("MESHY_CREDENTIALS_PATH", None)
        os.environ.pop("MESHY_API_KEY", None)
        with TemporaryDirectory() as temp_dir:
            os.environ["APPDATA"] = temp_dir

            resolved = self.module.credential_path().resolve()

        self.assertFalse(resolved.is_relative_to(REPO_ROOT.resolve()))
        self.assertEqual(resolved.name, "credentials.json")
        self.assertIn("meshy-prompt-studio", str(resolved))

    def test_get_balance_calls_meshy_balance_endpoint(self):
        transport = FakeTransport([{"balance": 123}])
        client = self.module.MeshyClient(api_key="msy_test_key", transport=transport)

        result = client.get_balance()

        self.assertEqual(result, {"balance": 123})
        self.assertEqual(transport.requests[0]["method"], "GET")
        self.assertEqual(transport.requests[0]["path"], "/openapi/v1/balance")
        self.assertEqual(transport.requests[0]["api_key"], "msy_test_key")

    def test_create_text_to_3d_preview_posts_preview_payload(self):
        transport = FakeTransport([{"result": "preview-task-id"}])
        client = self.module.MeshyClient(api_key="msy_test_key", transport=transport)

        result = client.create_text_to_3d_preview(
            {
                "prompt": "low-poly treasure chest",
                "target_formats": ["glb"],
                "pose_mode": "",
            }
        )

        self.assertEqual(result["task_id"], "preview-task-id")
        request = transport.requests[0]
        self.assertEqual(request["method"], "POST")
        self.assertEqual(request["path"], "/openapi/v2/text-to-3d")
        self.assertEqual(request["payload"]["mode"], "preview")
        self.assertEqual(request["payload"]["prompt"], "low-poly treasure chest")
        self.assertEqual(request["payload"]["target_formats"], ["glb"])
        self.assertNotIn("api_key", result)

    def test_image_to_3d_converts_local_image_path_to_data_uri(self):
        with TemporaryDirectory() as temp_dir:
            image_path = Path(temp_dir) / "reference.png"
            image_path.write_bytes(b"png-data")
            transport = FakeTransport([{"result": "image-task-id"}])
            client = self.module.MeshyClient(api_key="msy_test_key", transport=transport)

            result = client.create_image_to_3d({"image_path": str(image_path)})

            self.assertEqual(result["task_id"], "image-task-id")
            payload = transport.requests[0]["payload"]
            expected = base64.b64encode(b"png-data").decode("ascii")
            self.assertEqual(payload["image_url"], f"data:image/png;base64,{expected}")

    def test_wait_for_task_polls_until_terminal_status(self):
        transport = FakeTransport(
            [
                {"id": "task-id", "status": "PENDING", "progress": 0},
                {"id": "task-id", "status": "IN_PROGRESS", "progress": 50},
                {"id": "task-id", "status": "SUCCEEDED", "progress": 100},
            ]
        )
        client = self.module.MeshyClient(api_key="msy_test_key", transport=transport)

        result = client.wait_for_task(
            {"task_type": "text-to-3d", "task_id": "task-id", "poll_interval_seconds": 0}
        )

        self.assertEqual(result["status"], "SUCCEEDED")
        self.assertEqual(len(transport.requests), 3)
        self.assertEqual(transport.requests[0]["path"], "/openapi/v2/text-to-3d/task-id")

    def test_download_asset_writes_bytes_without_overwrite_by_default(self):
        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "model.glb"
            transport = FakeTransport([])
            client = self.module.MeshyClient(api_key="msy_test_key", transport=transport)

            result = client.download_asset(
                {"url": "https://assets.meshy.ai/task/model.glb", "output_path": str(output_path)}
            )

            self.assertEqual(output_path.read_bytes(), b"glb-bytes")
            self.assertTrue(Path(result["path"]).samefile(output_path))
            with self.assertRaises(self.module.MeshyError):
                client.download_asset(
                    {"url": "https://assets.meshy.ai/task/model.glb", "output_path": str(output_path)}
                )

    def test_dispatch_check_auth_calls_argless_client_method(self):
        with TemporaryDirectory() as temp_dir:
            credential_path = Path(temp_dir) / "credentials.json"
            credential_path.write_text(json.dumps({"api_key": "msy_test_key"}))
            os.environ["MESHY_CREDENTIALS_PATH"] = str(credential_path)

            class FakeClient:
                def check_auth(self):
                    return {"ok": True, "balance": 123}

            original_client_from_config = self.module.client_from_config
            self.module.client_from_config = lambda: FakeClient()
            try:
                result = self.module.dispatch_tool("meshy_check_auth", {})
            finally:
                self.module.client_from_config = original_client_from_config

            self.assertNotIn("isError", result)
            self.assertIn('"ok": true', result["content"][0]["text"])


if __name__ == "__main__":
    unittest.main()
