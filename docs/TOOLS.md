


>
> 📚 **配套文档**（2026-10-11 从 CLAUDE.md 析出，CLAUDE.md 只留指针）：
>
> 🔧 **文献流水线（lit-watch）**：引擎是 `tools/lit_*.py`（2026-10-10 扩容：新增体检、摘要勾选、
> 手工收编、批量台账、入库收尾、每日发现、期刊白名单维护）。
> 2026-10-26 新增 `lit_browser_fetch.py`：浏览器兜底（真实 Edge + 类人鼠标），
> 自动下载失败时补正文与 SI；协议见 `.dsh/skills/lit-browser-fetch/`。

## 主工具链 (tools/)

### 2026-10-24 统一调用层

**LLM/脚本首选 `kb.py`，旧脚本作为薄兼容层保留。** 不需要在 90 余个脚本中逐个猜参数；
先用 `python tools/kb.py tools --json` 获取 AST 静态生成的机器可读清单（不导入、不执行被扫描工具）。

| 需求 | 规范命令 |
|---|---|
| 简单事实：BM25/向量/RRF/本地精排/Top-K | `python tools/kb.py ask "什么是固态电解质" --strategy simple --json` |
| 复杂比较、机制、争议、证据核验 | `python tools/kb.py ask "比较 A 与 B 并核对证据" --strategy agentic --json` |
| 显式传统检索 | `python tools/kb.py search "SSE 水解" --mode hybrid -k 10 --json` |
| 兼容分层证据包 | `python tools/kb.py route "固态电解质" --budget 5,5,8` |
| 原文块回指 | `python tools/kb.py corpus "旋涂法" -k 8 --json` |
| 索引维护 | `python tools/kb.py index build` / `index embed` / `index corpus` |
| 健康检查 | `python tools/kb.py doctor --check-reranker` |
| 常驻服务 | `python tools/kb.py serve start --warm` / `serve status` / `serve stop` |
| 文献证据化二次加工 | `python tools/kb.py lit enrich request --page sources/X.md` |

`hybrid` 的 RRF 只负责候选融合，**不等于精排**。融合候选必须由本地 CrossEncoder 重排；
模型缺失、索引过期或推理失败时明确失败，不退回 BM25 冒充混合检索。默认模型为
`BAAI/bge-reranker-base`，可用 `MATSCI_RERANKER_MODEL` 指向本地模型；首次下载必须显式使用
`--allow-download` 或 `MATSCI_RERANKER_ALLOW_DOWNLOAD=1`。

