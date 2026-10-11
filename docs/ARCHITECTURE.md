# 架构

## 数据分层

```
<vault>/
├── wiki/            知识层（你会不断长大的一层）
│   ├── concepts/ entities/ sources/ topics/ outputs/
│   ├── index.md tags.md log_ops.md log_insights.md
│   └── .index/      派生索引（可重建，已 gitignore）
├── raw/             资料层（一手资料；工具**只读**不写）
│   ├── pdf/ text/ clippings/ assets/ notes/
├── tools/           工具层（kb_*.py 检索 / lit_*.py 文献流水线）
├── projects/        工程层（可选）
└── _archive/        归档（只移不删）
```

**关键区分**：`wiki/` 是**知识**（人/AI 维护、进 git）；`raw/` 是**资料**（原始、只读）；
`wiki/.index/` 是**派生数据**（可随时重建，不进 git）。

## 检索链路

```
kb_build_index.py  →  wiki/.index/{meta,meta_full,bm25,lite}.json
kb_semantic_search.py --build  →  embeddings.npy（可选）
kb_corpus.py --build  →  .index/corpus/（raw 全文块）

            ┌── kb_search.py     BM25 / 语义 / 混合
查询 ───────┼── kb_route.py      分层 L1(综合)/L2(文献卡)/L3(原文)  ← 首选
            └── kb_corpus.py     原文块检索（可回指 文件:行号）
```

`kb_route` 的三层**不混排**：L1 是「本库的综合」（二手），L3 是「某篇论文某一段」（一手），
可信度不同，混排会让 AI 把二手综合当一手证据。

## 文献流水线（lit-watch）

```
lit_discover  →  lit_fetch  →  lit_extract  →  lit_ingest  →  lit_finish
   OpenAlex        OA 全文        PDF→md/图       建卡骨架        收尾
                 (Unpaywall)                  + 骨架门禁     index/log/索引
```
配置唯一来源 `tools/lit_config.yaml`（路径一律相对库根）。每日无人值守由
`lit_daily.py` 驱动，调度放在 **OS 侧**（cron / Task Scheduler），**不在 MCP 范围**。

## 空库与索引（一个关键设计）

`kb_build_index.py` 在**0 页面**时也会写出**合法的空索引**（`count:0` / `n_docs:0` / schema 一致）。
因此：
- 全新空库 `kb_search` 返回「0 命中」，**不会** `exit(2)`；
- `kb_route` / `kb_serve` 等依赖索引的入口在空库下也优雅退化。

若索引**缺失**（不是空），`kb_search.load_index()` 仍会明确报错提示你重建——
这是刻意的：**「索引存在但为空」和「索引不存在」是两回事**，后者是真故障，
用静默的空结果掩盖它比报错更危险。

## 为什么工具不写死库路径

所有工具用 `os.path.dirname(os.path.dirname(os.path.abspath(__file__)))` 派生库根
（`tools/kb_lib.py:VAULT`）。于是整个库目录可随意改名、迁移、复制，工具无需改一行。

## MCP

`mcp/server.py` 以 subprocess 调用库自己的 CLI（`python tools/<脚本>.py ... --json`），
所以你无需常驻服务——若你另外起了 `kb_serve`，它会被 `kb.py` 自动优先使用（加速），
否则退化为进程内。写工具需 `--allow-write` + 调用方 `apply=true` 双钥。
