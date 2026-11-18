import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class TestMcpJson(unittest.TestCase):
    def test_mcp_json_points_to_existing_server(self):
        data = json.loads((ROOT / ".mcp.json").read_text(encoding="utf-8"))
        srv = data["mcpServers"]["matsci-kb"]
        self.assertEqual(srv["command"], "python")
        arg = srv["args"][0]
        # 提交默认 = Qoder 变体（Task 8 裁决）；Claude Code 手动换用见 docs/MCP.md
        self.assertIn("${QODER_PLUGIN_ROOT}", arg)
        self.assertIn("mcp/server.py", arg.replace("\\", "/"))
        self.assertEqual(srv["timeout"], 120000)
        rel = arg.split("}", 1)[1].lstrip("/")
        self.assertTrue((ROOT / rel).is_file())

    def test_marketplace_json(self):
        data = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
        self.assertEqual(data["name"], "matsci-local")
        self.assertEqual(data["plugins"][0]["name"], "matsci-knowledge-base")
        self.assertEqual(data["plugins"][0]["source"], "./")


if __name__ == "__main__":
    unittest.main()
