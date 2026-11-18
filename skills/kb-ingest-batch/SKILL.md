---
name: kb-ingest-batch
description: 综述工程 综述工程的「批次 ingest」编排工具链（台账查询、批次编排、批次收尾、批次文件 v1/v2 格式）。当需要在 <你的库根> 里查 ingest 进度、列出某批篇目、操作 batches_v2.json / batch_done.json、或执行 batch_close 时使用。⚠️ 该工程 64/64 批已于 2026-09-26 全部完成，本技能现为「按需复现/新增批次」用途。
---

# 批次 ingest 编排（第二工具链）

工具目录 `projects/综述工程/ingest/tools/`，工作目录为库根。
**这套工具链不在 `tools/` 下，`CLAUDE.md` 的检索层工具表也不含它们。**

> ⚠️ **状态**：LEDGER.md 载明本 ingest 工程 **64/64 批已于 2026-09-26 全部完成**，
> 新会话**不必再读 LEDGER.md**（曾膨胀到 356 KB，一次会话要灌 55–96 KB）。
> 本技能用于「日后新增文献要重跑批次」或「复现历史流程」。

## 🔴 运行前必读

**本项目部分脚本未实现 argparse**：传 `--help` 不会被识别，而是**直接执行主逻辑**。
`plan_batches_v2.py` 就是一例——它会**覆盖写入** `batches_v2.json`。运行任何脚本前先读源码。

## 三个脚本的职责

| 脚本 | 职责 | 是否写盘 |
|---|---|---|
| `ledger_status.py` | **只读**查询台账 | ❌ |
| `plan_batches_v2.py` | 从 `classification_state.json` **重新编排批次** | 默认干跑；`--apply` 才覆盖 `batches_v2.json` / `.md` |
| `batch_close.py` | 批次收尾：索引重建 + 页校验 + 写日志 + 标记完成 | 默认干跑；`--apply` 才写盘 |

### ledger_status.py（只读，优先用它）

```bash
python "projects/综述工程/ingest/tools/ledger_status.py"            # 下一批 + 总进度（<400 字节）
python ".../ledger_status.py" --batch N14    # 该批篇目清单（md 名 / 标题 / DOI / 字节）
python ".../ledger_status.py" --pending      # 所有未完成批次（编号/篇数/字节）
python ".../ledger_status.py" --check        # 实测建卡数（扫 wiki 回链，权威口径）
```

**它的存在理由**：把「读整个台账」变成几十字节的结构化查询。

⚠️ 已知偏差：`--check` 依赖 `classification_state.json` 的 `bak` 列表与
`raw/AI for Materials literatures Base/literatures-md` 回链；若 raw 目录结构变动，
它会报「已建卡 0」而与 LEDGER 的「183/183」矛盾——此时**以 LEDGER/页面实况为准，并怀疑该工具**。

### plan_batches_v2.py（编排，会覆盖）

输入 `classification_state.json`。规则：只对未建卡者编批；按 tier 分组不混；tier 内按 class 聚类、
class 内按字节升序；每批 ≤300 KB 且 ≤6 篇；单篇 >250 KB 独批。
T1 类集 `{A1,A5,A13,A14,A15,A′,C3,A9,A7,A10}`，其余为 T2。输出 `batches_v2.json` / `batches_v2.md`。

**仅在确实要重新编批时运行**。默认干跑（打印编排结果但不写盘）；确认无误后加 `--apply`，
覆盖前仍建议备份现有 `batches_v2.json`。

### batch_close.py（收尾）

```bash
python ".../batch_close.py" --batch N14 --pages 2026-xxx 2026-yyy --log "完成 N14（3/3，T1，A10）" --apply
python ".../batch_close.py" --batch N14 --check-only      # 只校验，不写任何文件
python ".../batch_close.py" --batch N14                   # 干跑：校验但不动索引/日志/台账
```

做三件事（幂等）：
1. **索引重建**：调 `tools/kb_build_index.py`
2. **校验本批新建页**，红旗判据：
   - 🔴 raw 回链缺引号（`- "[[raw/...]]"` 必须有外层引号）
   - 🔴 出链 < 2
   - 🔴 无入站链接
   - 🔴 缺 `## 批判性评估`
   - 🟠 缺 `## 诚实边界`；🟠 ⚠️ 标记数 0
3. **写日志 + 标记完成**：追加 `wiki/log.md`；把批次号写入 `batch_done.json`（**权威源**）；
   同步更新 `LEDGER.md` 的单批行（区间合并行不动）

未给 `--pages` 时从 `batches_v2.json` 反查带该 md 回链的 wiki 页。

⚠️ **两处已知缺陷**（`batch_close.py`）：
- `TODAY = "2026-09-20"` 是**硬编码日期**——每条日志都会写成该日期，与实际执行日不符。
- 它追加的是 `wiki/log.md`，而 `CLAUDE.md` §日志与更新协议 明确写「`wiki/log.md` 是**历史存档**，不再追加新内容」，
  并要求 `batch_close` 同时写 `log_ops.md` 与 `log_insights.md`。**两者矛盾，以 CLAUDE.md 的协议为准**，
  即收尾后需手动补 `log_ops.md` 条目。

## 批次文件格式

| 版本 | 文件 | 状态 |
|---|---|---|
| v1 | `batches_v1.json` / `archive_v1/batches.json` | **已废弃**，只读不写 |
| v2 | `batches_v2.json` | **当前格式** |
| 概览 | `batches_v2.md` | Markdown 表格视图，与 v2 同步维护 |
| 完成记录 | `batch_done.json` | 已完成批次 ID 数组，**权威源** |

**v2 批次对象**：`{id, tier, n, bytes, classes[], items[]}`，
`items[]` 每项 `{md, title, doi, cls, cat}`。

**操作前检查清单**：
1. 确认 `batches_v2.json` 存在；不存在则查 `batches_v1.json` 并提示需迁移
2. 读文件后按是否含 `tier`/`classes`/`items` 判定 v1/v2
3. **禁止混用**：不得把 v1 条目写入 v2，也不得把 v2 降级为 v1
4. 新批次一律 v2，必须含完整 `tier`/`classes`/`items`（含 `doi`）
5. `batch_close` 时**同时**更新 `batches_v2.json`（标记状态）与 `batch_done.json`（追加批次 ID）

## 一次完整批次的操作序列

1. `ledger_status.py` 看下一批 → `--batch Nxx` 取篇目
2. 逐篇按 KB `CLAUDE.md` §Ingest 8 步建卡（批判性三层结构；结论只能来自实读原文）
3. `batch_close.py --batch Nxx --check-only` 先校验
4. 修掉红旗项后 `batch_close.py --batch Nxx --log "..." --apply` 收尾
5. 手动补 `wiki/log_ops.md` 条目（见上文缺陷说明）
