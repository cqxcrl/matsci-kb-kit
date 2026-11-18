import contextlib
import importlib.util
import io
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
INIT = ROOT / "scripts" / "kb_init.py"
PY = sys.executable
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")


def run_init(*args, timeout=300):
    return subprocess.run([PY, str(INIT), *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=ENV, timeout=timeout)


def load_kb_init():
    """以模块方式加载 kb_init.py，便于 mock 内部调用（main/update_tools）。"""
    spec = importlib.util.spec_from_file_location("kb_init_under_test", INIT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestKbInit(unittest.TestCase):
    def test_default_mode_no_obsidian(self):
        with tempfile.TemporaryDirectory() as td:
            r = run_init("--target", td)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertFalse((pathlib.Path(td) / ".obsidian").exists())
            self.assertEqual(list(pathlib.Path(td).rglob("*.base")), [])
            self.assertTrue((pathlib.Path(td) / "tools" / "kb_lib.py").is_file())
            self.assertTrue((pathlib.Path(td) / "CLAUDE.md").is_file())
            self.assertTrue((pathlib.Path(td) / ".gitattributes").is_file())
            self.assertFalse((pathlib.Path(td) / ".dsh").exists())
            self.assertFalse((pathlib.Path(td) / ".claude").exists())

    def test_with_obsidian_layer(self):
        with tempfile.TemporaryDirectory() as td:
            r = run_init("--target", td, "--with-obsidian")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertTrue((pathlib.Path(td) / ".obsidian" / "app.json").is_file())
            self.assertGreaterEqual(len(list(pathlib.Path(td).rglob("*.base"))), 4)

    def test_idempotent_rerun(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(run_init("--target", td).returncode, 0)
            r2 = run_init("--target", td)
            self.assertEqual(r2.returncode, 0)
            self.assertIn("跳过", r2.stdout)

    def test_update_tools_preserves_data(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(run_init("--target", td).returncode, 0)
            sentinel = pathlib.Path(td) / "wiki" / "concepts" / "sentinel.md"
            sentinel.write_text("# sentinel\n", encoding="utf-8")
            tool = pathlib.Path(td) / "tools" / "kb_where.py"
            tool.write_text("# tampered\n", encoding="utf-8")
            cfg = pathlib.Path(td) / "tools" / "lit_config.yaml"
            custom_cfg = "# onboard 成果，绝不可被模板覆盖\nresearch_field: keep-me\n"
            cfg.write_text(custom_cfg, encoding="utf-8")
            r = run_init("--target", td, "--update-tools")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertTrue(sentinel.is_file())
            self.assertNotIn("tampered", tool.read_text(encoding="utf-8"))
            self.assertEqual(cfg.read_text(encoding="utf-8"), custom_cfg)
            backups = list((pathlib.Path(td) / "_archive").glob("tools-backup-*"))
            self.assertEqual(len(backups), 1)

    def test_index_failure_propagates_exit_code(self):
        mod = load_kb_init()
        with tempfile.TemporaryDirectory() as td:
            fake = subprocess.CompletedProcess(args=[], returncode=3)
            with mock.patch.object(mod.sys, "argv", ["kb_init.py", "--target", td]), \
                 mock.patch.object(mod.subprocess, "run", return_value=fake) as m, \
                 contextlib.redirect_stdout(io.StringIO()):
                rc = mod.main()
            m.assert_called_once()  # 仅索引步骤调用 subprocess.run
            self.assertNotEqual(rc, 0)
            self.assertEqual(rc, 3)

    def test_update_tools_same_second_backup_suffix(self):
        mod = load_kb_init()
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(run_init("--target", td, "--no-index").returncode, 0)
            with mock.patch.object(mod.time, "strftime",
                                   return_value="20260101-000000"), \
                 contextlib.redirect_stdout(io.StringIO()):
                rc1 = mod.update_tools(td, lambda msg: None)
                rc2 = mod.update_tools(td, lambda msg: None)
            self.assertEqual(rc1, 0)
            self.assertEqual(rc2, 0)
            backups = sorted(p.name for p in
                             (pathlib.Path(td) / "_archive").glob("tools-backup-*"))
            self.assertEqual(backups, ["tools-backup-20260101-000000",
                                       "tools-backup-20260101-000000-2"])

    def test_check_deps(self):
        r = run_init("--target", tempfile.gettempdir(), "--check-deps")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_archive_readme_materialized_and_idempotent(self):
        """Task 6 遗留项 G：_archive/README.md 登记册骨架随建库物化，
        表头含 日期/对象/原因/落点；已存在的用户登记册绝不覆盖。"""
        with tempfile.TemporaryDirectory() as td:
            r = run_init("--target", td, "--no-index")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            reg = pathlib.Path(td) / "_archive" / "README.md"
            self.assertTrue(reg.is_file())
            text = reg.read_text(encoding="utf-8")
            for header in ("日期", "对象", "原因", "落点"):
                self.assertIn(header, text)
            reg.write_text("# my register\n", encoding="utf-8")
            r2 = run_init("--target", td, "--no-index")
            self.assertEqual(r2.returncode, 0, r2.stdout + r2.stderr)
            self.assertEqual(reg.read_text(encoding="utf-8"), "# my register\n")


if __name__ == "__main__":
    unittest.main()
