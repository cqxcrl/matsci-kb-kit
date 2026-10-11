# lit-watch 运行手册（参数 · 产物 · 判据）

所有命令的工作目录 = 库根 `<你的库根>`。`<py>` = `python`（Windows 也可 `py`）。

> **产物路径 2026-10-10 起**：`<runs_dir>` = `raw/notes/lit-watch/`（配置键 `paths.runs_dir`），
> 子目录 `daily/ picks/ runs/ downloads/ state/ archive-pool/` 由 `kb_lib.lit_runs_dir()` 派生。
> **运行产物不再落 `_archive/lit-watch/lit-runs/`**（那里只剩一次性脚本/日志/说明）。
> PDF 收件箱仍是 `raw/pdf/Manual Download/`。

## 0 · 体检 `lit_doctor.py`

| 参数 | 作用 |
|---|---|
| `--quiet` | 只打印 warn/error |
| `--json` | 机器可读 + 写快照 `<runs_dir>/runs/doctor-snapshot.json`（用于环比） |
| `--fix` | 重跑 `lit_catalogue.py` + `kb_dois.py`（幂等；修 DOI 污染与清单滞后） |

检查面：Python/依赖（`fitz` 硬依赖、`yaml`/`jieba` 软依赖）→ 目录 → 配置（白名单、tier、
缺 ISSN、去重源**实际贡献**、Zotero 路径）→ 去重三方对账（目录 ∪ dois.json ∪ 卡片页，含
**DOI 未归一**与**缺标题**计数、降级源）→ 欠账（收件箱、隔离区、提取台账）→ 索引新鲜度 →
双运行时（全局 skill / DSH junction / KB 项目技能 / 斜杠命令）→ 每日任务（cron.log、空日期目录、
计划任务）→ 库内健康度（抽样 frontmatter 可解析率、待精读、待核比例）。

## A · 发现

```bash
python tools/lit_daily.py [--day D] [--window 近一周] [--limit 15] \
       [--directions slug1,slug2] [--resume] [--dry-run] [--no-render]
python tools/lit_discover.py "<查询>" "<窗口>" [--days N|--since YYYY-MM-DD] \
       [--limit N] [--out X.json] [--manifest Y.md] [--rel-min 0.55] [--no-seen] [--config Z.yaml]
```

- 窗口说法：`近三天/近一周/近半个月/近一个月/近三个月/近半年/近一年`、`N天/N周/N个月/N年`。
- 产出字段：`title, main_authors, authors_all, corresponding_author, doi, journal, issn_l,
  journal_tier, ingest_depth, publication_date, relevance, oa_url, is_oa, abstract`。
- 判据：**退出码 3 = 有分片失败**（检索未完成，不能读成"没新文献"）；0 且 0 篇才是真的没有。
  ⚠️ 旧版只在"零命中"时返回 3，「片 1 成功 + 片 2 失败」会返回 0 —— 已修。
- 通信作者**不编造**：OpenAlex 无 `is_corresponding` 时留白（旧版拿末位作者顶替）。
- 单分片最多翻 `MAX_PAGES=3` 页；**截断会告警并给出计数**（`retrieval.truncated_batches`）。
- 空结果排查顺序：放宽窗口 → 降 `--rel-min` 0.05 → 换英文标准说法 → 查白名单 →
  看有没有 `[warn] 未匹配到任何白名单期刊`。

## A′/A″ · 摘要与勾选 `lit_digest.py`

```bash
python tools/lit_digest.py --render [--day D] [--window W] [--with-ids] [--no-results-copy]
python tools/lit_digest.py --list [--day D]
python tools/lit_digest.py --pick "battery#1,oer#2-5|all" [--min-rel R] [--only-oa] \
       [--limit N] [--out X.json] [--mark]
python tools/lit_digest.py --parse <旧digest.md>   # 兼容旧摘要（字段有损，会警告）
python tools/lit_digest.py --stats
```

- ID = `<slug>#<n>`，n 是该方向**相关度降序**后的序号，与摘要里的编号一致。
- `--pick` 产出 `{query, days, generated, source, count, papers}`，**papers 保留全部字段**
  并加 `pick_id`/`direction`；默认落 `<runs_dir>/picks/<日期>-<时分秒>-picks.json`。
- 摘要落点：`daily/<日期>/digest.md`、`daily/latest-digest.md`、
  `<automation.results_dir>/lit-watch-daily-<日期>.md`（默认 `<库内运行产物目录>`，纯英文路径便于点开）。

## B · 取全文 `lit_fetch.py`

```bash
python tools/lit_fetch.py --in <picks.json> [--outdir <raw/pdf>] [--manifest <清单.md>] \
       [--limit N] [--label "<方向>"] [--si-dir <dir>]
```

- 成功判据：`%PDF-` 魔数 + 非 `text/html`；失败原因逐条记录。
- 失败清单：`<runs_dir>/downloads/手动下载清单.md`（可点 DOI/直链）。
- 结果：`<runs_dir>/runs/fetch_result-<时间戳>.json`。
- 已存在同名 PDF 且体积 >20KB 时会跳过（避免覆盖人工整理过的原件），但会再做一次魔数校验。