| 工具 | 用途 | 用法示例 |
|------|------|----------|
| `kb_lib.py` | 共享库（被其他工具导入；DOI 归一、frontmatter 解析/重组、代码剔除、lit 配置加载）。`--selftest` 跑底座不变量 | `python tools/kb_lib.py --selftest` |
| `kb.py` | **统一首选入口**：ask/search/route/corpus/index/serve/lit/qc/sci/doctor/tools | `python tools/kb.py ask "<问题>" --json` |
| `kb_rag.py` | 传统 RAG 引擎：BM25、向量、RRF、强制本地 CrossEncoder、Top-K | 由 `kb.py search/ask` 调用 |
| `kb_agentic.py` | 模型无关 Agentic RAG：分类、规划、有界分层检索、图扩展、证据包 | 由 `kb.py ask --strategy agentic` 调用 |
| `kb_manifest.py` | AST 静态工具/参数清单与规范替代入口 | `python tools/kb.py tools --json` |
| `lit_enrich.py` | 模型无关二次加工：逐字证据校验、默认干跑、备份、幂等写页 | `python tools/kb.py lit enrich request --page sources/X.md` |
| `kb_build_index.py` | BM25/元数据索引引擎（规范入口为 `kb.py index`） | `python tools/kb.py index build` |
| `kb_search.py` | 旧检索兼容层（新调用用 `kb.py search`） | `python tools/kb_search.py "固态电解质"` |
| `kb_route.py` | 分层证据引擎（L1/L2/L3；新调用用 `kb.py route`） | `python tools/kb.py route "<问题>"` |
| `kb_semantic_search.py` | 嵌入索引与向量检索引擎 | `python tools/kb.py index embed` |
| `kb_corpus.py` | raw 全文分块索引与检索（真实行号+字符区间回指） | `python tools/kb.py index corpus` |
| `kb_graph.py` | 多跳推理 / 枢纽与桥接页 | `python tools/kb_graph.py --path A B` |
| `kb_where.py` | **「库内有没有 X」四目录检索**（逐目录报命中数；NULL 断言前必跑） | `python tools/kb_where.py "Shiryaev"` |
| `kb_backlinks.py` | 链接图分析与补链建议 | `python tools/kb_backlinks.py --suggest` |
| `kb_lint.py` | 分级 lint 检查（`--quick` / `--deep` / `--fix`） | `python tools/kb_lint.py --quick` |
| `kb_lint_deep.py` | 扩展检查族 A–F（由 `kb_lint --deep` 调度；也可 `--selftest`） | `python tools/kb_lint_deep.py --selftest` |
| `kb_toolcheck.py` | **实跑**每个工具的 `--selftest`/`--help` + 编译 + 写盘防呆 | `python tools/kb_toolcheck.py` |
| `kb_stats.py` | 知识库统计仪表板 | `python tools/kb_stats.py` |
| `kb_cite.py` | GB/T 7714 引用格式化 | `python tools/kb_cite.py --page sources/xxx.md` |
| `kb_selftest.py` | 底座不变量自检（frontmatter/换行/出链/QC 目录解析） | `python tools/kb_selftest.py` |
| `lit_doctor.py` | **文献流水线体检**（46 项：配置/去重对账/欠账/索引/双运行时/任务） | `python tools/lit_doctor.py`（`--fix` 安全修复） |
| `lit_daily.py` | 每日发现（配置驱动、可续跑、退出码 0/2/3/4） | `python tools/lit_daily.py --resume` |
| `lit_discover.py` | 单方向检索（tier 阈值、分片并行、`cursor` 翻页） | `python tools/lit_discover.py "<查询>" "近一周" --limit 20` |
| `lit_digest.py` | 每日摘要渲染与勾选（取代三段手工 JSON） | `python tools/lit_digest.py --pick "battery#1"` |
| `lit_fetch.py` | 取 OA 全文（**自动串 `lit_si`**：有 SI 就取，取不到进清单；全失败退 4） | `python tools/lit_fetch.py --in <picks.json> --outdir raw/pdf` |
| `lit_si.py` | **SI 存在性判定 + 自动获取**（判据只认原文；Nature/Elsevier/Wiley 可自动） | `python tools/lit_si.py scan "<pdf>"` ／ `fetch "<pdf>" --apply` |
| `lit_browser_fetch.py` | **浏览器兜底**：真实 Edge + 类人鼠标过验证，补正文与 SI（默认干跑；0/3/4/2） | `python tools/lit_browser_fetch.py --latest --apply --import` |
| `lit_manual_import.py` | 手工下载 PDF 收编入库（DOI 匹配+改名+台账） | `python tools/lit_manual_import.py` |
| `lit_batch.py` | 批量提取/建卡的欠账台账（单篇失败不中断整批） | `python tools/lit_batch.py --status` |
| `lit_extract.py` | 单 PDF 图文提取（原子写；`--json` 产物报告） | `python tools/lit_extract.py "<pdf>" --json` |
| `lit_ingest.py` | 建卡骨架 **＋ 骨架门禁**（退出码 0/1/2 有语义） | `python tools/lit_ingest.py --all-text --apply` |
| `lit_finish.py` | 入库收尾（index.md 行 / log_ops.md / 索引） | `python tools/lit_finish.py --since 2026-10-09 --apply` |
| `lit_gapscan.py` | 缺口扫描 → 下一轮检索式（带出处与信号） | `python tools/lit_gapscan.py --queries` |
| `lit_catalogue.py` | 去重目录构建（缓存增量；缩水 >5% 拒绝覆盖） | `python tools/lit_catalogue.py --stats` |
| `lit_journals.py` | 期刊白名单维护（多学科池、按名解析 ISSN、调 tier） | `python tools/lit_journals.py --list` |
| `kb_dois.py` | 库内 DOI 清单（去重键之一；缓存增量） | `python tools/kb_dois.py` |
| `qc_base_check.py` | 五个 `.base` 选中集合重算 + 漂移守门 | `python tools/qc_base_check.py --check` |
| `qc_proj_sources.py` | 项目卡字段门禁（165/165 PASS 基线） | `python tools/qc_proj_sources.py --dir projects/myproj-review/sources` |
| `qc_proj_names.py` | 项目卡 ↔ PDF/Extract/SI **命名归属矩阵**（只读；stem/完整标题/DOI/词元/首页标题多判据） | `python tools/qc_proj_names.py --project projects/myproj-review` |
| `qc_proj_assets.py` | 项目 Extract **图片链接审计**（只读；括号配平解析，不用 `[^)]+`） | `python tools/qc_proj_assets.py --project projects/myproj-review` |

