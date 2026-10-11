


>
> 📚 **配套文档**（2026-10-11 从 CLAUDE.md 析出，CLAUDE.md 只留指针）：
>
> 🔧 **文献流水线（lit-watch）**：引擎是 `tools/lit_*.py`（2026-10-10 扩容：新增体检、摘要勾选、
> 手工收编、批量台账、入库收尾、每日发现、期刊白名单维护）。

## 主工具链 (tools/)

| 工具 | 用途 | 用法示例 |
|------|------|----------|
| `kb_lib.py` | 共享库（被其他工具导入；DOI 归一、frontmatter 解析/重组、代码剔除、lit 配置加载）。`--selftest` 跑底座不变量 | `python tools/kb_lib.py --selftest` |
| `kb.py` | **检索首选入口**（bm25/语义/混合/分层 route/语料/doctor） | `python tools/kb.py "<问题>" --route` |
| `kb_build_index.py` | 构建/增量更新检索索引 | `python tools/kb_build_index.py` |
| `kb_search.py` | BM25 + 语义 + 混合检索 | `python tools/kb_search.py "固态电解质"` |
| `kb_route.py` | **分层上下文包**（L1 综合 / L2 文献卡 / L3 原文块，不混排） | `python tools/kb_route.py "<问题>" --json` |
| `kb_semantic_search.py` | 语义检索引擎（嵌入向量） | `python tools/kb_semantic_search.py --query "锂金属"` |
| `kb_corpus.py` | raw 全文分块索引与检索（可回指行号） | `python tools/kb_corpus.py --build` |
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
| `lit_fetch.py` | 取 OA 全文（含 SI 尽力抓取；**全失败退 4**） | `python tools/lit_fetch.py --in <picks.json> --outdir raw/pdf` |
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
- `meta.json` — AI 查询用元数据（~400 KB）
- `meta_full.json` — 内部版（含出链/hash，工具专用）
- `bm25.json` — BM25 倒排索引
- `meta_lite.json` — 超精简索引（<500KB）

```bash
python tools/kb_build_index.py            # 增量构建（只重算变化的页面）
python tools/kb_build_index.py --full     # 全量重建
python tools/kb_build_index.py --lite     # 额外生成 meta_lite.json
python tools/kb_build_index.py --embed    # 同时构建嵌入索引
python tools/kb_build_index.py --stats    # 只打印统计
python tools/kb_build_index.py --add sources/新论文.md  # 增量添加指定页面
```

---

### kb_search.py — 检索

支持三种检索模式：
1. **BM25**（默认）：中文分词 + 字段加权 + 别名扩展
2. **语义**（`--semantic`）：嵌入向量余弦相似度
3. **混合**（`--hybrid`）：BM25 + 语义 RRF 融合

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
python tools/kb_cite.py --page sources/2022-数据驱动锂金属电解液设计-PNAS.md
python tools/kb_cite.py --page 2020-自主移动机器人化学家-Nature
python tools/kb_cite.py --authors "Kim S.C.; Oyakhire S.T.; Cui Y." \
    --year 2022 --title "Data-driven electrolyte design" --journal PNAS
python tools/kb_cite.py --page sources/xxx.md --copy    # 复制到剪贴板
```

输出示例：
```
[1] KIM S C, OYAKHIRE S T, CUI Y. 数据驱动锂金属负极电解液设计[J]. PNAS, 2022.
    DOI:10.1073/pnas.2214357120
```

---

## 依赖

- **必需**：Python 3.10+
- **检索分词**：`pip install jieba`
- **语义检索（首选）**：`pip install sentence-transformers`
- **语义检索（降级）**：`pip install scikit-learn numpy`
- **PDF 提取**：`pip install PyMuPDF`
- **剪贴板**：`pip install pyperclip`（可选，用于 kb_cite.py --copy）

---

## 命名规范

所有主工具链文件遵循：
- 前缀：`kb_`
- 分隔符：下划线（非连字符）
- 后缀：`.py`
