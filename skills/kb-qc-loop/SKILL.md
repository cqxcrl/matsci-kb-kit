---
name: kb-qc-loop
description: 在 <你的库根> 上推进、查看或暂停「知识库 QC 质量核查」串行循环——核查 ingest 产物里原文不存在的数字与结论。用户提到 qc_status.py、批次队列、LEDGER、进度看板、每 tick 推一批、防限流、上批是否还在跑时使用。含每 tick 五步顺序、串行与单批 ≤12 页的不变量、五级判定与假阴性归一化纪律。
---

# 知识库 QC 质量核查循环

> 库根 `<你的库根>`（Windows），下列命令均在该目录下执行。
> 依据：`references/protocol.md`（随包发布的通用批次协议骨架）、
> `tools/qc_status.py`、`tools/qc_ledger.py`、`tools/qc_batch_progress.py`、
> 库根 `.qc/{LEDGER.md,queue.json}`（QC 工作目录解析见 `kb_lib.qc_work_dir`）。

## 不变量

- **一次只跑一个 agent**：早期版本曾并行多个 agent 触发 API 限流被中断，仅少量页面落盘；后改为串行。
- **单批页数 ≤ ~12 页**（实测单次处理 12–15 页不超上下文）——protocol.md §批次与限流。
- **绝不并行启动多个 agent**。
- 循环目标：核查 ingest 产物里**原文不存在的数字/结论**（protocol.md §核心任务）。

## 每 tick 的动作顺序（protocol.md）

1. 读 `.qc/queue.json` 与 `.qc/LEDGER.md`，找**第一个未完成**的批次。
2. 读该批次的页面清单。
3. **启动 1 个 agent**（后台运行）执行该批次。
4. 在 `.qc/LEDGER.md` 把该批次标为 🔄。
5. 本轮结束；下次唤醒时检查其落盘结果并标 ✅。

## 命令

| 目的 | 命令 |
|---|---|
| 查看进度（打印看板） | `python tools/qc_status.py` |
| 刷新进度看板（写文件） | `python tools/qc_status.py --write` |
| 机器可读进度 | `python tools/qc_status.py --json` |
| 看板/队列解析自检 | `python tools/qc_status.py --selftest` |
| 追加台账条目（幂等） | `python tools/qc_ledger.py --file <文本文件> [--key "<幂等判据>"]` |
| 只判定不写盘 | `python tools/qc_ledger.py --text "<正文>" --dry-run` |
| 批次完成度快照 | `python tools/qc_batch_progress.py`（写 `.qc/batch_progress.json`） |
| 查某页入站链接（下游检查） | `python tools/kb_backlinks.py --page <页面名>` |

**节奏**：建议用**会话级 cron 每 25 分钟唤醒一次**，每 tick 推进一个批次，
约 10 轮 × 25 min ≈ 4–5 小时（protocol.md §批次与限流）。
> 不要自定义更高频节奏（如「每 8 分钟一 tick」）——以 25 分钟口径为准，除非用户明确要求提速。

**停止**：全部批次 ✅ → 进入汇总阶段（报告 + 索引重建 + 日志）→ 删除 cron 任务（protocol.md §停止条件）。

## 限流 与「上批是否仍在运行」

- **若发现已有 agent 仍在运行 → 不要启动新 agent，直接结束本轮，等下次唤醒**（protocol.md）。
- 某批被限流中断 → **下一 tick 重跑同一批次，并把该批拆成两半**（protocol.md §批次与限流）。
- **死亡判定靠 tick 计数（stall）**：建议 4 tick 无落盘进展即判死亡并重跑；产物 `.qc/last_tick.json`
  （已评分页数 + 停滞计数），递增/清零规则由调度方定义并写进台账（protocol.md §批次与限流）。
- **曾有一批在会话中断中死亡且未落盘任何产出**，此后拆成两半重跑——这就是「上批是否仍在运行」必须每 tick 核实的原因。

