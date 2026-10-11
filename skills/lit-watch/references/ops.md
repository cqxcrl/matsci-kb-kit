# lit-watch 运维手册（自动化 · 事故根因 · 双运行时布局）

这份文件记录**为什么**这些工具长成现在这样 —— 每条结论都有 2026-10-09 的实测证据。

---

## 1 · 每日自动发现（无人值守）

### 现状与曾经的事故

- 任务名 `litwatch-daily`，入口原是 `<你的 .claude>\scripts\lit_watch_daily.py`（方向硬编码，`DIRECTIONS`）。
- **2026-10-09 的事故**：`cron.log` 留下

  ```
  [run] battery ...
  [FAIL] battery: rc=3221225786
  [dedup] 去重键共 726 条（本地目录贡献 697，知识库补充 29）
  [检索] 白名单分片 1/2（90 刊）
  [检索] 白名单分片 2/2（12 刊）

  [run] oer-electrocatalysis ...
  ```
  然后**什么都没了**：`daily/2026-10-09/` 是空目录，没有 `cand_*`、没有 digest。
  `rc=3221225786` = `0xC000013A` = **STATUS_CONTROL_C_EXIT**：进程被外部终止
  （控制台被关、任务被"结束"、会话结束），不是 Python 异常（所以连 traceback 都没有）。

### 现在怎么防

| 措施 | 实现 |
|---|---|
| 边跑边落盘 | 每个方向跑完立刻写 `status.json`（原子替换）+ 触发 `lit_digest.py --render`；被中途杀掉也留下可用产物 |
| 可续跑 | `progress.json` 记已完成方向；`lit_daily.py --resume` 接着跑 |
| 失败可见 | 单方向失败记进 `status.json` 的 `error` 与摘要的 ❌；退出码 3（部分失败）/4（全失败） |
| 不依赖控制台 | 全程同时写 `daily/run-<日期>.log`（带时间戳） |
| 无窗口运行 | 计划任务改用 `pythonw.exe`（没有窗口可被误关），退出码仍写入日志 |

### 注册/改期/停用

```powershell
cd "<你的库根>"
# 先看会做什么（不写系统）
powershell -ExecutionPolicy Bypass -File tools\lit_daily_task.ps1 -WhatIf
# 每天 07:47，无窗口运行（pythonw），知识库路径显式
powershell -ExecutionPolicy Bypass -File tools\lit_daily_task.ps1 -Time 07:47
# 状态 / 立刻跑一次 / 停用 / 删除
powershell -ExecutionPolicy Bypass -File tools\lit_daily_task.ps1 -Status
powershell -ExecutionPolicy Bypass -File tools\lit_daily_task.ps1 -RunNow
powershell -ExecutionPolicy Bypass -File tools\lit_daily_task.ps1 -Disable
powershell -ExecutionPolicy Bypass -File tools\lit_daily_task.ps1 -Remove
```

任务设置：`StartWhenAvailable`（错过会补跑）、忽略重复实例、限时 2 小时、以当前用户身份运行。
**补跑会在任意时间弹出来**——所以必须用 `pythonw` 无窗口，否则用户随时可能把它关掉（正是 10-09 的成因）。

---

## 2 · 收尾链路（实测耗时）

| 命令 | 产物 | 实测 | 是否必跑 |
|---|---|---|---|
| `qc_evidence_base.py --apply` | 概念页 `evidence_base` | 快 | 仅新建/大改 concept、topic 时；**必须在建索引前** |
| `kb_build_index.py` | `wiki/.index/{meta,meta_full,bm25}.json` | 秒级 | ✅ 唯一强制 |
| `kb_semantic_search.py --add <页>` / `--build` | `embeddings.npy` 等 | 增量快 / 全量 ~110s | 按需（要语义检索） |
| `kb_corpus.py --build` | `wiki/.index/corpus/*`（~140MB） | ~66s（640 文件） | 按需（要原文分块检索） |
| `kb_dois.py` + `lit_catalogue.py` | `dois.json`、`local_lit_catalogue.json` | 秒级 / 数十秒 | 每轮 lit-watch 必跑（决定下轮去重） |
| `kb_lint.py --quick` | 红旗 | <1s | 建议 |
| `kb.py --doctor` | 新鲜度报告 | <1s | 建议 |

`lit_ingest.py --apply` 已自动跑 `kb_dois.py` + `lit_catalogue.py`；
`lit_finish.py` 负责 index.md / log_ops.md / `kb_build_index.py`（可选语料与语义）。

**index.md 与 log 的真相**（审计结论）：`wiki/index.md` **没有任何自动更新器**
（footer 自称"每次 ingest 自动更新"与事实不符）；`wiki/log.md` 按 CLAUDE.md
**已冻结为历史存档**，新条目写 `wiki/log_ops.md`。`lit_finish.py` 把这两件事补上。

---

## 3 · 体检项与已知失效