## B′ · 收编 `lit_manual_import.py`

```bash
python tools/lit_manual_import.py [--inbox D ...] [--fresh-since YYYY-MM-DD] \
       [--min-score 0.5] [--on-dup skip|import] [--limit N] [--pool-stats] [--report P] [--apply]
```

- 匹配顺序：**PDF 首页/元数据 DOI** → 标题词重叠（≥3 词命中，且与次优差距 ≥0.15，否则 ambiguous）。
- 行为：命中→按 `lit_fetch.pdf_filename()` 改名移入 `raw/pdf/`；未命中→`raw/pdf/_unmatched/`；
  非 PDF→拒绝；已在库→默认跳过。台账 `<runs_dir>/state/manual_import_log.json`。
- 报告：`<runs_dir>/downloads/手动导入报告.md`。

## C · 提取 `lit_batch.py` / `lit_extract.py`

```bash
python tools/lit_batch.py --reconcile | --status | --pending [--limit N] \
       | --extract [--limit N] [--dpi 150] | --ingest [--apply] [--limit N]
python tools/lit_extract.py "<pdf>" [--out raw/text] [--assets raw/assets] [--dpi 150] \
       [--no-images] [--main-pages N] [--force]
```

- 台账 `<runs_dir>/state/extract_ledger.json`：`{pdf 相对路径: {ok, how, doi, text, reason, at}}`。
- 对账判据（按可靠性）：① 台账已有成功记录且产物在 ② 同名 md ③ **DOI 对齐**（PDF 首页 vs md 正文）
  ④ 标题词重叠 ≥0.6。都不中才是真待办。
- `--ingest` 只看"已提取但没有任何卡片 `sources:` 引用它"的全文 —— 与"卡片是否精读"无关。

## D · 建卡 `lit_ingest.py`

```bash
python tools/lit_ingest.py [--candidates X.json | --files raw/text/a.md ... | --all-text] \
       [--apply] [--with-index] [--no-links]
```

- 干跑默认；`--apply` 才写盘。写入后：写后复算（N 写 = N 读）→ 自动重跑
  `kb_dois.py` + `lit_catalogue.py` → `--with-index` 再跑 `kb_build_index.py`
  （且存在时串 `kb_corpus.py --build`、`kb_semantic_search.py --add <新页>`）。
- 页面名 = `{年}-{标题前42字}-{刊名缩写}`；同名且 DOI 不同会加 `-2` 后缀并告警。
- 只建骨架；作者取不到留白 + `⚠️ 信息缺口`；`source_url` 仅在 DOI 完整时才生成。

## E · 收尾 `lit_finish.py`

```bash
python tools/lit_finish.py [--pages f1 f2 | --since YYYY-MM-DD | --days N] [--limit N] \
       [--apply] [--no-chain] [--no-index] [--with-corpus] [--with-semantic]
```

| 步骤 | 谁做 | 耗时 | 说明 |
|---|---|---|---|
| `wiki/index.md` 行 | 本脚本 | <1s | 插在 Sources 表尾；幂等；写后复算 |
| `wiki/log_ops.md` 行 | 本脚本 | <1s | **不是 log.md**（后者已冻结） |
| `kb_build_index.py` | 本脚本 | 秒级 | 必跑；否则新页不进 BM25 |
| `kb_corpus.py --build` | `--with-corpus` | ~66s | raw 全文分块检索面 |
| `kb_semantic_search.py --add` | `--with-semantic` | 增量 | 语义检索面（全量重建约 110s） |
| `kb_lint.py --quick` | 本脚本 | <1s | 本批红旗 |
| `kb.py --doctor` | 本脚本 | <1s | 索引新鲜度（注意它也会报嵌入缺失） |

另外：新建/大改 concept、topic 页时，**在建索引之前**先跑
`python tools/qc_evidence_base.py --apply`，否则 `evidence_base` 进不了索引。

## F · 缺口 `lit_gapscan.py`

```bash
python tools/lit_gapscan.py [--top 20] [--signals s1,s2] [--queries] [--list-signals] [--json]
```

## 一轮完整命令（复制即用）

```powershell
cd "<你的库根>"
$env:PYTHONIOENCODING="utf-8"
python tools/lit_doctor.py
python tools/lit_daily.py                       # 或 --resume
python tools/lit_digest.py --list
python tools/lit_digest.py --pick "battery#1,battery#2,ai-for-materials#1-3"
python tools/lit_fetch.py --in <runs_dir>/picks/<日期>-<时分秒>-picks.json --label "本轮"
# 被墙的按清单手动下载到 raw/pdf/Manual Download/ 之后：
python tools/lit_manual_import.py
python tools/lit_manual_import.py --apply
python tools/lit_batch.py --reconcile
python tools/lit_batch.py --extract --limit 10
python tools/lit_batch.py --ingest           # 干跑
python tools/lit_batch.py --ingest --apply
python tools/lit_finish.py --since <日期> --apply
```