## 进度看板

- 产出：`wiki/outputs/quality-check-进度看板.md`；刷新 `python tools/qc_status.py --write`。
- 三个数据源：`.qc/queue.json`（队列）、`.qc/LEDGER.md`（🔄/✅ 标记）、
  `wiki/**/*.md` 的 `qc_status` 字段（**最可靠**）。
- 评分口径：扫全库 `qc_status`，值为 `fixed`/`verified` 才计入「已评分」。
- 批次状态只认行内 ✅(done)/🔄(running)/⏳(pending)；同一行多批次用 `||` 拆分。
- ⚠️ **盘上看板可能过期**：要看真实进度**先 `--write` 重跑**。
- 明细表遍历 `queue.json` 的**全部批次键**（顺序动态派生，不写死批次号）。

## 产出落盘

- 页面本身：`wiki/` 下就地修正 + 改 frontmatter `updated` 与 `qc_status: fixed|verified`。
- 看板与总报告：`wiki/outputs/`。
- **QC 工作目录**：新产出写**库根 `.qc/`**；历史归档（如 `_archive/qc-working/.qc/`）**只读回退、绝不写入**
  （解析顺序：环境变量 `MATSCI_QC_DIR` > 库根 `.qc/` > 归档）。
- 备份：`.qc/backups/YYYYMMDD/`、`.qc/ghost_backup_YYYYMMDD/`。
- `qc_ledger.py` 首次追加会把归档台账**复制**到库根 `.qc/LEDGER.md`（不原地改归档）。

## `.qc/` 文件格式（实测）

| 文件 | 结构 |
|---|---|
| `batch_progress.json` | `{批次: {total, graded, done, not_found[]}}` |
| `ai_deps.json` | `[{page, ai[], others[]}]` |
| `si_sweep.json` | `[{page, claimed_none, actual_markers, evidence{raw路径: 计数}}]` |
| `schema_check.json` | 实测为 `[]`；`author_check.json`/`link_wrap.json`/`pdf_doi_cache.json` 同类清单 |

**队列与台账落点**：优先库根 `.qc/`；历史归档（如 `_archive/qc-working/.qc/`）只读回退。
协议骨架见 `references/protocol.md`。

## 判定与纪律（protocol.md）

- 五级：`VERIFIED` / `MISMATCH` / `STRETCHED`（页内强于原文）/ `UNSOURCED`（原文完全没有，最高危）/
  `CANT_CHECK`（raw 缺该部分，必须标出，不得放行）。
- 🔴 不可违反：**禁止凭领域常识判断**；**不得用 kb_search 结果页替代 raw 原文**；数字须在 raw 中**逐词命中**；
  核分母与对象、核因果方向、保留「自报 vs 第三方」属性。
- 🔴 **「0 命中」不等于捏造**：判定前必须排除假阴性形态（千分位/无分隔/细空格 U+2009/英文数词、
  连字 ﬁ ﬂ、分行断字、标点形态、小数点空格化）。
  **归一化顺序强制**：先 `\r\n`→`\n`，再删 `-\n`，并同时处理 `- `
  （顺序错则整批断字漏配，引号命中率显著下降）。
- **改完 source 页必须查下游**（`kb_backlinks.py`）——上游一个错误实测连带 **3–7 处副本**，常在批次名单之外。
- 批次返回**结构化清单**，每页给出 `raw: / 结论: PASS|FIXED|BLOCKED / issues / fixed_count`。
  完成判据：每页有结论、每处修改能指出 raw 依据、无「未读原文即判定」。
- 两类批次指令模板见 `references/protocol.md`：**证据升级型（二手→一手原文）**、
  **标准证据回溯型**。
- 每个 qc 脚本都带 `--selftest`（已知答案正反例反算）；**写盘脚本改动前先跑自检**
  （已有多次「计数器自己出错」被读成内容质量问题的事故）。
