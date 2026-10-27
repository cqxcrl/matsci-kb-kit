---
name: kb-lint
description: 知识库健康检查与批量修复（分级 lint、补链、工具实跑自检）。用户说“lint”“健康检查”“检查一下库”“补链”“孤立页面”“这批 ingest 质量如何”时使用。区分 --quick（效率优先，只查最近 ingest）与 --deep（全库全量 + 扩展检查族 A–F + 可修复项）。改动任何 lint/校验脚本后必跑自检。
---

# 知识库健康检查（lint）

工作目录为库根。**先跑工具，不要凭印象报问题。**

## 分级 lint：deep 与 quick 定位不同

```bash
python tools/kb_lint.py --quick                    # 只查最近 ingest 的页面，跳过 O(全库) 项
python tools/kb_lint.py --quick --days 3           # 常用：最近 3 天
python tools/kb_lint.py --deep                     # 全库全量：既有 17 项 + 扩展族 A–F
python tools/kb_lint.py --deep --fix               # 干跑预览可机械修复项（不写盘）
python tools/kb_lint.py --deep --fix --apply       # 真正落盘（自动备份 .qc_backup_YYYYMMDD/）
```

辅助：

```bash
python tools/kb_backlinks.py --suggest   # 孤立页 / 弱连接页 + 补链建议
python tools/kb_build_index.py --stats   # 索引新鲜度
python tools/kb_toolcheck.py             # 🔴 实跑全部工具的 --selftest/--help
```

## 扩展检查族（仅 `--deep` 生效）

| 族 | 检查 | 可自动修复 |
|---|---|---|
| A 结构完整性 | sources 的 raw 回链真实性、图片真实性、frontmatter 键拼写、日期格式 | 日期格式（仅可无损归一化时） |
| B 字段与证据链 | schema 类型、authors 结构破坏字符、evidence_base↔sources 重算、SI 标记、source 缺 raw | 列表字段被写成标量 |
| C 数据质量与冗余 | 重复别名、tag 拼写变体、同源副本候选 | —（需人工确认） |
| D 关系图与综合层 | 孤立页、entity 深度、topic 覆盖、degree、证据继承 | — |
| E 工具完整性 | 静态：selftest 覆盖、硬写 `.qc/`、编译健全性 | 动态见 `kb_toolcheck.py` |
| F 内容严谨性 | 占位符残留、百分比密集、空摘要（仅机械可判定部分） | — |

⚠️ **D/E/F 的纪律**：LLM 级判断（"内容是否合理、严谨"）**不在此处冒充**——
机械可判定的才报，需人判的一律 `fix_id=None` 留给人工。
`--fix` 后须遵循写盘铁律（见下）。日期修复器**仅在可无损归一化**时动手，语义不明（`2026-10`、`最近`）一律不碰——**宁可不修，不可改错**。

## 人工抽查项（工具查不到的）

读 `wiki/index.md` 取全貌后抽查：矛盾（跨页说法不一）、过时（被新来源推翻）、孤立（无入站）、
缺失（高频引用但无专属页）、缺口（可联网填补）、**证据标记未继承**
（本页复述了上游带限定标记的数字却没有承接表述——`check_evidence_inheritance` 自动检测，
**这是 QC 实证的头号失真类型**）。

报告存 `wiki/outputs/`，并追加 `wiki/log_ops.md`。

## 🔴 校验器自检纪律（本库已八次同类事故）

> **凡是"用正则/字符串计数做判定"的校验器，必须能对已知答案的样本反算一次。**

事故模式一律是「**计数器本身出错，却被读成内容质量问题**」：429 条真实 raw 回链被误报 broken；
`qc_fix_image_syntax` 报 34 处图片语法错（真值 0）；`qc_evidence_base` 因判定顺序错把 127 个
**已发表**论文（`source_reliability` 含「**非**预印本」）误判为预印本；`kb_lint_deep` 首版一次
报 302 处（同源根因：把「规范定义」当成「实况」），修后 302 → 67（真值近 0）；
某工程 断图链 `[^)]+` 把含成对括号的合法路径截断，报 104 条/18 份（真值 **89/16**）。

**强制做法**：

```bash
python tools/kb_lint.py --selftest
python tools/kb_lint.py --selftest-deep
python tools/kb_selftest.py      # 底座：frontmatter 重组、QC 工作目录、换行归一、出链剔除
python tools/kb_toolcheck.py     # 实跑全部工具（46/46 全绿基线）
```

🔴 `--selftest` 存在 ≠ 通过 ≠ 工具可用。实证：`kb_semantic_search --selftest` 曾因**嵌入索引陈旧**
实跑 FAIL，而 E 族静态检查看不见（静态只 grep "selftest" 字样）。

守门夹具必须**同时含正例与反例**——只测「该过的过了」会漏掉「该报的没报」。
**新增回归夹具**：把每次踩过的坑写成夹具，否则同一坑会踩第三次。

**判据**：修复前先记录**基线数字**，修复后对照；数字下降必须能逐类解释，
否则可能是把真问题一起放过了。

## 🔴 写盘脚本的额外铁律

1. **必须有 `--apply` 开关，默认干跑**
2. **写前用「与被校验系统同一个解析器」复核**——即 `kb_lib.split_frontmatter`，
   **不要另写一个「差不多」的正则**（宽松的校验器等于没有校验器；曾因此「校验通过、实际已坏」）
3. **批量写盘前先备份**（`.qc_backup_YYYYMMDD/`），**写后复算总量**：写 N 页就要能读出 N 页

**重组 frontmatter 一律走 `kb_lib.join_frontmatter(fm_text, body)`**，不要手写
`"---" + fm + "\n---" + body`——该写法在两个工具里各犯过一次，后果是 frontmatter **静默解析不出来**
（曾一次写坏 124 页，页面能正常打开、人工浏览完全看不出）。

凡**会写盘**的修复脚本，运行前必须与一个**独立实现**（grep / 另一段正则）对总数；
数字不一致时**先怀疑工具**，**不得先跑 `--apply`**。
