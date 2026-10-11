---
name: lit-watch
description: "文献自动发现与入库（本工具链 原生）。全链：体检 → 方向与窗口(标题+摘要复筛) → OpenAlex 检索 → 下载 OA 全文 → 手工下载收编 → PDF 提取 → 建卡骨架(含门禁) → 收尾(index.md/log_ops/索引/base 守门) → 缺口驱动下一轮。触发词：文献监控、盯刊、自动找文献、补文献、lit-watch、每日发现、手工下载收编、这批 PDF 还没提取、入库收尾、跑一下 lit-watch、look for new papers。典型示例：「用 lit-watch 搜固态电解质近一个月的文章，下载、改名、归类、建卡」「把 raw/pdf/Manual Download 里那批收编进库」「入库完把 index.md 和 log_ops 补上」。"
whenToUse: "当用户要盯某个方向的新文献、把每日/每轮候选审核后下载入库、把手工下载的 PDF 收编、查还有哪些 PDF 没提取、或入库后做收尾与体检时使用。"
trigger: /lit-watch
---

# lit-watch — 文献发现 → 下载 → 提取 → 建卡 → 收尾（本工具链）

> 引擎全在知识库里：`<你的库根>\tools\lit_*.py`。
> **一切命令的工作目录是库根**：`cd "<你的库根>"`。
> 本 skill **真源在库内** `<KB>\.dsh\skills\lit-watch\`（2026-10-10 迁入，随库入 git 可回滚）；
> `<你的 .claude>\skills\lit-watch` 与 `<KB>\.claude\skills\lit-watch` 都是指向它的 junction。
> ⚠️ 改内容请改 `.dsh/skills/` 下的真实文件，**不要**改 junction 两侧。

**先体检，再干活。** 不知道库的状态就不要开跑——2026-10-09 的教训是这个流水线
"坏掉"时不会报错，只会静默变差（当天定时任务被外部杀掉、去重目录里 15 条 DOI 粘连中文标点、
某个"去重源"其实 0 篇贡献，全都一声不吭）。

```bash
python tools/lit_doctor.py            # 体检：环境/配置/去重对账/欠账/索引/双运行时/任务
python tools/lit_doctor.py --fix      # 安全修复：重建去重目录与 DOI 清单（幂等）
```

退出码：`0` 正常 / `1` 有警告 / `2` 有严重问题。有 ❌ 就先修，别往下跑。

---

## 产物去哪了（2026-10-10 迁移，最容易踩的一处）

**运行产物不再落 `_archive/lit-watch/lit-runs/`，改落 `raw/notes/lit-watch/`**——因为 `_archive/`
既在 `.gitignore` 内（`git ls-files _archive` → 0，没有回滚网），又被 Obsidian
`userIgnoreFilters` 排除（摘要点不开）。

| 位置 | 内容 | 入 git？ |
|---|---|---|
| `raw/notes/lit-watch/daily/<日期>/` | `cand_*.json`、`digest.md`、`manifest_*.md`、`status.json`、`progress.json`、`run-*.log` | ✅ |
| `raw/notes/lit-watch/picks/` | `<日期>-<时分秒>-picks.json`（同一天多次勾选**不会**互相覆盖） | ✅ |
| `raw/notes/lit-watch/downloads/` | `手动下载清单*.md`、`手动导入报告.md` | ✅ |
| `raw/notes/lit-watch/state/` | 去重目录、提取台账、收编台账**＋各工具的 mtime 缓存** | 缓存忽略（`manual_import_log.json` 除外） |
| `raw/notes/lit-watch/runs/` | 抓取结果、体检快照、源缓存、缺口报告、门禁报告、任务日志 | 忽略（可重建） |
| `raw/notes/lit-watch/archive-pool/` | 迁移前的历史候选池（匹配池仍会扫它） | ✅ |
| `_archive/lit-watch/lit-runs/` | **只剩**一次性脚本/日志/说明（8 py、1 sh、4 txt、若干 log）——那确实是归档料 | 忽略 |

PDF 收件箱**不在**上面：仍是 `raw/pdf/Manual Download/`。
新笔记落点也已从 `raw/_park` 改为 `raw/notes`（`.obsidian/app.json`）。

🔴 **路径全部由 `tools/lit_config.yaml` 的 `paths.*` 派生**（`kb_lib.lit_runs_dir(cfg, 子目录)`）。
**不要在任何脚本里硬编码**——迁移前它有 6 处硬编码副本，只有一处读配置，
导致同一条流水线有两个产物根。

---

## 阶段总览

| 阶段 | 命令 | 关键产物 | 退出码 |
|---|---|---|---|
| 0 体检 | `lit_doctor.py` | 问题清单、`runs/doctor-snapshot.json` | 0/1/2 |
| A 发现 | `lit_daily.py`（按配置方向）／`lit_discover.py`（单方向） | `daily/<日期>/cand_<slug>.json` + `status.json` | daily 0/2/3/4；discover 0/**3**=有分片失败 |
| A′ 摘要 | `lit_digest.py --render` | `daily/<日期>/digest.md`、`daily/latest-digest.md`、`<库内运行产物目录>` 副本 | 0 |
| A″ 勾选 | `lit_digest.py --list / --pick` | `picks/<日期>-<时分秒>-picks.json`（**全字段，零损失**） | 0/2 |
| B 取全文 | `lit_fetch.py --in <picks> --outdir raw/pdf` | `raw/pdf/*.pdf` + `downloads/manifest-<ts>.md` | 0=至少一篇成功／**4=全部失败**／2=参数或输入不可用 |
| B′ 收编 | `lit_manual_import.py` | 改名入库 + `downloads/手动导入报告.md` + 台账 | 0 |
| C 提取 | `lit_batch.py --extract` | `raw/text/*.md`、`raw/assets/<slug>/fig_*.png`、台账 | 0 |
| D 建卡 | `lit_batch.py --ingest [--apply]` | `wiki/sources/*.md` **骨架** + `runs/gate-*.json` | 0=过／**1=写坏**／**2=缺补链** |
| E 收尾 | `lit_finish.py --apply` | `index.md` 行、`log_ops.md`、BM25 索引 | 0/1 |
| F 缺口 | `lit_gapscan.py --out` | `runs/gaps-<日期>.json` | 0/**1=降级**／2=写盘失败 |

---

## 0 · 首次/换机器

1. `python tools/lit_doctor.py` —— 看有没有 ❌。
2. 方向写进 `tools/lit_config.yaml` 的 `automation.directions`（**不要在脚本里硬编码方向**）：
   ```yaml
   automation:
     window: "近一周"
     limit: 15
     results_dir: "<库内运行产物目录>"
     directions:
       - {slug: battery, label: 电池, limit: 15, query: "battery lithium ... interphase"}
   ```
3. 期刊白名单是**范围边界**：要加刊就改 `journals`（每刊带 `tier: T0..T4`）。
   白名单为空 = 退化成全网关键词检索。
4. `python tools/kb_toolcheck.py` —— **实跑**每个工具的 `--selftest`/`--help` 与写盘防呆。
   数字会随工具增删漂移，**以实跑输出为准，不要照抄文档里的分母。**

## A · 每日/每轮发现

```bash
python tools/lit_daily.py                 # 按配置里的方向各跑一轮（推荐）
python tools/lit_daily.py --resume        # 今天被中断后续跑（跳过已成功方向）
python tools/lit_daily.py --dry-run       # 只看会跑什么
python tools/lit_discover.py "<方向关键词>" "近半个月" --limit 20 \
       --out raw/notes/lit-watch/archive-pool/cand_<名字>.json
```

`lit_daily.py` 的退出码要当信号读：**0** 全部成功／**2** `--directions` 与配置不匹配／
**3** 有方向失败（含分片失败）／**4** 全部失败。
（失败方向会在 `status.json` 与摘要里标 ❌；**不要把"失败"读成"这个方向没有新文献"**。）

要点：
- 去重键 = 本机文献目录 ∪ 库内已建卡 DOI 清单（`dedup_sources` + Zotero）。
  **目录里 `degraded` 非空或 `zotero_status != ok` ⇒ 去重集残缺**，会重复下载；工具会告警。
- tier 决定标题+摘要复筛阈值（T0 0.40 / T1 0.45 / T2 0.55 / T3 0.60 / T4 0.70）；
  **T0/T1 不被 `--limit` 截断**（宁可多不能漏）。
- 白名单 >90 刊自动分片检索（OpenAlex 的 OR 列表上限 100），分片**并行**取回，
  全局限速约 3 req/s；单分片最多翻 `MAX_PAGES=3` 页，**截断会告警并给出计数**。
- ⚠️ **已知限制（未修，如实记录）**：`relevance()` 的正值下限是 0.70
  （命中标题 0.9／仅命中摘要 0.7 取大）⇒ T2/T3/T4 的 0.55/0.60/0.70 阈值
  **实际不产生区分**。要真正分层需要改权重，那会动真实召回，故暂不动。

## A′/A″ · 摘要与勾选（取代过去的三段手工流水线）

```bash
python tools/lit_digest.py --render              # 从候选 JSON 重新生成摘要（可重复渲染）
python tools/lit_digest.py --list                # 列出可勾选 ID：battery#3
python tools/lit_digest.py --pick "battery#1,battery#3,oer#2-5"   # → picks JSON
python tools/lit_digest.py --pick all --min-rel 0.9 --only-oa     # 带过滤
python tools/lit_digest.py --pick "battery#1" --mark              # 顺带在摘要里标 [x]
```

**为什么不再手工转 JSON**：过去是 `digest.md → digest-parsed.json → digest-keep.json →
digest-fetch-input.json` 三次落盘，且**往返 markdown 会丢字段**——
digest 里没有 `oa_url` / `authors_all` / `journal_tier`，导致下游下载来源变少、建卡丢档位。
现在 `--pick` 直接在候选 JSON 上勾选，fields 一个不丢，并且带 `pick_id` 可追溯。

## B · 取全文

```bash
python tools/lit_fetch.py --in raw/notes/lit-watch/picks/<日期>-<时分秒>-picks.json \
       --outdir raw/pdf --label "<方向>" [--limit N]
```

- 来源顺序：OpenAlex `oa_url` → Unpaywall → 出版社机构直链；**逐条校验 `%PDF-` 魔数**，
  且拒绝 `text/html`；PDF/SI 都是**原子写**（`.part` + `os.replace`）。
- 拿不到的写进 `<runs_dir>/downloads/manifest-<时间戳>.md`（含可点 DOI 与直链）。
- **退出码**：0 = 至少一篇成功；**4 = 全部失败**（旧版无条件 0，上层读不出"全被墙了"）。
- ⚠️ `datasource.mailto` 为空 ⇒ **Unpaywall 回退被整体跳过**（只告警一次）。
  想恢复该回退请在 `tools/lit_config.yaml` 填**真实**邮箱——**绝不编造联系地址**。

## B′ · 手工下载收编（以前每批都要临时写脚本）

```bash
python tools/lit_manual_import.py                  # 干跑：配对结果 + 报告
python tools/lit_manual_import.py --apply          # 改名并移入 raw/pdf/
python tools/lit_manual_import.py --inbox "<库外路径>" --fresh-since 2026-10-06
```

- 收件箱默认 `raw/pdf/Manual Download/`；匹配池 = **新旧两处**候选 JSON
  （`raw/notes/lit-watch/**` 与 `_archive/lit-watch/lit-runs/**`）∪ 两处手动下载清单。
  **先按 PDF 首页 DOI 精确匹配**，再按标题词重叠（需 ≥3 词命中、且与第二名差距足够，否则判 ambiguous 不猜）。
- 非 PDF（HTML 冒充）直接拦下；已在库（DOI 命中本机目录）默认跳过并列入报告。
- 未匹配的隔离到 `raw/pdf/_unmatched/`，**永不删除**；台账 `state/manual_import_log.json`。

## C · 提取（批量 + 台账）

```bash
python tools/lit_batch.py --reconcile     # 首次对账：用 DOI/文件名判定哪些其实已提取（只读 PDF 首页）
python tools/lit_batch.py --status        # PDF / 全文 / 卡片 三段各欠多少
python tools/lit_batch.py --pending --limit 20
python tools/lit_batch.py --extract --limit 5
python tools/lit_extract.py "<单个pdf>" [--dpi 150] [--force] [--json]
```

- 台账 `state/extract_ledger.json`；`--reconcile` 用**PDF 首页 DOI 与 raw/text 正文 DOI** 对齐，
  所以"md 名与 PDF 名不一致"不会再被误判为未提取。
- `lit_extract.py` 默认**不覆盖**已存在的 `raw/text/*.md`（要覆盖加 `--force`）——
  这是把库里"覆盖前先确认"的规则落进代码。退出码：`2` = 目标不是真 PDF；`4` = 目标已存在且未加 `--force`
  （`lit_batch` 把 4 **记成"已提取"**，不再永久 pending）。
- 批量提取走**进程内**（一个解释器连做多篇），省掉逐篇的冷启动；
  单篇失败被隔离成一条 `rc=124`，**整批继续**、台账照落。

## D · 建卡（只建骨架，绝不替你写结论）

```bash
python tools/lit_batch.py --ingest            # 干跑：列出已提取但还没建卡的全文
python tools/lit_batch.py --ingest --apply
python tools/lit_ingest.py --candidates <cand.json>            # 干跑
python tools/lit_ingest.py --candidates <cand.json> --apply
```

骨架规则（写错会被门禁抓）：frontmatter 只用**可核验元数据**；作者/通讯作者取不到就留白并标
`> ⚠️ 信息缺口`；`institution` 留白 + `authors_source`；`source_reliability` 标「待核」；
正文只有标题 + 摘要 + `## 待精读`。同名页若 **DOI 不同**会自动加 `-2` 后缀而不是静默跳过。

**`si_status` 由证据推导，不再默认 `missing`**：取值来自
① 独立 SI 文件 `<pdf_dir>/si/*.si.pdf` 存在 → `present`；
② 提取件头部声明「补充材料 a-b 页」→ `partial`；
③ 头部声明「无补充材料」→ `missing`（依据写进正文）。
`missing`/`partial` 会在正文就地加 `> ⚠️ 信息缺口：…`。

**骨架门禁（本轮新增，硬判定）**——`--apply` 后自动跑：
- **硬**（退出码 1）：frontmatter 不可解析 / 缺 type / `authors` 不是列表 /
  `sources:` 首条不是 `[[raw/...]]` / 回链文件在盘上不存在。
- **软**（退出码 2）：出站页面链接 <2 或入站 =0 —— 页面本身完好，但
  **CLAUDE.md §操作流程 6 的补链纪律未完成**。工具**不替你补链**（那会凭空造出错误关联），
  只把缺口写进 `runs/gate-<时间戳>.json` 并在终端列出。**看到 2 就要去补链，别当成功。**

`--apply` 后自动重跑 `kb_dois.py` + `lit_catalogue.py` + `qc_base_check.py`（Bases 守门）；
`--with-index` 还会跑 `kb_build_index.py`（并在存在时串上 `kb_corpus.py --build` /
`kb_semantic_search.py --add <新页>`）。

## E · 收尾（index.md / log_ops.md / 索引）

```bash
python tools/lit_finish.py --since 2026-10-09            # 干跑：给出将插入的行与日志
python tools/lit_finish.py --since 2026-10-09 --apply     # 写入并重建 BM25 索引
python tools/lit_finish.py --pages 2026-x-JACS.md --apply --with-corpus --with-semantic
```

- `wiki/index.md`：按既有 4 列格式把新页插进 Sources 表尾，**幂等**，写后复算。
  入站数**一次扫描**算出全部页（旧版每页重扫全 wiki）；写前备份到 `.qc_backup_YYYYMMDD/`。
- `wiki/log_ops.md`：追加一行（**log.md 按 CLAUDE.md 已冻结，不要再写它**）。
- 链路：`kb_build_index.py`（**必跑，秒级**）→ 可选 `kb_corpus --build`（约 66s）／
  `kb_semantic_search --add <新页>`（增量）→ `kb_lint.py --quick` → `kb.py --doctor`。
- **没跑语料/语义索引 = 新页搜不到**，命令末尾会提醒。
- 换行：本库 `wiki/` 是**混合**换行；工具按多数票写回并**点名混合文件**，
  不让"只加一行却出现几千行 diff"的事故复发。

## F · 缺口驱动下一轮

```bash
python tools/lit_gapscan.py                          # 按「缺口严重度 × 页面重要性」排序
python tools/lit_gapscan.py --queries                # 只出检索式（带出处/信号/权重注释），直接喂阶段 A
python tools/lit_gapscan.py --signals single-source,no-experiment
python tools/lit_gapscan.py --out raw/notes/lit-watch/runs/gaps-2026-10-10.json
```

信号来自库自身：`evidence_base: single-source/secondhand`、`si_status: missing`、
正文 `⚠️ 单源论断 / 无实验验证 / 信息缺口`、`## 诚实边界` 里的待办。
**`si-missing` 现在要求双条件**（`si_status` **且**正文有显式 SI 表述），
同页有其它缺口时并入不重复计分——否则该信号会凭空造出缺口。
`meta_full.json` 读不到时**显式降级并返回退出码 1**（入度权重会全变 1.0）。

---

## 规则（违反即返工）

1. **期刊白名单是范围边界** —— 只收白名单内的刊；命中不足时先降阈值/扩刊，不是绕过复筛。
2. **方向锁定靠标题+摘要复筛** —— 不要用标题关键词直接当结论。
3. **不伪造证据** —— 拿不到全文就列清单交人工；读不到就只写到主题层面并标注；
   **HTML 冒充 PDF 必须判失败**（`%PDF-` 魔数 + `doc.is_pdf` 双闸）。
   **不得伪造通讯作者**（OpenAlex 无 `is_corresponding` 时留白）、
   **不得伪造 `si_status`**、**不得编造联系邮箱**。
4. **不代替思考** —— 建卡只建骨架，报告只做统计；结论必须逐篇读原文后写。
   门禁报 2（缺补链）时**不许当成功**。
5. **覆盖任何已有文件前先确认**；`raw/` 只写不改既有资料。
6. **每轮结束必须更新去重清单**（`lit_ingest --apply` 会自动跑；否则下轮重复下载）。
7. **失败要能被读出来** —— 方向失败、分片失败、抓取全失败、去重集降级、
   索引降级都要**有退出码**，不许静默变"没有新文献"。
8. Windows 下命令带 `PYTHONIOENCODING=utf-8`；工具自身已在 import 期把 stdout 切 UTF-8。

## 自检（改完代码或换机器后跑）

**只有两条命令**（旧版在这里手写了一份 13 个工具的名字清单，很快就与真实工具集脱节）：

```bash
python tools/lit_doctor.py        # 环境/配置/去重/欠账/索引/任务 体检
python tools/kb_toolcheck.py      # 实跑：编译 + --selftest + --help + 写盘防呆（分母以输出为准）
```

单工具改动后仍可直接 `python tools/<工具>.py --selftest`；
`kb_lint` 的双自检是 `python tools/kb_lint.py --selftest` 与 `--selftest-deep`。

## 参考文件（按需读）

| 文件 | 什么时候读 |
|---|---|
| `references/runbook.md` | 需要每个阶段的完整参数、产物路径与判据时 |
| `references/ops.md` | 收尾链路、自动化任务、体检项、以及 2026-10-09 那批事故的根因与修法 |
| `<知识库>\tools\_LIT-WATCH-NEXT.md` | **跨会话续作清单**：待办（含验收标准）、待用户拍板的决定、技术债、下轮别踩的坑、回滚手册。接手优化工作时**先读它** |
