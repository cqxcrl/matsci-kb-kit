import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "build"))
import build_plugin as BP  # noqa: E402


class TestBuild(unittest.TestCase):
    def test_banner_after_shebang(self):
        out = BP.add_banner("#!/usr/bin/env python\nprint(1)\n")
        lines = out.splitlines()
        self.assertTrue(lines[0].startswith("#!"))
        self.assertIn("GENERATED", lines[1])

    def test_skills_list_nine_no_sci(self):
        self.assertEqual(len(BP.SKILLS), 9)
        self.assertIn("kb-ingest-batch", BP.SKILLS)
        self.assertIn("kb-qc-loop", BP.SKILLS)
        self.assertIn("kb-review-cycle", BP.SKILLS)
        self.assertFalse(any("sci" in s for s in BP.SKILLS))

    def test_generate_tools_whitelist_filter(self):
        with tempfile.TemporaryDirectory() as td:
            src, out = pathlib.Path(td) / "src", pathlib.Path(td) / "out"
            (src / "tools").mkdir(parents=True)
            (src / "tools" / "kb_x.py").write_text("x = 1\n", encoding="utf-8")
            (src / "tools" / "sci_x.py").write_text("x = 1\n", encoding="utf-8")
            # load_lines 的 where 默认参数在定义时绑定，patch RULES 无效，直接 patch 函数
            with mock.patch.object(BP, "load_lines", return_value=["kb_x.py"]):
                n = BP.generate_tools(str(src), str(out), {}, [], {}, [], lambda m: None)
            self.assertEqual(n, 1)
            self.assertTrue((out / "tools" / "kb_x.py").is_file())
            self.assertFalse((out / "tools" / "sci_x.py").exists())

    def test_generate_tools_removes_stale_generated_files(self):
        """Task 6：include 白名单是 tools/ 的唯一真源——被审计排除的旧生成物
        必须从输出目录清掉，否则空库审计/随包清单会带上已排除的工具。"""
        with tempfile.TemporaryDirectory() as td:
            src, out = pathlib.Path(td) / "src", pathlib.Path(td) / "out"
            (src / "tools").mkdir(parents=True)
            (src / "tools" / "kb_x.py").write_text("x = 1\n", encoding="utf-8")
            (out / "tools").mkdir(parents=True)
            (out / "tools" / "stale_old.py").write_text("# stale\n", encoding="utf-8")
            (out / "tools" / "keep.yaml").write_text("k: v\n", encoding="utf-8")
            # lit_config.yaml 是用户配置（刻意不在白名单）：任何情况下都不清、不改
            (out / "tools" / "lit_config.yaml").write_text(
                "user: config\n", encoding="utf-8")
            with mock.patch.object(BP, "load_lines",
                                   return_value=["kb_x.py", "keep.yaml"]):
                BP.generate_tools(str(src), str(out), {}, [], {}, [], lambda m: None)
            self.assertFalse((out / "tools" / "stale_old.py").exists())
            self.assertTrue((out / "tools" / "kb_x.py").is_file())
            self.assertTrue((out / "tools" / "keep.yaml").is_file())
            self.assertTrue((out / "tools" / "lit_config.yaml").is_file())
            self.assertEqual((out / "tools" / "lit_config.yaml").read_text(
                encoding="utf-8"), "user: config\n")

    def test_source_dirty_detects_uncommitted(self):
        with tempfile.TemporaryDirectory() as td:
            subprocess.run(["git", "init", "-q", td], check=True)
            subprocess.run(["git", "-C", td, "config", "user.email", "t@example.org"], check=True)
            subprocess.run(["git", "-C", td, "config", "user.name", "t"], check=True)
            os.makedirs(os.path.join(td, "tools"))
            p = os.path.join(td, "tools", "a.py")
            with open(p, "w") as f:
                f.write("a = 1\n")
            subprocess.run(["git", "-C", td, "add", "."], check=True)
            subprocess.run(["git", "-C", td, "commit", "-qm", "init"], check=True)
            self.assertEqual(BP.source_dirty(td), [])
            with open(p, "a") as f:
                f.write("a = 2\n")
            self.assertEqual(BP.source_dirty(td), ["tools/a.py"])

    def test_scan_targets_exclude_internal_docs(self):
        self.assertFalse(any("superpowers" in t for t in BP.SCAN_TARGETS))
        self.assertIn("scaffold", BP.SCAN_TARGETS)

    def test_tools_rules_rename_before_drop_lines(self):
        """finding 5：TOOLS.md 的 find/replace 改名先于 drop_lines 生效，
        含库名的 H1 被改名而不是被当噪声整行删掉；未命中要告警。"""
        with tempfile.TemporaryDirectory() as td:
            src, out = pathlib.Path(td) / "src", pathlib.Path(td) / "out"
            (src / "tools").mkdir(parents=True)
            (src / "tools" / "_README.md").write_text(
                "# OldName 工具链\n\n> 本库原名「OldName」，某年更名。\n\n"
                "## 主工具链 (tools/)\n\n正文。\n", encoding="utf-8")
            drops = {
                "tools_rules": [{"find": "# OldName 工具链",
                                 "replace": "# 工具索引"}],
                "drop_lines": [{"pattern": r"^.*(?:OldName|原名).*$"}],
            }
            warn = []
            BP.generate_carriers(str(src), str(out), [], {}, [], drops,
                                 warn, lambda m: None)
            t = (out / "docs" / "TOOLS.md").read_text(encoding="utf-8")
            self.assertTrue(t.startswith("# 工具索引"), t[:40])
            self.assertNotIn("原名", t)          # 更名史噪声行仍被 drop_lines 删掉
            self.assertIn("## 主工具链", t)
            self.assertFalse(any("TOOLS.md 变换未命中" in w for w in warn))
            # 未命中的 tools_rules find 必须告警（漂移可见）
            warn2 = []
            drops2 = {"tools_rules": [{"find": "# 不存在的标题",
                                       "replace": "# x"}]}
            BP.generate_carriers(str(src), str(out), [], {}, [], drops2,
                                 warn2, lambda m: None)
            self.assertTrue(any("TOOLS.md 变换未命中" in w for w in warn2))


