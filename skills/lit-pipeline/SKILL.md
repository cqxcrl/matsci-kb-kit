---
name: lit-pipeline
description: "本工具链 的文献流水线本地约定（库根路径、运行产物落点、期刊白名单与 tier 红线、去重源、收尾链路、建卡门禁、已知坑）。用户在本库内做「文献监控/盯刊/找新文献/补文献/lit-watch/把这批 PDF 收编/哪些还没提取/入库收尾」时使用；流程细节与全部命令见 skill `lit-watch`。"
whenToUse: "当会话工作目录在 <库外路径> 内，且任务涉及文献发现、下载、提取、建卡或入库收尾时使用。"
---

# lit-pipeline — 本库的文献流水线约定

> **续作/待办清单见 `tools/_LIT-WATCH-NEXT.md`**（跨会话交接：下一步任务与验收标准、
> 待用户拍板的决定、技术债、下轮别踩的坑、回滚手册）。**接手优化前先读它。**
>
> **流程与命令见 skill `lit-watch`**——真源已迁入库内
> `<KB>\.dsh\skills\lit-watch\`（2026-10-10；`<你的 .claude>\skills\lit-watch` 与
> `<KB>\.claude\skills\lit-watch` 都是指向它的 junction，随库入 git 可回滚）。
> 本文件只放**本库特有**的约定，避免两处文档各说一套。

## 库根与入口

- 库根：`<你的库根>`；所有命令在此目录执行。
- 引擎：`tools/lit_*.py`（发现/取全文/提取/建卡/二次加工/收编/批量/收尾/体检）。
- 调用入口：可用 `python tools/kb.py lit <operation> ...`；全部参数用 `python tools/kb.py tools --json` 查询。
- 配置唯一来源：`tools/lit_config.yaml`（刊白名单与 tier、路径、去重源、`automation.directions`）。
- 与 skill `lit-watch` 的关系：那边讲怎么跑；本文件讲本库的**具体取值与红线**。

## 运行产物落点（2026-10-10 迁移，改代码前必读）

`paths.runs_dir = raw/notes/lit-watch`（**不再** `_archive/lit-watch/lit-runs`）。
`_archive/` 在 `.gitignore` 内且被 Obsidian 排除 ⇒ 放那里的产物**没有回滚网、也点不开**。
子目录一律经 `kb_lib.lit_runs_dir(cfg, "daily"|"picks"|"runs"|"downloads"|"state")` 派生：

| 子目录 | 内容 | 入 git |
|---|---|---|
| `daily/<日期>/` | `cand_*.json` / `digest.md` / `manifest_*.md` / `status.json` / `progress.json` / `run-*.log` | ✅ |
| `picks/` | `<日期>-<时分秒>-picks.json`（同日多次勾选不覆盖） | ✅ |
| `downloads/` | 手动下载清单、手动导入报告 | ✅ |
| `state/` | 去重目录、提取台账、收编台账 + 各工具 mtime 缓存 | 缓存忽略 |
| `runs/` | 抓取结果、体检快照、源缓存、缺口报告、门禁报告、任务日志 | 忽略 |
| `archive-pool/` | 迁移前的历史候选池（匹配池仍扫它） | ✅ |

`_archive/lit-watch/lit-runs/` 只剩**一次性脚本/日志/说明**（8 py / 1 sh / 4 txt / 若干 log）——
那一层名实相符，别再往里写新产物。PDF 收件箱仍是 `raw/pdf/Manual Download/`。

## 每天先做一次体检

```bash
cd "<你的库根>"
python tools/lit_doctor.py            # 0 正常 / 1 警告 / 2 严重
python tools/kb_toolcheck.py          # 实跑全部工具（分母以输出为准，不照抄文档）
```

体检覆盖：依赖（`fitz` 硬依赖）、白名单与 tier、**去重源实际贡献**、去重三方对账、
**DOI 是否粘连中文标点**、**去重集是否降级（`degraded` / `zotero_status`）**、
提取台账欠账、索引新鲜度、双运行时 junction、每日任务日志与空日期目录。

## 本库的四道红线（改代码时勿破）

1. `kb_lib.load_lit_config` **不得退回白名单式透传**：它现在是「已知段逐段合并 +
   未知顶层段兜底合并」，`kb_selftest` 会断言「YAML 的每个顶层键都出现在返回的 cfg 里」。
   历史教训：`tiers` 与 `automation` 都曾因缺席白名单而被**静默丢弃**。
2. `paths.*` **一律配置派生**（`cfg["paths"][...]` / `kb_lib.lit_runs_dir(...)`）。
   迁移前 runs 根在 6 个文件里被硬编码，只有一处读配置 ⇒ 同一条流水线两个产物根。
3. OpenAlex 的 `source.id` OR 列表**上限 100**；白名单 >90 刊须**分片检索后合并**
   （当前 102 刊、两片，并行取回，全局限速 ≈3 req/s）。
4. **不得编造**：通信作者（无 `is_corresponding` 就留白）、`si_status`（必须来自证据）、
   联系邮箱（`datasource.mailto` 为空就跳过 Unpaywall 回退，绝不填占位串）。

## 收尾链路（本库实测耗时）

| 命令 | 耗时 | 说明 |
|---|---|---|
| `kb.py index build` | 秒级 | **必跑**，否则新页不进 BM25 |
| `kb.py index embed [页...]` | 增量/全量 | 语义索引与同名内容哈希 |
| `kb.py index corpus` | 约 1 分钟 | raw 全文分块、真实行号/字符区间与文件哈希 |
| `kb_dois.py` | 冷 ~1.1s / 热 ~0.6s | 去重清单（有 mtime 缓存；`--full` 强制全量） |
| `lit_catalogue.py` | 冷 ~6s / 热 ~0.6s | 去重目录（同上；缩水 >5% 会**拒绝覆盖**并退 4） |
| `qc_base_check.py` | 快 | 五个 `.base` 选中集合重算 + 漂移守门 |
| `lit_finish.py --apply` | — | 写 `wiki/index.md` 行 + `wiki/log_ops.md` + 建索引 |

**`wiki/log.md` 已冻结**（CLAUDE.md）：新记录写 `wiki/log_ops.md`。
`lit_ingest --apply` 会自动串上 `kb_dois` + `lit_catalogue` + `qc_base_check`（无条件）。

## 建卡门禁（2026-10-10 新增，别把它当"打印"）

`lit_ingest --apply` 的退出码是有语义的：
**0** = 写好且门禁全过 ｜ **1** = 写坏（frontmatter 不可解析 / 回链文件不存在等**硬**问题）
｜ **2** = 写好了但**缺补链**（出站 <2 或入站 0，CLAUDE.md §操作流程 6 未完成）。

门禁报 **2** 时**不许当成功**：工具**不替你补链**（会凭空造出错误关联），
只把缺口写进 `runs/gate-<时间戳>.json`。补链是人的活。

## 证据化二次加工（2026-10-24）

`lit_ingest` 只建骨架；`lit_enrich` 负责把外部 LLM 的结构化提案校验后写入 wiki source，不绑定模型厂商：

```bash
python tools/kb.py lit enrich request --page sources/X.md --json > request.json
# 外部 LLM 按 request.output_contract 生成 proposal.json
python tools/kb.py lit enrich apply --proposal proposal.json --json          # 默认干跑
python tools/kb.py lit enrich apply --proposal proposal.json --apply --json # 备份后写页
```

硬约束：每条 claim 必须带 `evidence.path/line_start/line_end/quote`；证据只能是库内已存在 Markdown，
行号为 1-based 闭区间，quote 必须在指定行内逐字存在。路径穿越、错行、错 quote、空 summary、无证据 claim
都会整体拒绝且不写页。写入采用备份 + 校验写盘 + 幂等标记段，保留其他 frontmatter 和正文。
`source_reliability` 只提升为「已做带原文定位的 LLM 二次加工；仍须人工复核」，**不等于人工精读完成**。
本轮不批量改写既有页面；二次加工后仍需人工审阅，再运行 `kb.py index build/index embed` 和 `kb.py doctor`。

## 已知坑（都踩过，写在代码注释里）

- `lit_catalogue.py` 不再导入旧账本 `.lit_watch_seen.json`（含大量参考文献伪 DOI）。
- 旧代码 glob `raw/*.md` 而全文在 `raw/text/` ⇒ 曾漏扫 77 篇（死代码）。
- Zotero 路径曾写 C: 符号链接，断链即静默漏扫。
- `kb_backlinks.py` 曾因 bm25 v1→v2 迁移读 `_tokens` 而**三种模式全崩**，现从 `postings` 还原。
- 每日任务曾用控制台程序，补跑时弹窗被关掉 ⇒ 当天产物为空。
  现在 `lit_daily.py` 边跑边落盘 + `--resume`，计划任务用 `pythonw` 无窗口运行
  （`tools/lit_daily_task.ps1`；action 经 `cmd /c … >> task.log 2>&1`，日志才真的有内容）。
- **`_archive/lit-watch/lit-runs` 曾是活的运行根**：2026-10-04 把它当"运行历史"归档，
  但工具继续往里写——本轮才把产物正式迁出（受控迁移见
  `kb_restructure.py --stage litruns`，含前置断言与回滚清单）。
- **`relevance()` 的正值下限是 0.70** ⇒ T2/T3/T4 的阈值实际不产生区分（未修，已在 skill 记录）。