> ⚠️ **运行产物落点 2026-10-10 起**：`raw/notes/lit-watch/`（配置键 `paths.runs_dir`，
> 经 `kb_lib.lit_runs_dir(cfg, 子目录)` 派生）。`_archive/lit-watch/lit-runs/` 只剩一次性历史件。
> 详表见 skill `lit-watch` 的「产物去哪了」一节。

---

### kb_lib.py — 共享库

被其他工具导入的公共函数库，不直接运行。

主要功能：
- YAML frontmatter 解析（轻量实现，不依赖 pyyaml）
- 中文分词（jieba）+ 英文/化学式切分
- 别名映射构建
- 字段加权 token 计算

---

### kb_build_index.py — 索引构建

产出文件到 `wiki/.index/`：
- `meta.json` — **AI 查询整份读入**的元数据（2026-10-15 实测 939 KB）
- `meta_fm.json` — 🆕 预取的 frontmatter 限定词（`source_reliability` /
  `evidence_base` / `si_status`），**检索层按需加载**（247 KB）。刻意与 `meta.json`
  分开：后者是每次查询整份读入的文件，内嵌这 247 KB 会让它 +26%
- `meta_full.json` — 内部版（含出链/hash/fm，工具专用）
- `bm25.json` — BM25 倒排索引
- `meta_lite.json` — 精简索引。⚠️ **目前没有任何工具读它**（仅 `kb_stats` /
  `kb.py --doctor` 列其大小）。实测 712 KB —— 旧文档写的「<500KB」是**失效声明**，已更正。
  按本工具链「已声明 ≠ 已生效」纪律：别把这份未接线的设计当成正在起作用的功能。

```bash
python tools/kb_build_index.py            # 增量构建（只重算变化的页面）
python tools/kb_build_index.py --full     # 全量重建
python tools/kb_build_index.py --lite     # 额外生成 meta_lite.json（无消费者，见上）
python tools/kb_build_index.py --embed    # 同时构建嵌入索引
python tools/kb_build_index.py --stats    # 只打印统计
python tools/kb_build_index.py --add sources/新论文.md  # 增量添加指定页面
```

---

### kb_search.py — 旧检索兼容层

新调用用 `kb.py search/ask`。旧脚本支持三种模式：
1. **BM25**（旧脚本默认）：中文分词 + 字段加权 + 别名扩展
2. **语义**（`--semantic`）：嵌入向量余弦相似度
3. **混合**（`--hybrid`）：BM25 + 语义 RRF + 强制本地 CrossEncoder 精排

