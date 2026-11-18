import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "mcp"))
import server as S  # noqa: E402

PY = sys.executable


class TestMcp(unittest.TestCase):
    def test_registry_has_kb_init_no_sci(self):
        self.assertIn("kb_init", S.TOOL_BY_NAME)
        self.assertFalse(any("sci" in t["name"] for t in S.TOOLS))

    def test_kb_init_argv_uses_plugin_script(self):
        tool = S.TOOL_BY_NAME["kb_init"]
        argv, write_mode = S.build_argv(None, tool, {"target": "X:/some/vault", "apply": True})
        self.assertTrue(argv[1].replace("\\", "/").endswith("scripts/kb_init.py"))
        self.assertIn("--target", argv)
        self.assertIn("X:/some/vault", argv)
        self.assertTrue(write_mode)

    def test_write_gate_double_key(self):
        r = S.run_tool(None, "kb_init", {"target": "x", "apply": True}, allow_write=False)
        self.assertFalse(r["ok"])
        self.assertIn("allow-write", r["error"])
        r2 = S.run_tool(None, "kb_init", {"target": "x"}, allow_write=True)
        self.assertFalse(r2["ok"])
        self.assertIn("apply", r2["error"])

    def test_relative_target_rejected(self):
        # 相对 target 必须被守卫拒绝，且不触发任何 subprocess（不真实建库）。
        with mock.patch.object(S.subprocess, "run") as m:
            r = S.run_tool(None, "kb_init",
                           {"target": "relative/vault", "apply": True}, allow_write=True)
        self.assertFalse(r["ok"])
        self.assertIn("绝对路径", r["error"])
        m.assert_not_called()

    def test_absolute_target_passes_guard(self):
        # 绝对 target 不被守卫拦截：mock subprocess 避免真实建库。
        abs_target = os.path.join(tempfile.gettempdir(), "kb-guard-test-vault")
        fake = subprocess.CompletedProcess(args=[], returncode=0, stdout="{}", stderr="")
        with mock.patch.object(S.subprocess, "run", return_value=fake) as m:
            r = S.run_tool(None, "kb_init",
                           {"target": abs_target, "apply": True}, allow_write=True)
        self.assertTrue(r["ok"])
        m.assert_called_once()
        argv = m.call_args.args[0]
        self.assertIn("--target", argv)
        self.assertIn(abs_target, argv)

    def test_vault_tool_rejected_when_vault_none(self):
        r = S.run_tool(None, "kb_stats", {}, allow_write=False)
        self.assertFalse(r["ok"])
        self.assertIn("vault", r["error"])

    def test_list_tools_cli(self):
        r = subprocess.run([PY, str(ROOT / "mcp" / "server.py"), "--list-tools"],
                           capture_output=True, text=True, encoding="utf-8",
                           env=dict(os.environ, PYTHONIOENCODING="utf-8"))
        self.assertEqual(r.returncode, 0)
        self.assertIn("kb_init", r.stdout)


if __name__ == "__main__":
    unittest.main()