class TestOverlay(unittest.TestCase):
    """Task 6 遗留项 E：overlay 机制——skills 生成后，把 build/overlay/skills/<name>/
    下的公开泛化补件复制进 skills/<name>/（同名覆盖）。全部用 fake-src/tmp，不触活库。"""

    def _fake_src(self, td):
        src = pathlib.Path(td) / "src"
        for name in BP.SKILLS:
            sk = src / ".dsh" / "skills" / name
            sk.mkdir(parents=True)
            (sk / "SKILL.md").write_text("# generated skill\n", encoding="utf-8")
        return src

    def test_overlay_copies_new_files_and_overrides_generated(self):
        with tempfile.TemporaryDirectory() as td:
            src = self._fake_src(td)
            out = pathlib.Path(td) / "out"
            overlay = pathlib.Path(td) / "overlay"
            refs = overlay / "skills" / "kb-qc-loop" / "references"
            refs.mkdir(parents=True)
            (refs / "protocol.md").write_text("protocol skeleton\n", encoding="utf-8")
            (overlay / "skills" / "kb-qc-loop" / "SKILL.md").write_text(
                "# overridden\n", encoding="utf-8")
            with mock.patch.object(BP, "OVERLAY", str(overlay)):
                BP.generate_carriers(str(src), str(out), [], {}, [], {},
                                     [], lambda m: None)
                BP.apply_overlays(str(out), [], lambda m: None)
            self.assertEqual(
                (out / "skills" / "kb-qc-loop" / "references" / "protocol.md")
                .read_text(encoding="utf-8"), "protocol skeleton\n")
            self.assertEqual(
                (out / "skills" / "kb-qc-loop" / "SKILL.md")
                .read_text(encoding="utf-8"), "# overridden\n")

    def test_overlay_unknown_skill_warns_and_skips(self):
        with tempfile.TemporaryDirectory() as td:
            src = self._fake_src(td)
            out = pathlib.Path(td) / "out"
            overlay = pathlib.Path(td) / "overlay"
            unknown = overlay / "skills" / "not-a-shipped-skill"
            unknown.mkdir(parents=True)
            (unknown / "x.md").write_text("x\n", encoding="utf-8")
            warn = []
            with mock.patch.object(BP, "OVERLAY", str(overlay)):
                BP.generate_carriers(str(src), str(out), [], {}, [], {},
                                     warn, lambda m: None)
                BP.apply_overlays(str(out), warn, lambda m: None)
            self.assertTrue(any("overlay" in w and "not-a-shipped-skill" in w
                                for w in warn), warn)
            self.assertFalse((out / "skills" / "not-a-shipped-skill").exists())

    def test_overlay_absent_is_noop(self):
        with tempfile.TemporaryDirectory() as td:
            src = self._fake_src(td)
            out = pathlib.Path(td) / "out"
            warn = []
            with mock.patch.object(BP, "OVERLAY",
                                   str(pathlib.Path(td) / "no-such-overlay")):
                BP.generate_carriers(str(src), str(out), [], {}, [], {},
                                     warn, lambda m: None)
                BP.apply_overlays(str(out), warn, lambda m: None)
            self.assertTrue((out / "skills" / "kb-qc-loop" / "SKILL.md").is_file())
            self.assertFalse(warn)


