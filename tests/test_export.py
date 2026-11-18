import pathlib
import unittest

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _include_entries():
    lines = (ROOT / "build" / "rules" / "include.txt").read_text(
        encoding="utf-8").splitlines()
    return [ln.strip() for ln in lines
            if ln.strip() and not ln.strip().startswith("#")]


class TestExport(unittest.TestCase):
    def test_plugin_yaml_exists_and_no_sci(self):
        doc = yaml.safe_load((ROOT / "plugin.yaml").read_text(encoding="utf-8"))
        self.assertEqual(doc["_generated_by"], "build/build_plugin.py")
        self.assertFalse(any("sci_" in t for t in doc["tools"]))
        self.assertFalse(any(t.endswith(".ps1") for t in doc["tools"]))
        self.assertGreaterEqual(len(doc["tools"]), 60)

    def test_nine_skills_exported(self):
        skills = sorted(p.name for p in (ROOT / "skills").iterdir() if p.is_dir())
        self.assertEqual(len(skills), 9)
        self.assertNotIn("sci-assistant", skills)

    def test_claude_md_in_scaffold(self):
        self.assertTrue((ROOT / "scaffold" / "CLAUDE.md").is_file())

    def test_bases_exported(self):
        bases = list((ROOT / "scaffold" / "bases").rglob("*.base"))
        self.assertEqual(len(bases), 5)

    # ---- 控制器裁决 1：额外验收断言 ----
    def test_include_no_sci_entries(self):
        self.assertFalse(any("sci_" in e for e in _include_entries()))

    def test_include_has_three_qc_tools(self):
        entries = _include_entries()
        for name in ("qc_evidence_base.py", "qc_schema_check.py",
                     "qc_base_check.py"):
            self.assertIn(name, entries)

    def test_generated_tools_no_sci_no_ps1(self):
        names = [p.name for p in (ROOT / "tools").iterdir() if p.is_file()]
        self.assertFalse(any("sci_" in n for n in names),
                         f"sci_* leaked into tools/: "
                         f"{[n for n in names if 'sci_' in n]}")
        self.assertFalse(any(n.endswith(".ps1") for n in names))

    # ---- task-3 fix 轮（review findings 2/3/4/5）回归断言 ----
    def test_lit_digest_default_results_dir_derived(self):
        """finding 2：未配置时经 kb_lib.lit_runs_dir 派生库内目录，不再是空串。"""
        t = (ROOT / "tools" / "lit_digest.py").read_text(encoding="utf-8")
        self.assertIn('or K.lit_runs_dir(cfg, "results"))', t)
        self.assertIn("缺省落在库内运行产物目录", t)
        d = (ROOT / "tools" / "lit_daily.py").read_text(encoding="utf-8")
        self.assertIn('or K.lit_runs_dir(cfg, "results"),', d)

    def test_skills_no_dsh_truth_source_pointer(self):
        """finding 3：技能文本不得再宣称真源在库内 .dsh/ 或 junction 布局。"""
        for p in (ROOT / "skills").rglob("*.md"):
            t = p.read_text(encoding="utf-8")
            for bad in ("真源在库内", "改内容请改 `.dsh", "技能真源：`.dsh",
                        "真源已迁入库内", "本机正确布局"):
                self.assertNotIn(bad, t, f"{p}: {bad}")

    def test_skill_headers_plugin_layout(self):
        """Task 9 fix 轮 finding 1：技能在插件级注册，kb_init 不复制 skills 进 vault；
        库内无 .claude/skills/ 属正常（不得再宣称建库脚本复制副本）。"""
        for name in ("lit-watch", "lit-browser-fetch", "lit-pipeline"):
            t = (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("随插件发布", t, name)
            self.assertIn("kb_init` 不复制 skills 进 vault", t, name)
            self.assertIn("库内无 `.claude/skills/` 属正常", t, name)
            self.assertNotIn("建库脚本会把项目技能复制", t, name)

    def test_qc_pdf_identity_docstring_example_synthetic(self):
        """finding 4：author_overlap 示例输出与合成名一致（末词取姓 → gamma）。"""
        t = (ROOT / "tools" / "qc_pdf_identity.py").read_text(encoding="utf-8")
        self.assertIn('"Carla C. D. Gamma" → gamma', t)

    def test_tools_md_starts_with_h1(self):
        """finding 5：docs/TOOLS.md 不再无标题开头悬空。"""
        first = (ROOT / "docs" / "TOOLS.md").read_text(
            encoding="utf-8").splitlines()[0]
        self.assertTrue(first.startswith("# "), first)

    # ---- Task 6：空库可用性审计 + 遗留项 A-I 的回归断言 ----
    def test_kb_py_no_sci_family(self):
        """遗留项 D：sci 兼容入口的注册/分发段已结构性删除。"""
        t = (ROOT / "tools" / "kb.py").read_text(encoding="utf-8")
        self.assertNotIn('"sci"', t)
        self.assertIn('"lit", "qc"', t)

    def test_tools_md_no_sci_no_dsh_pointer(self):
        """遗留项 D/F：TOOLS.md 无 sci 宣传、无 .dsh 协议指针。"""
        t = (ROOT / "docs" / "TOOLS.md").read_text(encoding="utf-8")
        self.assertNotIn("qc/sci", t)
        self.assertNotIn(".dsh", t)

    def test_skills_no_dead_ledger_pointers(self):
        """遗留项 E/F：技能不得再指向未随包的 _QC-DRIVER/_QC-PROTOCOL/_LIT-WATCH-NEXT。"""
        for p in (ROOT / "skills").rglob("*.md"):
            t = p.read_text(encoding="utf-8")
            for bad in ("_QC-DRIVER", "_QC-PROTOCOL", "_LIT-WATCH-NEXT"):
                self.assertNotIn(bad, t, f"{p}: {bad}")

    def test_qc_loop_protocol_overlay_present(self):
        """遗留项 E：泛化协议骨架经 overlay 随包发布，且 overlay 源件入 git。"""
        self.assertTrue((ROOT / "skills" / "kb-qc-loop" / "references"
                         / "protocol.md").is_file())
        self.assertTrue((ROOT / "build" / "overlay" / "skills" / "kb-qc-loop"
                         / "references" / "protocol.md").is_file())

    def test_no_url_placeholder_damage(self):
        """遗留项 F：盘符占位兜底不得吃掉 URL（http<库外路径> 形态）。"""
        targets = list((ROOT / "skills").rglob("*.md")) + [ROOT / "docs" / "TOOLS.md"]
        for p in targets:
            t = p.read_text(encoding="utf-8")
            self.assertNotIn("http<库外路径>", t, str(p))

    def test_lit_pipeline_when_to_use_vault_root(self):
        """遗留项 F：whenToUse 的库根占位语义正确（<你的库根>，不是 <库外路径>）。"""
        t = (ROOT / "skills" / "lit-pipeline" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("当会话工作目录在 <你的库根> 内", t)

    def test_excluded_one_shot_tool_absent(self):
        """遗留项 A：绑活库具体页的一次性修复器已排除。"""
        self.assertFalse((ROOT / "tools" / "qc_fix_escaped_tex.py").exists())
        self.assertNotIn("qc_fix_escaped_tex.py", _include_entries())

    def test_kb_cite_examples_synthetic(self):
        """隐私：kb_cite 的 README 示例作者/DOI 已全合成（given name 也不留真实形态，
        夹具两端同换：Given Middle Alpha → ALPHA G M）。"""
        t = (ROOT / "tools" / "kb_cite.py").read_text(encoding="utf-8")
        self.assertIn("ALPHA G M", t)
        self.assertIn("Given Middle Alpha", t)
        self.assertIn("10.1073/pnas.2200000001", t)

    # ---- Task 6 fix 轮（review findings 1-5/7）回归断言 ----
    # 隐私纪律：被跟踪测试里不写真实专名，只做**合成形态正断言**与通用形态反断言。

    def test_lit_ingest_fixture_synthetic_surname(self):
        """finding 1：事故论文夹具文件名的作者姓氏已合成（DOI 后缀此前已合成）。"""
        t = (ROOT / "tools" / "lit_ingest.py").read_text(encoding="utf-8")
        self.assertIn("Sample_2026_JES_10.1149_1945-7111_aaa000.md", t)

    def test_publishers_no_ip_and_generalized_auth(self):
        """finding 2：出版商参考不得含实测 IP；机构授权措辞泛化。"""
        import re
        t = (ROOT / "skills" / "lit-browser-fetch" / "references"
             / "publishers.md").read_text(encoding="utf-8")
        self.assertIn("确认机构 IP 授权（以本机实测为准）", t)
        self.assertNotRegex(t, r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")

    def test_review_cycle_no_live_project_state(self):
        """finding 3：§8 改为新工程自查清单模板；三刊组合改示例刊措辞；
        轮次史/投稿排序/稿件原句不得残留（此处只断言通用形态，不贴真实专名）。"""
        t = (ROOT / "skills" / "kb-review-cycle" / "SKILL.md").read_text(
            encoding="utf-8")
        self.assertIn("新工程自查清单", t)
        self.assertIn("示例刊", t)
        self.assertIn("按你的方向自选", t)
        self.assertNotIn("待确认空白", t)
        self.assertNotIn("三目标刊", t)
        self.assertNotIn("主投", t)
        self.assertNotIn("cycle-99", t)
        self.assertNotIn("cycle-10", t)
        self.assertNotIn("cycle-7", t)
        self.assertNotIn("cycle-8", t)
        self.assertNotIn("cycle 6", t)
        # D1–D7 / C1–C9 / 七章方法论保留
        for keep in ("D1–D7", "C1–C9", "七章"):
            self.assertIn(keep, t)

    def test_skill_cross_references_within_bundle(self):
        """finding 4：SKILL.md 文中引用的技能名必须在随包九技能内（死指针回归）。
        提取 `skills/<name>` 路径与「见 (skill) `X` 技能」两种形态；
        末尾断言提取结果非空，防止正则失配造成零正断言。"""
        import re
        allowed = {"kb-onboard", "kb-query", "kb-lint", "kb-ingest-batch",
                   "kb-qc-loop", "kb-review-cycle", "lit-watch",
                   "lit-pipeline", "lit-browser-fetch"}
        refs = []
        for p in sorted((ROOT / "skills").rglob("SKILL.md")):
            t = p.read_text(encoding="utf-8")
            # 形态 1：skills/<name>（含 .claude/skills/<name>；占位符 <name> 不匹配）
            refs += [(p, m) for m in re.findall(r"skills/([a-z][a-z0-9-]*)", t)]
            # 形态 2：见 `X` 技能 / 见 skill `X` 技能 / 见 X 技能
            refs += [(p, m) for m in re.findall(
                r"见\s*(?:skill\s*)?`?([a-z][a-z0-9-]*)`?\s*技能", t)]
        self.assertTrue(refs, "技能引用提取为空——正则失效，断言失去意义")
        for p, name in refs:
            self.assertIn(name, allowed, f"{p}: 引用了未随包技能 {name}")

    def test_si_sweeps_have_positive_fixture(self):
        """finding 5：sweep 集成路径必须有合成库正例夹具（恒返回 [] 不得 PASS），
        空库分支保留 info 口径。"""
        for name in ("qc_si_sweep.py", "qc_si_template_sweep.py"):
            t = (ROOT / "tools" / name).read_text(encoding="utf-8")
            self.assertIn("tempfile.mkdtemp", t, name)
            self.assertIn("夹具 正例", t, name)
            self.assertIn("[info] 全库扫描跑通", t, name)

    def test_real_form_dois_and_titles_synthesized(self):
        """finding 7：真实形态 DOI/标题残留已全合成（正断言合成形态）。"""
        t = (ROOT / "tools" / "lit_browser_fetch.py").read_text(encoding="utf-8")
        self.assertIn("10.1002/anie.6900001", t)
        self.assertIn("10.1038/s41467-026-60003-y", t)
        t = (ROOT / "tools" / "lit_si.py").read_text(encoding="utf-8")
        self.assertIn("10.1021/jacs.6c00004", t)
        self.assertIn("10.1016/j.jpowsour.2024.230001", t)
        t = (ROOT / "tools" / "qc_pdf_identity.py").read_text(encoding="utf-8")
        self.assertIn("Sample Widget Failure At Example Interfaces", t)
        self.assertIn("Removal of sample interface widget failure in examples", t)
        self.assertIn("10.1038/s41467-026-60002-z", t)
        t = (ROOT / "tools" / "lit_manual_import.py").read_text(encoding="utf-8")
        self.assertIn("10.1021/acsnano.6c00001", t)

    # ---- Task 9 fix 轮（review findings 1–5）回归断言 ----
    def test_no_skill_copy_claim_in_carriers(self):
        """finding 1：scaffold/方法论/ops.md 统一为「kb_init 不复制 skills」口径。"""
        for rel in ("scaffold/CLAUDE.md", "docs/METHODOLOGY.md",
                    "skills/lit-watch/references/ops.md"):
            t = (ROOT / rel).read_text(encoding="utf-8")
            self.assertIn("kb_init` 不复制 skills 进 vault", t, rel)
            for bad in ("建库脚本会把它们复制", "建库脚本复制的副本",
                        "库内副本由建库脚本复制", "再重新建库或同步库内副本"):
                self.assertNotIn(bad, t, f"{rel}: {bad}")

    def test_validator_discipline_pointer_normalized(self):
        """finding 3：§校验器自检纪律 死指针 → §六「校验器纪律」（仿 H 项有序规则）；
        skills/kb-lint 自身节标题不带 §，必须原样保留。"""
        for p in (ROOT / "tools").glob("*.py"):
            t = p.read_text(encoding="utf-8")
            self.assertNotIn("§校验器自检纪律", t, p.name)
        t = (ROOT / "tools" / "kb_lib.py").read_text(encoding="utf-8")
        self.assertIn("CLAUDE.md §六「校验器纪律」", t)
        t = (ROOT / "skills" / "kb-lint" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("## 🔴 校验器自检纪律", t)

    def test_review_cycle_counterexample_wording(self):
        """finding 4：「已实测多起反例」→「已有实测反例」（保真，去聚合计数）。"""
        t = (ROOT / "skills" / "kb-review-cycle" / "SKILL.md").read_text(
            encoding="utf-8")
        self.assertIn("已有实测反例", t)
        self.assertNotIn("已实测多起反例", t)

    def test_kb_onboard_mailto_question(self):
        """finding 5：访谈清单含联系邮箱（mailto）问题，落点 datasource.mailto。
        兼作 skill_scrub 插入锚点的漂移兜底（该层未命中不告警）。"""
        t = (ROOT / "skills" / "kb-onboard" / "SKILL.md").read_text(
            encoding="utf-8")
        self.assertIn("联系邮箱", t)
        self.assertIn("mailto", t)
        self.assertIn("datasource.mailto", t)

    def test_rules_readme_trailing_newline(self):
        """finding 2：build/rules/README.md 以换行结尾。"""
        b = (ROOT / "build" / "rules" / "README.md").read_bytes()
        self.assertTrue(b.endswith(b"\n"))

    # ---- 2026-11-17 终审 fix 轮（Minor 1/2）回归断言 ----
    def test_getting_started_dist_marketplace_note(self):
        """终审 minor 1：安装节须说明 dist 分发包不含本地 marketplace 件，
        Claude Code 安装指向仓库根（含 .claude-plugin/marketplace.json）。"""
        t = (ROOT / "docs" / "GETTING-STARTED.md").read_text(encoding="utf-8")
        self.assertIn("dist 分发包不含本地 marketplace 件", t)
        self.assertIn(".claude-plugin/marketplace.json", t)
        self.assertIn("仓库根", t)

    def test_review_cycle_grey_zone_conditional(self):
        """终审 minor 2：D6⑥ 灰色地带判定改条件式（去特定稿件状态残留）。
        兼作 skill_scrub 锚点的漂移兜底（该层未命中不告警）。"""
        t = (ROOT / "skills" / "kb-review-cycle" / "SKILL.md").read_text(
            encoding="utf-8")
        self.assertIn("若稿件属**灰色地带**", t)
        self.assertNotIn("本稿属", t)

    # ---- Task 10：空库冒烟验收（spec §9.3/§9.4）三处空库容忍逻辑回归 ----
    # 核心依赖、无 Obsidian 的空库必须 doctor PASS + toolcheck 通过。
    # 这三处生成物逻辑曾对「可选语义层缺失/空语料/caj2pdf 未克隆」过硬，
    # 经 private/scrub.yaml 规则层泛化（真源不动）。下列断言钉住修复，防重建漂移。

    def test_doctor_tolerates_missing_optional_embedding_index(self):
        """嵌入索引属可选语义层：缺失时 doctor 降为 [--] 跳过，不再硬 FAIL。"""
        t = (ROOT / "tools" / "kb.py").read_text(encoding="utf-8")
        self.assertIn("嵌入索引未建（语义层可选", t)
        self.assertNotIn("[FAIL] 嵌入索引不存在", t)
        # 嵌入存在但陈旧仍须 FAIL（freshness 判据不被削弱）。
        self.assertIn("嵌入覆盖：缺失", t)

    def test_corpus_freshness_empty_corpus_is_ok(self):
        """corpus meta 缺失且无原文文件 ⇒ 空语料合法（ok=True）；
        有文件却缺 meta 仍判 ok=False（不掩盖真陈旧）。"""
        t = (ROOT / "tools" / "kb_corpus.py").read_text(encoding="utf-8")
        self.assertIn("if not list(iter_corpus_files()):", t)
        self.assertIn('"ok": True, "reason": "空语料', t)
        self.assertIn('return {"ok": False, "reason": "corpus meta 不存在"}', t)

    def test_toolcheck_exempts_caj_env_not_ready(self):
        """Task 10 fix 轮：caj_to_pdf selftest 专用退出码 3（失败子项全为可选环境
        判据）按豁免记 SKIP；rc=2（环境无关失败/装齐环境仍失败）不再豁免，仍 FAIL；
        FAIL/TIMEOUT 判据不变。行为级测试见 test_caj_selftest_codes.py。"""
        t = (ROOT / "tools" / "kb_toolcheck.py").read_text(encoding="utf-8")
        self.assertIn('elif rc == 3 and base == "caj_to_pdf.py":', t)
        self.assertNotIn('elif rc == 2 and base == "caj_to_pdf.py":', t)
        self.assertIn('rec["selftest"] = "SKIP"', t)
        self.assertIn("专用退出码 3", t)
        self.assertIn('or rec.get("selftest") in ("FAIL", "TIMEOUT")', t)

    def test_caj_selftest_exit_code_split(self):
        """Task 10 fix 轮：selftest 区分退出码——仅当失败子项全为可选环境判据
        （env_fail 计数 + 环境未 ready）才返回专用码 3；其余失败仍返回 2。"""
        t = (ROOT / "tools" / "caj_to_pdf.py").read_text(encoding="utf-8")
        self.assertIn("ok = fail = env_fail = 0", t)
        self.assertIn('if fail == env_fail and not av["ready"]:', t)
        self.assertIn("return 3", t)
        self.assertNotIn("return 0 if not fail else 2", t)
        # 环境判据标记只落在 caj2pdf 克隆件与其可选 Python 依赖两条 chk 上
        self.assertIn('av["home_ok"], av["reason"], env=True)', t)
        self.assertIn('str(av["missing_python"]), env=True)', t)


if __name__ == "__main__":
    unittest.main()
