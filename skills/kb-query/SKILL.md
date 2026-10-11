---
name: kb-query
description: 在本知识库里检索并回答问题（分层证据、多跳推理、原文回指）。用户提出任何需要库内证据的问题、要求“查一下库里怎么说”“这个结论有几篇文献支撑”“对比几种说法”“找原文出处”时使用。先 kb_route 分层召回，再按需展开；不要先读 index.md 全表。
---

# 库内检索与作答

工作目录为库根。**首选入口是 `kb_route.py`**，不要手工 grep，也不要先读 `wiki/index.md` 全表。

## 第一原则：先分层，再排序

```bash
python tools/kb_route.py "固态电解质 界面 稳定性"           # L1 综合 / L2 文献卡 / L3 原文
python tools/kb_route.py "<查询>" --budget 5,5,8 --json    # 机器可读
python tools/kb_route.py "<查询>" --layer 1                # 只要综合层
```

| 层 | 内容 | 证据地位 |
|---|---|---|
| L1 | concept / entity / topic | **本库的当前综合**——二手概括 |
| L2 | source | **单篇论文的主张** + `source_reliability` |
| L3 | raw 全文块 | **原文字面表述**，可回指 `文件:行号` |

🔴 **混排会让 Agent 把二手综合当一手证据引用**。引用 L1 时必须意识到它需要 L2/L3 支撑。
留意 `signal.top_score` 与 `low_confidence`：**BM25 没有分数下限，任何查询都会凑满 k 条**；
普遍低分应视为**知识空白**，而不是硬答。

## 常驻服务是前提，不是优化项

实测（583 页）：真正的计算是亚毫秒级，99.9% 时间花在每次进程启动重做初始化上。

| 模式 | CLI 冷启动 | 经常驻服务 |
|---|---|---|
| BM25 | 820 ms | **177 ms** |
| 语义 | 30,162 ms | **231 ms** |
| 混合 | 56,026 ms | **480 ms** |

一次「查询分解 + 多跳 + 交叉比对」要 5–20 次检索 ⇒ 用 CLI 是 5–19 分钟纯等待。

```bash
python tools/kb_serve.py --port 8791 --warm   # 放后台启动
python tools/kb_serve.py --status | --stop
python tools/kb.py --doctor                   # 环境与索引自检
```

## 工具选择

| 需求 | 命令 |
|---|---|
| 分层上下文包（默认首选） | `kb_route.py "<q>" --json` |
| BM25 / 语义 / 混合 | `kb_search.py "<q>" -k 10`，加 `--semantic` / `--hybrid` |
| 术语归一 | `kb_search.py --resolve "<术语>"` |
| 限定类型 | `kb_search.py "<q>" --type concept,entity` |
| **原文级别检索（可回指行号）** | `kb_corpus.py --search "<q>"` |
| 多跳推理链 | `kb_graph.py --path A B`；`--neighbors PAGE --hops 2`；`--bridges`；`--hubs` |
| 断言「库里没有 X」 | `kb_where.py "X"`（**必跑**，见下） |

`kb_search.py` 支持别名自动解析（查 `SSE` → `固态电解质`）。

## 检索-验证-综合循环

1. **检索**：`kb_route.py` 分层召回（L1+L2；需要原文佐证再加 L3）
2. **验证**：读 L2/L3 随结果返回的 `source_reliability` / `evidence_base` / `si_status`
3. **交叉比对**：多个 source 对同一数据/结论比对，标注一致或分歧
4. **单源即标**：仅一篇支撑的结论必须写 `> ⚠️ 单源论断：...`
5. **需要更多证据**：`kb_corpus.py --search` 拿 L3 原文块

### 自适应检索深度

| 问题类型 | 策略 |
|---|---|
| 简单事实（定义、数值） | `--layer 1` 读 L1 top-3 |
| 综合分析（机制对比、趋势） | L1 top-5 + L2 top-5 |
| 争议性 / 前沿 | L1 + L2 + **L3 原文**，逐一标注各方立场与证据强度 |
| 核对「页面数字是否忠于原文」 | 必须走 `kb_corpus.py` 拿 L3，**不要靠 grep** |

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

## 上下文预算

- 优先 `--json` 取精简结果，**按需**再读具体页面全文
- `meta_lite.json`(461 KB) 用于浏览；`meta.json`(567 KB) 仅在需要完整元数据时读
- L3 语料索引较大（chunks 62 MB + bm25 43 MB），**只在前两层不足以回答时才启用**

## 作答后

有长期价值的回答，询问用户是否保存到 `wiki/outputs/`；并追加 `wiki/log_ops.md`。