| 检查 | 若失败意味着 |
|---|---|
| 依赖 `fitz` | 阶段 C 与"收编对账"全废（`lit_extract.py`/`lit_catalogue.py` import 期即崩） |
| 白名单为空 / 配置解析失败 | `lit_discover` 退化为**全网关键词检索**（违背"白名单是范围边界"） |
| 去重源"贡献 0 篇" | 该源白配（实测 `<库外路径> 文献` 递归 0 个 PDF） |
| DOI 未归一（尾部粘连） | 去重键失配 ⇒ 那批论文被**重复下载**（实测目录里 15 条） |
| 目录条目缺标题 | 目录无法人工辨认（实测 623/791 缺标题，历史遗留） |
| 卡片 DOI ⊄ 库内清单 | `kb_dois.py` 滞后 ⇒ 新卡不参与去重 |
| 索引比最新卡片旧 | 新页搜不到（跑 `kb_build_index.py`） |
| 提取台账未建立 | "哪些 PDF 还没提取"只能靠文件名猜（实测 495 PDF vs 391 md，199 个疑似） |
| 空的每日目录 | 当天任务被中途杀掉（外部终止不留 traceback） |

### 已修/待注意的库内缺陷

- **`kb_backlinks.py` 曾全面不可用**：`bm["_tokens"]` 是 v1 索引字段，索引迁到 v2（倒排 `postings`）后
  默认 / `--page` / `--suggest` 三种模式全部 `KeyError`，而 `--selftest` 不碰 bm25 所以一直绿。
  现已改为从 `postings` 还原（717 页实测可还原），**"入站≥1、出站≥2"的补链纪律恢复可用**。
- **`kb.py --doctor` 会报嵌入索引缺页**（如"713 页, 缺失 4"）——那是语义索引没增量更新，
  用 `kb_semantic_search.py --add <缺的页>` 或 `--build` 补。

---

## 4 · 双运行时布局（Claude Code / DSH）

### DSH 的发现规则（源码级）

DSH（`@deepseek-ai/dsh-skill-filesystem`）只扫这些根，**不读 `.claude/skills`**：

| 优先级 | 根 |
|---|---|
| 100 | `<项目根>/.dsh/skills`（项目根 = 向上找 `.git`） |
| 200 | `<项目根>/.agents/skills` |
| 300 | custom（agent preset 自带） |
| 400 | `$DSH_HOME/skills` |
| 500 | `~/.agents/skills` |
| — | bundled（产品自带 skills） |

frontmatter：**必填 `name` + `description`**；`name` 必须 `^[a-z0-9]+(-[a-z0-9]+)*$`；
`whenToUse`、`metadata` 被识别；未知键（如 `trigger:`、`allowed-tools:`）**静默丢弃**；
camelCase 的 `disableModelInvocation`/`modelInvocable`/`userInvocable` 会**报错并整条忽略**。

### 本机正确布局（方向在两处恰好相反）

| 层级 | 真源（放内容） | 另一侧（junction） |
|---|---|---|
| 全局 | `<你的 .claude>\skills\<name>\` | `$DSH_HOME\skills\<name>`（DSH_HOME=`<库外路径> |
| KB 项目内 | `<你的库根>\.dsh\skills\<name>\` | `<你的库根>\.claude\skills\<name>` |

⚠️ 两个已知坑（审计实测，未擅自改动）：
1. **项目技能真源未入 git**：`.dsh/skills/` 与 6 条 junction 在 KB 仓库里都是 untracked，
   唯一被跟踪的 skill 文件是废弃的 `.claude/skills/batch-ops/SKILL.md`。真源没有回滚网。
2. **`skill-creator` 双源**：DSH 取 bundled 版，改 `<你的 .claude>\skills\skill-creator` 对 DSH 无效。

### 查断链（只读）

```powershell
$dirs = @('<库外路径>','<你的 .claude>\skills',
          '<你的库根>\.dsh\skills','<你的库根>\.claude\skills')
foreach ($d in $dirs) {
  "===== $d"
  Get-ChildItem $d -Force | ForEach-Object {
    $i = Get-Item $_.FullName -Force; if (-not $i.LinkType) { return }
    foreach ($t in $i.Target) { if (-not (Test-Path $t)) { "BROKEN  $($_.Name) -> $t"; return } }
    if (-not (Test-Path (Join-Path $_.FullName 'SKILL.md'))) { "NO-SKILL.md  $($_.Name)" }
  }
}
```

**关键前提**：DSH 的项目根靠"向上找 `.git`"、且只从**会话工作目录**推导。
所以 KB 的 6 个 kb-* 项目技能**只有在以 KB 为工作目录开会话时**才会进 DSH 目录。

---

## 5 · Claude Code 侧

- 斜杠命令：`<你的 .claude>\commands\lit-watch.md`（全局）与
  `<你的库根>\.claude\commands\lit-watch.md`（项目内）。
  内容是把自然语言请求翻译成上面那套命令；`$ARGUMENTS` 接用户输入。
- 全局 skill：`<你的 .claude>\skills\lit-watch\SKILL.md`（保留 `trigger: /lit-watch`，
  Claude Code 用它做 `/` 菜单；DSH 会忽略该键但保留 `whenToUse` 与 description）。
