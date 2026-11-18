import contextlib
import io
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
PY = sys.executable

sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "build"))
import build_plugin as BP  # noqa: E402
import export_plugin as EP  # noqa: E402


class TestExportDist(unittest.TestCase):
    @unittest.skipUnless(
        os.path.isfile(os.path.join(BP.PRIVATE, "leak_denylist.txt")),
        "private rules absent (clean checkout / CI)")
    def test_export_clean(self):
        r = subprocess.run([PY, str(ROOT / "scripts" / "export_plugin.py")],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        dist = ROOT / "dist" / f"matsci-knowledge-base-{EP.VERSION}"
        self.assertTrue((dist / ".qoder-plugin" / "plugin.json").is_file())
        self.assertTrue((dist / "tools" / "kb_lib.py").is_file())
        for banned in ("build", "tests", ".git", "dist"):
            self.assertFalse((dist / banned).exists(), banned)
        self.assertFalse((dist / "docs" / "superpowers").exists())
        self.assertIn("泄漏扫描：0 命中", r.stdout)


class TestFinalAuditGate(unittest.TestCase):
    """Task 11 fix 轮：终审门禁不得在私有规则缺失时静默降级。"""

    def test_private_denylist_missing_aborts_rc2(self):
        """finding 1：私有 denylist 缺失 → rc=2 明确中止，绝不打印「0 命中」。

        不真删本机 private：patch BP.PRIVATE 指向空目录（内存级 mock）。
        """
        with tempfile.TemporaryDirectory() as empty:
            buf = io.StringIO()
            with mock.patch.object(BP, "PRIVATE", empty), \
                    mock.patch.object(BP, "scan_leaks") as sl, \
                    contextlib.redirect_stdout(buf):
                rc = EP.main()
        out = buf.getvalue()
        self.assertEqual(rc, 2, out)
        self.assertNotIn("0 命中", out)
        self.assertIn("ABORT", out)
        self.assertIn("leak_denylist.txt", out)
        sl.assert_not_called()  # 不允许降级为仅公开规则扫描

    def test_license_in_scan_targets_and_actually_scanned(self):
        """finding 2：LICENSE 与 NOTICE/README 同列入 SCAN_TARGETS，且真被扫。"""
        self.assertIn("LICENSE", BP.SCAN_TARGETS)
        with tempfile.TemporaryDirectory() as tmp:
            # 公开规则①家目录形态（/home/<user>）——不含任何真实专名。
            with open(os.path.join(tmp, "LICENSE"), "w", encoding="utf-8") as f:
                f.write("see /home/someuser/notes for details\n")
            hits = BP.scan_leaks(tmp)
        self.assertTrue(any(h[0] == "LICENSE" for h in hits), hits)

    def test_scan_leaks_warns_on_unreadable_files(self):
        """finding 3：不可读文件跳过须计数告警；命中判定（fail-closed）不变。"""
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "tools"))
            with open(os.path.join(tmp, "tools", "x.md"), "w",
                      encoding="utf-8") as f:
                f.write("clean line\n")
            orig_read = BP._read

            def fake_read(path):
                if os.path.abspath(path).startswith(os.path.abspath(tmp)):
                    raise OSError("unreadable (test)")
                return orig_read(path)  # 规则文件仍可读

            buf = io.StringIO()
            with mock.patch.object(BP, "_read", side_effect=fake_read), \
                    contextlib.redirect_stdout(buf):
                hits = BP.scan_leaks(tmp)
        self.assertEqual(hits, [])
        self.assertIn("不可读", buf.getvalue())
        self.assertIn("1", buf.getvalue())

    def test_scan_leaks_ignores_bytecode_cache(self):
        """finding 3 附带：__pycache__/*.pyc 非文本，先验排除，
        不占用「不可读」告警（否则本机 verify 每轮虚报 74 个）。"""
        with tempfile.TemporaryDirectory() as tmp:
            cache = os.path.join(tmp, "tools", "__pycache__")
            os.makedirs(cache)
            with open(os.path.join(cache, "x.cpython-314.pyc"), "wb") as f:
                f.write(b"\x00\xff\xfe binary \x80")
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                hits = BP.scan_leaks(tmp)
        self.assertEqual(hits, [])
        self.assertNotIn("不可读", buf.getvalue())

    def test_export_script_trailing_newline(self):
        """finding 4：scripts/export_plugin.py 以换行结尾。"""
        b = (ROOT / "scripts" / "export_plugin.py").read_bytes()
        self.assertTrue(b.endswith(b"\n"))

    def test_final_fix_trailing_newlines(self):
        """终审 minor 4：tests/test_export_dist.py、LICENSE、.gitignore 以换行结尾。"""
        for rel in ("tests/test_export_dist.py", "LICENSE", ".gitignore"):
            b = (ROOT / rel).read_bytes()
            self.assertTrue(b.endswith(b"\n"), rel)


if __name__ == "__main__":
    unittest.main()
