"""Task 10 fix 轮：caj 豁免收窄的行为级测试（review finding 1）。

修复前：kb_toolcheck 按文件名 + rc=2 豁免 caj_to_pdf，但 rc=2 是其 selftest 的
通用失败码——环境无关子项（数据安全回归等）失败或装齐环境仍失败都被静默放行。
修复后（规则层）：
  · caj selftest 仅当全部失败子项均为可选环境判据时返回专用码 3，其余失败仍 2；
  · kb_toolcheck 只豁免 caj_to_pdf 的 rc=3（SKIP），rc=2 恢复 FAIL。

本文件钉住行为链：① 环境未就绪 → 专用码 3 → toolcheck SKIP；
② 非环境性失败（mock / 夹具构造 rc=2）→ toolcheck 仍 FAIL。
隐私纪律：夹具全合成，不含真实专名。
"""
import contextlib
import importlib.util
import io
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
PY = sys.executable
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
CAJ = ROOT / "tools" / "caj_to_pdf.py"
INIT = ROOT / "scripts" / "kb_init.py"

sys.path.insert(0, str(ROOT / "tools"))
import kb_toolcheck as T  # noqa: E402


def run(argv, cwd=None, timeout=300):
    return subprocess.run(argv, cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=ENV, timeout=timeout)


def load_caj_module():
    spec = importlib.util.spec_from_file_location("caj_under_test", CAJ)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_fixture(dirpath, name, rc, body):
    """合成工具夹具：argparse + --selftest，按指定退出码退出。"""
    p = pathlib.Path(dirpath) / name
    p.write_text(
        "import argparse\n"
        "ap = argparse.ArgumentParser(description='synthetic fixture')\n"
        "ap.add_argument('--selftest', action='store_true')\n"
        "a = ap.parse_args()\n"
        "if a.selftest:\n"
        + body +
        f"    raise SystemExit({rc})\n",
        encoding="utf-8")
    return p


# 环境未就绪形态：[skip] + 专用码 3 的末行归因
BODY_ENV_NOT_READY = (
    "    print('  [skip] 真实转换器未就绪，跳过 cajparser shim 自检。')\n"
    "    print('=== 退出码 3：仅可选环境未就绪（无环境无关失败），按可选层豁免 ===')\n"
)
# 非环境性失败形态：即使带 [skip] 字样，数据安全回归 FAIL → 通用失败码 2
BODY_NON_ENV_FAIL = (
    "    print('  [skip] 真实转换器未就绪，跳过 cajparser shim 自检。')\n"
    "    print('  [FAIL] 上游中途失败时目的地不留文件')\n"
)


class TestCajSelftestExitCodes(unittest.TestCase):
    def test_env_not_ready_returns_dedicated_code(self):
        """① 环境未就绪态 → 专用码 3（不再是 2）；装齐环境全过 → 0。"""
        av = json.loads(run([PY, str(CAJ), "--available", "--json"]).stdout)
        r = run([PY, str(CAJ), "--selftest"])
        out = r.stdout + r.stderr
        if av["ready"]:
            self.assertEqual(r.returncode, 0, out)
        else:
            self.assertEqual(r.returncode, 3, out)
            self.assertIn("[skip]", out)
            self.assertIn("退出码 3", out)
            fails = [ln for ln in out.splitlines() if "[FAIL]" in ln]
            self.assertTrue(fails, "环境未就绪态应有环境判据 FAIL")
            for ln in fails:
                self.assertTrue("能定位 caj2pdf 目录" in ln or "Python 依赖齐备" in ln,
                                f"出现非环境判据 FAIL 时不得返回专用码: {ln}")

    def test_non_env_failure_returns_2_even_if_env_not_ready(self):
        """② mock 破坏数据安全回归（convert_one 谎报成功）→ 环境无关失败 →
        无论环境就绪与否都必须返回 2，不得落入专用码豁免。"""
        mod = load_caj_module()
        cwd = os.getcwd()
        buf = io.StringIO()
        try:
            with mock.patch.object(mod, "convert_one",
                                   return_value={"ok": True, "reason": ""}), \
                 contextlib.redirect_stdout(buf):
                rc = mod.selftest()
        finally:
            os.chdir(cwd)
        self.assertEqual(rc, 2, buf.getvalue())
        self.assertIn("[FAIL]", buf.getvalue())


class TestToolcheckCajExemption(unittest.TestCase):
    def test_skip_only_for_caj_dedicated_code(self):
        """夹具直测 check_one：caj rc=3 → SKIP 不计失败；caj rc=2（即使带
        [skip] 字样）→ FAIL 计失败；其他工具 rc=3 → 不豁免（豁免按名绑定）。"""
        with tempfile.TemporaryDirectory() as td:
            p3 = write_fixture(td, "caj_to_pdf.py", 3, BODY_ENV_NOT_READY)
            rec = T.check_one("caj_to_pdf.py", str(p3), do_write_guard=False)
            self.assertEqual(rec["selftest"], "SKIP")
            self.assertFalse(T._record_failed(rec))
            self.assertTrue(any("环境未就绪" in n and "退出码 3" in n
                                for n in rec["notes"]), rec["notes"])

            p2 = write_fixture(td, "caj_to_pdf.py", 2, BODY_NON_ENV_FAIL)
            rec2 = T.check_one("caj_to_pdf.py", str(p2), do_write_guard=False)
            self.assertEqual(rec2["selftest"], "FAIL")
            self.assertTrue(T._record_failed(rec2))

            other = write_fixture(td, "kb_probe.py", 3, BODY_ENV_NOT_READY)
            rec3 = T.check_one("kb_probe.py", str(other), do_write_guard=False)
            self.assertEqual(rec3["selftest"], "FAIL")
            self.assertTrue(T._record_failed(rec3))

    def test_empty_vault_toolcheck_skips_real_caj(self):
        """① 全链端到端：kb_init 空库（真实生成物）里跑 toolcheck——
        环境未就绪 → 真实 caj selftest 专用码 → SKIP 且退出 0、归因正确；
        装齐环境 → PASS 且退出 0。"""
        with tempfile.TemporaryDirectory() as td:
            r0 = run([PY, str(INIT), "--target", td, "--no-index"])
            self.assertEqual(r0.returncode, 0, r0.stdout + r0.stderr)
            vault = pathlib.Path(td)
            caj = vault / "tools" / "caj_to_pdf.py"
            tc = vault / "tools" / "kb_toolcheck.py"
            av = json.loads(run([PY, str(caj), "--available", "--json"], cwd=td).stdout)
            r = run([PY, str(tc), "--tools", "caj_to_pdf.py", "--json"], cwd=td)
            rows = json.loads(r.stdout)
            self.assertEqual(len(rows), 1, r.stdout + r.stderr)
            row = rows[0]
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            if av["ready"]:
                self.assertEqual(row["selftest"], "PASS")
            else:
                self.assertEqual(row["selftest"], "SKIP")
                self.assertTrue(any("环境未就绪" in n and "退出码 3" in n
                                    for n in row["notes"]), row["notes"])


if __name__ == "__main__":
    unittest.main()
