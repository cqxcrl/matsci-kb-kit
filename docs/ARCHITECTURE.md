# 架构

## 数据分层

```
<vault>/
├── wiki/            知识层（你会不断长大的一层）
│   ├── concepts/ entities/ sources/ topics/ outputs/ experiments/
│   ├── index.md tags.md log_ops.md log_insights.md
│   └── .index/      派生索引（可重建，已 gitignore）
├── raw/             资料层（一手资料；工具**只读**不写）
│   ├── pdf/ text/ clippings/ assets/ notes/
├── tools/           工具层（kb_* 检索 / lit_* 文献流水线 / qc_* 质检 / sci_* 决策）
├── projects/        工程层（可选）
└── _archive/        归档（只移不删）
```

**关键区分**：`wiki/` 是**知识**（人/AI 维护、进 git）；`raw/` 是**资料**（原始、只读）；
`wiki/.index/` 是**派生数据**（可随时重建，不进 git）。

`wiki/experiments/` 是唯一**由工具写入**的知识层子目录：
`sci_protocol_gen.py --export-experiment <METHOD_ID>` 把审核过的实验方案落成
`type: experiment` 页，这样它也能被检索到。其余知识页由人/AI 写。
类型→目录的映射只有一份（`kb_lib.TYPE_DIR`），`kb_selftest` 断言它与 `PAGE_DIRS` 一致。

## 检索链路

```
kb_build_index.py  →  wiki/.index/{meta,meta_full,bm25,lite}.json
kb_semantic_search.py --build  →  embeddings.npy（可选）
kb_corpus.py --build  →  .index/corpus/（raw 全文块）

            ┌── kb_rag.py        传统 RAG：BM25 / 向量 / RRF 融合 / CrossEncoder 精排
查询 ───────┼── kb_agentic.py    Agentic RAG：规划 → 分层检索 → 图扩展 → 停止判据
            ├── kb_route.py      分层 L1(综合)/L2(文献卡)/L3(原文)  ← 取证首选
            ├── kb_search.py     检索原语（被上面几个复用）
            └── kb_corpus.py     原文块检索（可回指 文件:行号）

kb.py 是这些的统一 CLI 入口（ask / search / route / corpus / index / serve / …），
并兼容旧的裸查询与 --route / --corpus / --resolve 写法。
```

`kb_route` 的三层**不混排**：L1 是「本库的综合」（二手），L3 是「某篇论文某一段」（一手），
可信度不同，混排会让 AI 把二手综合当一手证据。

### 一条硬规则：hybrid 不静默降级

`kb_rag.retrieve()` 的默认 `mode="hybrid"` 同时要求①嵌入索引②本地 Reranker
（`sentence-transformers` 的 CrossEncoder）。任一缺失就抛 `RetrievalUnavailable`
→ CLI **退出码 3**，而**不是**悄悄退回 BM25。

> 为什么这么设计：静默降级会让调用方以为拿到了融合+精排的结果，实际只有 BM25。
> 在「证据承重」的方法论下，这种假成功比报错危险得多。
> 依赖不全时的正确写法是**显式** `--mode bm25`——意图写在命令行里，不靠猜。

Reranker 默认**只读本地模型**；首次下载必须显式加 `--allow-download`，
避免在离线/受控环境里意外联网。

## 质检层（qc_*）

质检不是一套 lint 的别名，而是三类不同的判据：

| 类 | 工具 | 判什么 |
|---|---|---|
| **结构** | `qc_schema_check` `qc_base_check` | frontmatter 合不合法；Bases 视图的选中集合有没有被**静默收窄** |
| **证据** | `qc_evidence_base` `qc_evidence_audit` `qc_evidence_note` `qc_sources_drift` `qc_si_backfill` | 一个论断的**承重等级**（一手/二手/单源），以及 `sources:` 有没有语义漂移 |
| **工程** | `qc_proj_sources` `qc_proj_names` `qc_proj_assets` | `projects/*/` 内的卡片、命名矩阵与图片链接（只读审计） |

共同纪律：**默认干跑**，`--apply` 才写；写前备份、写后复算。
判断（哪页该补源、哪页该降级）由人/模型给 decisions JSON，**工具只重算数字、不猜结论**。

## 文献流水线（lit-watch）

```
lit_discover → lit_digest → lit_fetch → lit_extract → lit_ingest → lit_finish
  OpenAlex      摘要/勾选     OA 全文     PDF→md/图     建卡骨架      收尾
              (Unpaywall)                            + 骨架门禁   index/log/索引
                    │                                     │
                    ├─ lit_si            补 SI（判据只认 PDF 声明句式）
                    ├─ lit_browser_fetch 反爬站点兜底（真实浏览器，可选依赖）
                    ├─ lit_manual_import 手工下载收编
                    └─ lit_enrich        建卡后的**证据化**二次加工（quote 机械校验）
```
配置唯一来源 `tools/lit_config.yaml`（路径一律相对库根）。每日无人值守由
`lit_daily.py` 驱动，调度放在 **OS 侧**（cron / Task Scheduler），**不在 MCP 范围**。

**退出码是信号，不是成败**：`lit_fetch` 4 = 全部下载失败；`lit_si` 4 = 有 SI 但一份没取到；
`lit_ingest` 2 = 页面写好了但**补链没做完**；`lit_gapscan` 1 = 索引读不到、权重已失真。
把非 0 一律当"失败"或一律当"成功"都会做错决定。

## 空库与索引（一个关键设计）

`kb_build_index.py` 在**0 页面**时也会写出**合法的空索引**（`count:0` / `n_docs:0` / schema 一致）。
因此：
- 全新空库 `kb_search` 返回「0 命中」，**不会** `exit(2)`；
- `kb_route` / `kb_serve` 等依赖索引的入口在空库下也优雅退化。

若索引**缺失**（不是空），`kb_search.load_index()` 仍会明确报错提示你重建——
这是刻意的：**「索引存在但为空」和「索引不存在」是两回事**，后者是真故障，
用静默的空结果掩盖它比报错更危险。

> 同一条原则也解释了上面的 hybrid 不降级：**空结果是合法状态，缺依赖不是**。

## 为什么工具不写死库路径

所有工具用 `os.path.dirname(os.path.dirname(os.path.abspath(__file__)))` 派生库根
（`tools/kb_lib.py:VAULT`）。于是整个库目录可随意改名、迁移、复制，工具无需改一行。

## MCP

`mcp/server.py` 以 subprocess 调用库自己的 CLI（`python tools/<脚本>.py ... --json`），
所以你无需常驻服务——若你另外起了 `kb_serve`，它会被 `kb.py` 自动优先使用（加速），
否则退化为进程内。写工具需 `--allow-write` + 调用方 `apply=true` 双钥。

工具清单不手写：`kb_manifest.py` 用 AST **静态**扫出每个工具的参数、默认值与
「推荐用哪个 `kb.py` 子命令」（**不导入、不执行**被扫描脚本），`kb.py tools` 据此输出
机器可读清单，给 Agent 自己发现能力用。

`mcp/tools.yaml` 是另一回事：它只是**人读副本**，真源是 `mcp/server.py` 的 `TOOLS`
注册表。加 MCP 工具要改 `server.py`，改 `tools.yaml` 不会生效。