class TestDirtyGateFailClosed(unittest.TestCase):
    """finding 1：不可验证 = 拒绝构建。git 失败/缺失/超时必须抛 RuntimeError，
    main 捕获后 exit 2，绝不静默放行。全部用 fake-src/tmp 目录，不触活库。"""

    def test_source_dirty_non_git_dir_raises(self):
        with tempfile.TemporaryDirectory() as td:
            # 阻断 git 向上遍历祖先目录，确保 td 被判定为非 git 仓库（exit 128）
            ceiling = str(pathlib.Path(td).parent)
            with mock.patch.dict(os.environ, {"GIT_CEILING_DIRECTORIES": ceiling}):
                with self.assertRaises(RuntimeError):
                    BP.source_dirty(td)

    def test_source_dirty_git_nonzero_exit_raises(self):
        fake = subprocess.CompletedProcess(args=["git"], returncode=128,
                                           stdout="", stderr="fatal: not a git repo")
        with mock.patch("subprocess.run", return_value=fake):
            with self.assertRaises(RuntimeError):
                BP.source_dirty("whatever")

    def test_source_dirty_git_missing_raises(self):
        with mock.patch("subprocess.run", side_effect=FileNotFoundError("git")):
            with self.assertRaises(RuntimeError):
                BP.source_dirty("whatever")

    def test_source_dirty_git_timeout_raises(self):
        with mock.patch("subprocess.run",
                        side_effect=subprocess.TimeoutExpired(cmd="git", timeout=20)):
            with self.assertRaises(RuntimeError):
                BP.source_dirty("whatever")

    def test_main_rejects_unverifiable_src_exit_2(self):
        with tempfile.TemporaryDirectory() as td:
            src, out = pathlib.Path(td) / "src", pathlib.Path(td) / "out"
            (src / "tools").mkdir(parents=True)
            (src / "tools" / "kb_lib.py").write_text("x = 1\n", encoding="utf-8")
            argv = ["build_plugin.py", "--src", str(src), "--out", str(out)]
            with mock.patch.object(sys, "argv", argv), \
                 mock.patch.object(BP, "private_paths", return_value=[]), \
                 mock.patch.object(BP, "source_dirty",
                                   side_effect=RuntimeError("git 不可用")):
                rc = BP.main()
            self.assertEqual(rc, 2)
            self.assertFalse((out / "plugin.yaml").exists())