```bash
python tools/kb_search.py "固态电解质 界面 稳定性"
python tools/kb_search.py "SSE 水解" --type concept,entity
python tools/kb_search.py "MEE 极性指数" -k 5 --json
python tools/kb_search.py --resolve "SSE"              # 只做别名解析
python tools/kb_search.py --stats                       # 索引概览
python tools/kb_search.py --semantic "固态电解质界面"    # 语义检索
python tools/kb_search.py --hybrid "锂沉积效率"          # 混合检索
```

---

### kb_semantic_search.py — 语义检索

独立语义检索引擎，支持 sentence-transformers（首选）或 scikit-learn TF-IDF+SVD（降级）。

```bash
python tools/kb_semantic_search.py --build              # 构建嵌入索引
python tools/kb_semantic_search.py --add PAGE ...       # 增量更新
python tools/kb_semantic_search.py --query "固态电解质"  # 语义检索
python tools/kb_semantic_search.py --hybrid "锂沉积"     # 混合检索
```

依赖：`pip install sentence-transformers` 或 `pip install scikit-learn`

---

### kb_backlinks.py — 链接图分析

分析 wiki 链接图，找出孤立页面，生成补链建议。

```bash
python tools/kb_backlinks.py              # 概览：链接图统计 + 孤立页面
python tools/kb_backlinks.py --suggest    # 为孤立页面生成补链建议
python tools/kb_backlinks.py --suggest --type concept   # 只处理某类页面
python tools/kb_backlinks.py --page 固态电解质          # 查某页的入站/出站
```

---

### kb_lint.py — 分级 Lint

质量检查工具，分 Quick/Deep 两种模式。

```bash
python tools/kb_lint.py --quick                          # 最近 7 天 ingest 的页面
python tools/kb_lint.py --quick --days 3                 # 最近 3 天
python tools/kb_lint.py --quick --topic "锂金属电池"      # 指定主题
python tools/kb_lint.py --quick --pages sources/xxx.md    # 指定页面
python tools/kb_lint.py --deep                           # 全库深度检查
python tools/kb_lint.py --deep --json                    # JSON 输出
```

检查项：frontmatter 完整性、source 页专项、wikilink 有效性、出度/入度、warning 标记、entity 深度、topic 覆盖、index 一致性、重复别名、交叉引用密度、孤立页面、日志一致性。

---

### kb_stats.py — 统计仪表板

快速查看知识库整体健康状况。

```bash
python tools/kb_stats.py              # 完整统计概览
python tools/kb_stats.py --json       # JSON 格式输出
python tools/kb_stats.py --top 20     # 列出前 20 项
python tools/kb_stats.py --tags       # 详细标签分布
python tools/kb_stats.py --orphans    # 仅显示孤立页面
```

---

### kb_cite.py — GB/T 7714 引用格式化

从 wiki source 页生成标准引用字符串。

```bash
python tools/kb_cite.py --page sources/2022-示例卡片-示例期刊.md
python tools/kb_cite.py --page 2020-自主移动机器人化学家-Nature
python tools/kb_cite.py --authors "Kim S.C.; Oyakhire S.T.; Cui Y." \
    --year 2022 --title "Data-driven electrolyte design" --journal PNAS
python tools/kb_cite.py --page sources/xxx.md --copy    # 复制到剪贴板
```

输出示例：
```
[1] KIM S C, OYAKHIRE S T, CUI Y. 示例论文标题[J]. PNAS, 2022.
    DOI:10.1073/pnas.2214357120
```

---

## 依赖

- **必需**：Python 3.10+
- **检索分词**：`pip install jieba`
- **语义检索与本地精排（hybrid 必需）**：`pip install sentence-transformers`
- **纯语义检索的降级后端**：`pip install scikit-learn numpy`（不允许冒充 hybrid 精排）
- **PDF 提取**：`pip install PyMuPDF`
- **剪贴板**：`pip install pyperclip`（可选，用于 kb_cite.py --copy）

---

## 命名规范

所有主工具链文件遵循：
- 前缀：`kb_`
- 分隔符：下划线（非连字符）
- 后缀：`.py`
