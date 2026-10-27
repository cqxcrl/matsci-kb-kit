---
name: kb-query
description: 在本知识库里检索并回答问题（传统 RAG、Agentic RAG、分层证据、原文回指）。用户提出需要库内证据的问题、要求比较机制/争议/趋势或核对原文时使用。首选 kb.py ask/search，不要先读 index.md 全表或手工 grep。
---

# 库内检索与作答

工作目录为库根。**统一首选入口是 `kb.py`**；旧 `kb_search.py`、`kb_route.py` 等是兼容层。
先用 `python tools/kb.py tools --json` 查看 AST 静态生成的工具清单，不要凭记忆猜冷门脚本参数。

## 第一原则：先选策略，再分层验证

| 问题 | 规范命令 |
|---|---|
| 定义、术语、单点事实 | `python tools/kb.py ask "什么是固态电解质" --strategy simple --json` |
| 比较、机制、争议、趋势、多子问题、证据核验 | `python tools/kb.py ask "比较 A 与 B 并核对证据" --strategy agentic --json` |
| 不确定 | `python tools/kb.py ask "<问题>" --strategy auto --json` |
| 显式传统检索 | `python tools/kb.py search "SSE 水解" --mode hybrid -k 10 --json` |
| 兼容分层包 | `python tools/kb.py route "<查询>" --budget 5,5,8` |
| 只查原文 | `python tools/kb.py corpus "<原文字段>" -k 8 --json` |

传统 `hybrid` 的顺序是 **BM25 + 向量候选 → RRF → 本地 CrossEncoder → Top-K**；RRF 不等于 Rerank。
精排不可用、索引过期或推理失败时明确失败，不会静默退回 BM25。纯 `--mode bm25` 可用于快速词项排查，
但不能声称经过语义召回或精排。

Agentic 模式是有界的**证据检索器**：默认最多 6 步，支持外部 JSON 子查询计划、图扩展、证据去重和停止原因。
最终综合由调用方模型依据 `synthesis_request` 完成；`ready_for_synthesis` 不等于「已经生成答案」。
外部计划格式为 `{"subqueries": ["子问题 1", "子问题 2"], "reason": "..."}`，用 `--plan plan.json` 传入。

| 层 | 内容 | 证据地位 |
|---|---|---|
| L1 | concept / entity / topic | **本库的当前综合**——二手概括 |
| L2 | source | **单篇论文的主张** + `source_reliability` |
| L3 | raw 全文块 | **原文字面表述**，可回指 `文件:行号` |

🔴 **混排会让 Agent 把二手综合当一手证据引用**。引用 L1 时必须意识到它需要 L2/L3 支撑。
留意 `signal.top_score` 与 `low_confidence`：**BM25 没有分数下限，任何查询都会凑满 k 条**；
普遍低分应视为**知识空白**，而不是硬答。

## 常驻服务与本地精排

多次检索应使用常驻服务，避免每次进程重复初始化模型：

```bash
python tools/kb.py serve start --warm
python tools/kb.py serve status
python tools/kb.py serve stop
python tools/kb.py doctor --check-reranker
```

CLI 默认优先走服务，只有连接失败才在进程内执行；**HTTP 400/503 是真实错误，不会当成离线重试**。
`--no-server` 可显式绕开服务。端点包括 `/ask`、`/search`、`/route`、`/corpus`、`/resolve`、`/graph`。
BM25/meta 索引签名变化会自动重载索引并使图缓存失效；语料缓存也按文件签名重载。

默认精排模型是 `BAAI/bge-reranker-base`，默认只读本地文件；可用 `MATSCI_RERANKER_MODEL` 指定本地模型。
首次下载必须显式 `--allow-download` 或 `MATSCI_RERANKER_ALLOW_DOWNLOAD=1`。
`doctor --check-reranker` 才真正测试加载，仅看配置不算通过。

## 检索-验证-综合循环

1. **检索**：简单问题取传统 Top-K；复杂问题取 Agentic 证据包。
2. **验证**：读 L2/L3 的 `source_reliability` / `evidence_base` / `si_status`，必要时打开原路径核对。
3. **交叉比对**：多个 source 对同一数字/结论比对，标注一致、分歧和适用条件。
4. **单源即标**：仅一篇支撑的结论必须写 `> ⚠️ 单源论断：...`。
5. **需要更多证据**：`kb.py corpus` 拿 L3 原文块，不靠 grep 代替语料检索。
6. **综合**：只依据 evidence 作答；关键结论附路径/行号，`gaps` 非空时明确证据不足。

### 自适应检索深度

| 问题类型 | 策略 |
|---|---|
| 简单事实（定义、数值） | `ask --strategy simple`，先读 Top-3 |
| 综合分析（机制对比、趋势） | `ask --strategy agentic`，保留 supporting_queries |
| 争议性 / 前沿 | Agentic + L3，逐一标注各方立场与证据强度 |
| 核对「页面数字是否忠于原文」 | 必须检查 L3 路径/行号/quote，**不要靠 grep** |
| 多跳关系 | Agentic 默认图扩展；也可用 `kb_graph.py --path A B` 等专用图工具 |

## 🔴 断言「库内无 X」之前必跑 `kb_where.py`

```bash
python tools/kb_where.py "X"
```

它跨**四个目录**检索并**逐目录报告命中数**：`raw/`、`wiki/`、
`projects/综述工程/references/`、`projects/综述工程/`。

**为什么必须**：2026-09-26 有三处独立检索都断言某篇全文不在库内，且都「写明了检索范围」——
但范围只有 `raw/`+`wiki/`，而全文一直在 `references/` 里。
⇒ **「已声明范围」≠「范围完备」**；缺省值最危险，因为它从不被写出来、因而不被审查。
对「缺失」的断言，证据强度天然低于对「存在」的断言：`grep → 0 命中` 只能证明「在我搜过的地方没有」。

## 索引维护与上下文预算

修改知识页或 raw 后按影响面刷新：

```bash
python tools/kb.py index build
python tools/kb.py index embed
python tools/kb.py index corpus
python tools/kb.py doctor
```

嵌入索引检查页面缺失/幽灵和同名内容哈希；语料索引逐文件检查 SHA-256。不要删哈希清单或放宽检查来让旧索引通过。
优先 `--json` 取精简结果，按需再读具体页面全文；L3 索引很大，只在前两层不足或必须原文核验时启用。

## 作答后

有长期价值的回答，询问用户是否保存到 `wiki/outputs/`；并追加 `wiki/log_ops.md`。