class TestBasesAndPluginYaml(unittest.TestCase):
    """控制器要求的补充覆盖：optional 路由 + plugin.yaml 溯源字段与措辞。"""

    def test_generate_bases_optional_routing(self):
        with tempfile.TemporaryDirectory() as td:
            src, out = pathlib.Path(td) / "src", pathlib.Path(td) / "out"
            src.mkdir()
            (src / "公众号文集.base").write_text("views: []\n", encoding="utf-8")
            (src / "文献总览.base").write_text("views: []\n", encoding="utf-8")
            (src / "not_a_base.txt").write_text("x\n", encoding="utf-8")
            n = BP.generate_bases(str(src), str(out), [], [], {}, [], lambda m: None)
            self.assertEqual(n, 2)
            self.assertTrue((out / "scaffold" / "bases" / "optional"
                             / "公众号文集.base").is_file())
            self.assertTrue((out / "scaffold" / "bases" / "文献总览.base").is_file())
            self.assertFalse((out / "scaffold" / "bases" / "optional"
                              / "文献总览.base").exists())
            self.assertFalse((out / "scaffold" / "bases" / "not_a_base.txt").exists())

    def test_write_plugin_yaml_fields_and_note(self):
        import hashlib
        import yaml
        with tempfile.TemporaryDirectory() as td:
            src, out = pathlib.Path(td) / "src", pathlib.Path(td) / "out"
            src.mkdir()
            subprocess.run(["git", "init", "-q", str(src)], check=True)
            subprocess.run(["git", "-C", str(src), "config", "user.email",
                            "t@example.org"], check=True)
            subprocess.run(["git", "-C", str(src), "config", "user.name", "t"],
                           check=True)
            (src / "a.txt").write_text("a\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(src), "add", "."], check=True)
            subprocess.run(["git", "-C", str(src), "commit", "-qm", "init"],
                           check=True)
            (out / "tools").mkdir(parents=True)
            tool = out / "tools" / "kb_x.py"
            tool.write_text("x = 1\n", encoding="utf-8")
            commit = BP.write_plugin_yaml(str(out), str(src))
            self.assertNotEqual(commit, "unknown")
            yml = out / "plugin.yaml"
            self.assertTrue(yml.is_file())
            self.assertFalse((out / "kit.yaml").exists())
            doc = yaml.safe_load(yml.read_text(encoding="utf-8"))
            self.assertEqual(doc["_generated_by"], "build/build_plugin.py")
            self.assertIn("source_commit", doc)
            self.assertEqual(doc["source_commit"], commit)
            self.assertIn("tools/kb_x.py", doc["tool_sha256"])
            self.assertEqual(doc["tool_sha256"]["tools/kb_x.py"],
                             hashlib.sha256(tool.read_bytes()).hexdigest())
            # finding 2：导出物不得残留 "kit" 自称
            self.assertIn("本插件", doc["_note"])
            self.assertNotIn("kit", doc["_note"])


class TestCompatScrub(unittest.TestCase):
    """PEP 701：f-string 表达式内反斜杠仅 py≥3.12 合法；插件声明 ≥3.10、
    CI 跑 3.11。公开 compat 规则层在构建期把病灶转 .format（不动活库、
    不手改生成物）。ast.parse(feature_version=(3,10)) 测不出该词法差异，
    故用字面量钉住 + 真 CI 兜底。"""

    LESION_SELFTEST = r'''        print(f"  [{'ok' if good else 'FAIL'}] write_text_keep_eol 保住 CRLF"
              f"（crlf={_raw.count(b'\r\n')} bare={_raw.count(b'\n') - _raw.count(b'\r\n')}）")'''
    LESION_LIT_SI = r'''                    ev.append(f"p{i} [{tag}]: {re.sub(r'\s+', ' ', t[s:e]).strip()[:170]}")'''
    LESION_ZBASE = '''        # 反例：全部基目录都不可用 ⇒ 必须抛 OSError（不能静默返回坏目录）
        try:
            K.make_temp_dir(bases=[os.path.join("Z:", "nope_zzz"),
                                   os.path.join("Z:", "nope_yyy")])
            raised = False
        except OSError:
            raised = True'''

    def test_compat_rules_target_both_lesions(self):
        compat = BP.load_compat()
        self.assertIn("kb_selftest.py", compat)
        self.assertIn("lit_si.py", compat)
        for name, lesion in (("kb_selftest.py", self.LESION_SELFTEST),
                             ("kb_selftest.py", self.LESION_ZBASE),
                             ("lit_si.py", self.LESION_LIT_SI)):
            self.assertTrue(any(f == lesion for f, _ in compat[name]),
                            f"compat 规则的 find 必须与病灶原文逐字一致：{name}")

    def test_generate_tools_applies_compat(self):
        with tempfile.TemporaryDirectory() as td:
            src, out = pathlib.Path(td) / "src", pathlib.Path(td) / "out"
            (src / "tools").mkdir(parents=True)
            (src / "tools" / "kb_selftest.py").write_text(
                self.LESION_SELFTEST + "\n" + self.LESION_ZBASE + "\n",
                encoding="utf-8", newline="\n")
            (src / "tools" / "lit_si.py").write_text(
                self.LESION_LIT_SI + "\n", encoding="utf-8", newline="\n")
            warn = []
            with mock.patch.object(BP, "load_lines",
                                   return_value=["kb_selftest.py", "lit_si.py"]):
                n = BP.generate_tools(str(src), str(out), {}, [], {}, warn,
                                      lambda m: None)
            self.assertEqual(n, 2)
            self.assertEqual(warn, [])
            t1 = (out / "tools" / "kb_selftest.py").read_text(encoding="utf-8")
            t2 = (out / "tools" / "lit_si.py").read_text(encoding="utf-8")
            self.assertNotIn("f\"（crlf=", t1)
            self.assertIn("保住 CRLF（crlf={} bare={}）\".format(", t1)
            self.assertNotIn("f\"p{i} [{tag}]", t2)
            self.assertIn("\"p{} [{}]: {}\".format(", t2)
            self.assertNotIn("os.path.join(\"Z:\", \"nope_zzz\")", t1)
            self.assertIn("kb_selftest_basefile_zzz", t1)

    def test_file_base_raises_on_this_os(self):
        """Z: 盘符反例的跨平台替代语义守卫：基目录是**文件**时 make_temp_dir
        必须抛 OSError。Windows 与 Linux 上都成立（CI 也跑这条）。"""
        sys.path.insert(0, str(ROOT / "tools"))
        import kb_lib as K
        with tempfile.TemporaryDirectory() as td:
            fb = os.path.join(td, "base_is_a_file")
            with open(fb, "w", encoding="utf-8") as f:
                f.write("x")
            with self.assertRaises(OSError):
                K.make_temp_dir(bases=[fb, fb])

    def test_shipped_tools_free_of_pep701_lesions(self):
        t1 = (ROOT / "tools" / "kb_selftest.py").read_text(encoding="utf-8")
        t2 = (ROOT / "tools" / "lit_si.py").read_text(encoding="utf-8")
        self.assertNotIn("f\"（crlf=", t1)
        self.assertNotIn("f\"p{i} [{tag}]", t2)
        self.assertIn("保住 CRLF（crlf={} bare={}）\".format(", t1)
        self.assertIn("\"p{} [{}]: {}\".format(", t2)
        self.assertNotIn("os.path.join(\"Z:\", \"nope_zzz\")", t1)
        self.assertIn("kb_selftest_basefile_zzz", t1)

    @unittest.skipUnless(sys.version_info >= (3, 12),
                         "FSTRING_* tokens require py3.12+; CI 3.11 由 py_compile 兜底")
    def test_no_pep701_expression_backslashes_anywhere(self):
        """通用守卫：f-string 表达式内（FSTRING_START/END 区间里的 STRING token）
        出现反斜杠仅 py≥3.12 合法。字面文本部分的反斜杠（FSTRING_MIDDLE）全版本
        合法，不算病灶。"""
        import io
        import tokenize
        bad = []
        for sub in ("tools", "scripts", "mcp", "build"):
            for p in sorted((ROOT / sub).rglob("*.py")):
                if "__pycache__" in p.parts:
                    continue
                depth = 0
                readline = io.StringIO(p.read_text(encoding="utf-8")).readline
                for t in tokenize.generate_tokens(readline):
                    if t.type == tokenize.FSTRING_START:
                        depth += 1
                    elif t.type == tokenize.FSTRING_END:
                        depth -= 1
                    elif depth > 0 and t.type == tokenize.STRING and "\\" in t.string:
                        bad.append(f"{p.relative_to(ROOT)}:{t.start[0]} {t.string[:40]}")
        self.assertEqual(bad, [])


if __name__ == "__main__":
    unittest.main()