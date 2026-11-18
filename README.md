# Matsci Knowledge Base

> 一个让 **AI agent 从零搭建并运作材料科学知识库**的插件。
> 一条命令起一个空库，之后用**检索层**（BM25／语义／分层取证）、**文献流水线**（发现→下载→提取→建卡）、
> **健康检查**（lint／QC）把它养成你的「第二大脑」。附 **MCP server** 与 **9 个流程技能**，
> 兼容 **Claude Code 与 Qoder** 双平台。
>
> **它不是**一份现成的内容库——**不含任何文献或笔记**。它只给你**结构、工具与纪律**，内容由你自己灌。
> **建议安装 Obsidian**：库本体是纯 Markdown，Obsidian 让笔记和索引可视化。

**版本谱系**：仓库版本 **v0.4.0**，续接 matsci-kb-kit v0.3.0；插件形态为首版。
相对旧 kit 的变化：插件化双平台安装、`sci_*` 决策层不随包、Obsidian 降为可选层、
以「空库可用性」为工具取舍审计标准。

---

## 目录

- [1. 30 秒看懂它是什么](#1-30-秒看懂它是什么)
- [2. 它给你什么](#2-它给你什么)
- [3. 安装](#3-安装)
- [4. 5 分钟跑起来](#4-5-分钟跑起来)
- [5. 你的库长什么样](#5-你的库长什么样)
- [6. 日常怎么用](#6-日常怎么用)
- [7. 文献流水线：从发现到建卡](#7-文献流水线从发现到建卡)
- [8. 挂到 AI 客户端（MCP）](#8-挂到-ai-客户端mcp)
- [9. 技能一览](#9-技能一览)
- [10. 常见问题排错](#10-常见问题排错)
- [11. 设计要点（为什么这么做）](#11-设计要点为什么这么做)
- [12. 给维护者：生成物 vs 手写件](#12-给维护者生成物-vs-手写件)
- [许可](#许可)

---

## 1. 30 秒看懂它是什么

### 它解决什么问题

用 Markdown 记科研笔记的人，几乎都会撞到同一面墙：

| 症状 | 后果 |
|---|---|
| 笔记越写越多，**找不到东西** | 只能靠记忆和文件夹，检索等于翻箱倒柜 |
| 同一个概念在 5 个页面里说法不一 | 不知道哪个是最新、最可信的 |
| 从论文里抄了结论，**忘了是哪篇、哪一段** | 写作时无法回溯，等于白抄 |
| 让 AI 帮忙，它**读不到你的笔记** | AI 只能靠通用知识瞎猜 |

本插件就是针对这四点的**约定 + 工具 + 纪律**：

1. **约定**（建库时物化的 `CLAUDE.md`）：页面该长什么样、字段怎么填、证据怎么写——**AI 也按同一套约定工作**。
2. **工具**（`tools/`）：建索引、检索、分层取证、lint、文献流水线——把约定变成可执行的命令。
3. **纪律**（方法论与技能）：什么算证据、什么只能算单篇主张、哪些错误必须报警。

### 一个类比

把库想成一座**图书馆**：

- `raw/` = **书库**（原始资料，只进不改）
- `wiki/` = **阅览室 + 你自己写的书评**（知识，会被反复整理）
- `wiki/.index/` = **卡片目录**（派生数据，随时可重做；目录丢了，书还在）
- `tools/` = **管理员**（帮你上架、找书、校对）

**关键**：卡片目录（索引）不是知识。搞坏了就重建，一秒的事。

### 它不是什么

- ❌ 不是文献库：不含任何 PDF 或笔记。
- ❌ 不是 Obsidian 插件：工具是独立 Python 脚本；不装 Obsidian 一切功能照常。
- ❌ 不会替你写结论：建卡只建**骨架**，正文留 `## 待精读` 给你（或 AI）填。
- ❌ 不是 npm 命令行工具：以 **agent 插件**形态安装（Claude Code / Qoder），也可克隆源码直接用脚本。

---

## 2. 它给你什么

| 层 | 内容 | 在哪 |
|---|---|---|
| **结构** | `wiki/{concepts,entities,sources,topics,outputs,experiments}` + `raw/` + `_archive/`（只移不删）+ `_scratch/` | `scaffold/` |
| **工具** | **71 个**：`kb.py` 统一入口 + `kb_*` 检索与体检、`qc_*` 质检、`lit_*` 文献流水线 | `tools/` |
| **纪律** | 页面 schema、`evidence_base` 证据承重、批判性标记、元数据静默丢失防线、L1/L2/L3 分层检索 | `scaffold/CLAUDE.md`（建库时物化） |
| **流程技能** | **9 个**：首跑配置 / 检索 / 体检 / 文献全链 / 本地约定 / 浏览器兜底 / QC 循环 / 审稿循环 / 批次 ingest | `skills/` |
| **客户端** | `mcp/server.py`：**20 个**工具（18 读 + 2 写，写需双钥） | `mcp/` |
| **可选渲染层** | `.obsidian/` 最小配置 + 5 个 Bases 视图（`--with-obsidian` 才铺设） | `scaffold/obsidian/`、`scaffold/bases/` |
| **文档** | 架构 / 快速上手 / MCP / 工具速查 / 方法论 | `docs/` |

---

## 3. 安装

### 3.1 前置

| 需要 | 说明 |
|---|---|
| **Python ≥ 3.10** | 3.14 已实测。`python --version` 确认 |
| **核心依赖 4 包** | `pyyaml` `jieba` `numpy` `PyMuPDF`（检索分词、索引、PDF 提取） |
| **Git**（可选但强烈推荐） | 你的库是纯文本，适合版本化 |
| **Obsidian**（可选并强烈推荐） | 仅当你要图形化浏览时可选安装 |

### 3.2 安装插件（双平台）

**Qoder**：设置 → 插件 → 从本地安装，选择本仓库目录（或按白名单打包 zip 后经安装器安装）。
`.mcp.json` 的 `${QODER_PLUGIN_ROOT}` 变体无需改动。

**Claude Code**（安装链路已实测）：

```bash
claude plugin marketplace add <本仓库目录>
claude plugin install matsci-knowledge-base@matsci-local
```

- marketplace 名为 `matsci-local`；安装后 `claude plugin list` 应显示 enabled。
- **MCP 需一步手动换用变体**：仓库 `.mcp.json` 默认是 Qoder 变体
  （`${QODER_PLUGIN_ROOT}`），Claude Code 不展开该变量；按 [`docs/MCP.md`](docs/MCP.md)
  换成 `${CLAUDE_PLUGIN_ROOT}` 即 Connected。技能主路径不受影响。

**源码直用**（不装插件也能跑全部脚本）：克隆本仓库后

```bash
pip install -r requirements.txt
```

### 3.3 分层依赖

```bash
pip install -r requirements.txt            # 核心：pyyaml jieba numpy PyMuPDF
pip install -r requirements-optional.txt   # 可选：语义检索/精排、浏览器兜底、CAJ 转换等
pip install -r mcp/requirements.txt        # 只有要用 MCP 才装
```

可选依赖**缺失时明确报错并提示安装命令，不静默降级**。
特别注意：`kb.py search` 默认 `--mode hybrid` 要求嵌入索引 + 本地 Reranker，
缺一就**退出码 3**；没装可选依赖时显式用 `--mode bm25`（零额外依赖）。

---

## 4. 5 分钟跑起来

### 4.1 建库（一条命令，纯 Markdown）

```bash
python scripts/kb_init.py --target /path/to/my-vault
```

Windows 示例：`python scripts\kb_init.py --target "D:\MyVault"`

它做的事（**幂等**：已存在的文件默认**不覆盖**）：

1. 建目录树（含 `.gitkeep`）：`wiki/` 六类页面目录、`raw/` 五子目录、`projects/`、`_archive/`、`_scratch/`
2. 放 4 个根元文件：`wiki/index.md` `wiki/tags.md` `wiki/log_ops.md` `wiki/log_insights.md`
3. 放 `tools/`（71 个工具）与 `CLAUDE.md`（方法论）
4. 放 `profile.md`（首跑访谈用的空白档案），由模板写 `tools/lit_config.yaml`
5. 放 `.gitignore` / `.gitattributes` / `_archive/README.md`（归档登记册）
6. **跑一次索引构建**——空库也会产出一个**合法的空索引**

常用开关：

```bash
python scripts/kb_init.py --target <vault> --with-obsidian   # 加铺 .obsidian/ 与 5 个 Bases 视图
python scripts/kb_init.py --target <vault> --force           # 允许覆盖已存在文件
python scripts/kb_init.py --target <vault> --no-index        # 跳过索引构建
python scripts/kb_init.py --target <vault> --check-deps      # 只检查依赖分层
python scripts/kb_init.py --target <vault> --update-tools    # 升级工具（见 §4.4）
```

> 技能在**插件级**注册，`kb_init` **不**把技能复制进库——装好插件即带 9 个技能。

### 4.2 自检

```bash
python <vault>/tools/kb.py --doctor      # 环境与索引诊断 → === doctor PASS ===
python <vault>/tools/kb_toolcheck.py     # 实跑全部工具的 --selftest/--help
```

`[MISS] 嵌入索引不存在` 与 `[--] 常驻服务未运行` 是**正常态**：
语义检索是可选增强；`kb_serve` 只是加速器，不是硬依赖。

### 4.3 首跑配置（只做一次）

在 agent 里触发 **`kb-onboard`** 技能（说「初始化知识库 / 帮我配研究方向」即可）：
分 4 轮访谈（专业 / 关键词 / 偏好期刊 / 机器与习惯），产出 `profile.md` 与
**真正生效**的 `tools/lit_config.yaml`（方向 + 期刊白名单）。随后就能跑第一轮文献发现。

### 4.4 升级工具

插件更新后，对已有库重新物化工具——**知识数据不动**，旧工具备份到 `_archive/tools-backup-*/`：

```bash
python scripts/kb_init.py --target <vault> --update-tools
```

`tools/lit_config.yaml` 是你的配置，升级时**保留不重置**。

### 4.5 怎么算成功

`--doctor` 以 `=== doctor PASS ===` 结尾；空库 `kb_search` 返回 0 命中 + low_confidence
而**不是崩溃**。刚建的空库跑 `lit_doctor` 报一些 ❌/⚠️（白名单为空、方向未配）是
**空库正常态**，onboard 配好后自然消失。

---

## 5. 你的库长什么样

### 5.1 目录地图

```
my-vault/
├── wiki/                      ← 知识层：你会不断长大的一层
│   ├── concepts/              概念页（"固态电解质是什么"）
│   ├── entities/              实体页（人 / 机构 / 材料 / 软件）
│   ├── sources/               文献卡（一篇论文 = 一页）
│   ├── topics/                主题综述页（把一个概念簇讲成一个知识模块）
│   ├── outputs/               产出（lint 报告、综述稿、分析结论）
│   ├── experiments/           实验方案（审核过的方案才进知识层）
│   ├── index.md               全库总览（Pages 表）
│   ├── tags.md                标签清单
│   ├── log_ops.md             操作日志（每次操作追加一行）
│   ├── log_insights.md        方法论洞察
│   └── .index/                ★ 派生索引（可重建，已 gitignore）
│
├── raw/                       ← 资料层：一手资料，工具**只读**不写
│   ├── pdf/                   PDF 原件（含 si/ 补充材料）
│   ├── text/                  提取出的全文 Markdown
│   ├── assets/                正文插图
│   ├── clippings/             网页剪藏
│   └── notes/                 笔记 + lit-watch 运行产物
│       └── lit-watch/{daily,picks,downloads,state}
│
├── tools/                     ← 工具层（kb_* / qc_* / lit_*）＋ lit_config.yaml
├── CLAUDE.md                  ← 方法论：AI 按它工作，你也该读一遍
├── profile.md                 ← 你的研究档案（首跑访谈产物）
├── projects/                  ← 工程层（可选：写作/课题，与知识层分离）
├── _archive/                  ← 归档（**只移不删**，登记册 README.md）
├── _scratch/                  ← 在用临时区（备份落点，不可整目录清理）
└── *.base + .obsidian/        ← 仅 --with-obsidian 时存在（可选渲染层）
```

### 5.2 三层数据的区分（这条最重要）

| 层 | 目录 | 性质 | 进 git？ | 丢了怎么办 |
|---|---|---|---|---|
| **知识** | `wiki/`（除 `.index/`） | 人／AI 维护，会被反复整理 | ✅ 要 | **不可丢** |
| **资料** | `raw/` | 原始一手资料，**只读** | 视情况（PDF 常忽略） | 重新下载／重新提取 |
| **派生** | `wiki/.index/` | 由 `wiki/` 算出来的索引 | ❌ 不用 | **重建即可（秒级）** |

搞混这三层是本类库最常见的错误来源：把索引当知识手工编辑 → 下次重建被覆盖；
把 `raw/` 当笔记去改 → 回链与证据全部失真。

### 5.3 页面的六种类型

| 类型 | 目录 | 写什么 |
|---|---|---|
| `concept` | `wiki/concepts/` | 概念／方法／机理的综合 |
| `entity` | `wiki/entities/` | 人／机构／材料／软件 |
| `source` | `wiki/sources/` | **一篇文献一页**：摘要 + 要点 + 批判性评估 |
| `topic` | `wiki/topics/` | 把一簇概念讲成一个独立知识模块 |
| `output` | `wiki/outputs/` | 报告、综述稿、分析结论 |
| `experiment` | `wiki/experiments/` | 审核过的实验方案（逐条带 quote） |

### 5.4 一页的最小结构

每个 `wiki/` 页面都以 **YAML frontmatter** 开头：

```markdown
---
created: 2026-10-12
updated: 2026-10-12
type: concept
tags: [固态电解质, 界面]
aliases: [SSE, 固态电解质]
summary: "一句话摘要，用于 index.md"
sources:
  - "[[sources/2024-某论文标题.md]]"
---

# 固态电解质

开篇一句摘要。

## 二级标题组织板块

关键术语首次出现时用 [[wikilink]]。
```

附加字段：concept/topic 的 `evidence_base` 由 `qc_evidence_base.py` **机械判定，勿手填**
（`strong / mixed / single-source / secondhand`，综述引用按此判权重）；
source 页 `source_url` **必填**。

> 🔴 **元数据静默丢失是本类库的头号失效**：页面能正常打开、正文可读，人工浏览完全看不出，
> 但元数据在索引层整个消失。成因通常是**长字段含冒号没加引号**。
> 纪律：frontmatter 一律走 `kb_lib` 的解析／重组函数，写完跑一次 `kb_lint.py --quick`。

### 5.5 可选渲染层（Obsidian）

加 `--with-obsidian` 后得到 5 个 **Bases** 视图（核心插件，不是 Dataview）：
全库总览 / 文献总览 / 概念索引 / 实体名录 / `optional/` 剪藏文集。

> ⚠️ **视图会静默收窄**：frontmatter 缺字段或 YAML 写坏，页面会**从视图中悄悄消失**且不报错。
> 改完大批页面后跑 `python tools/qc_base_check.py --check`。

---

## 6. 日常怎么用

### 6.1 写笔记 → 让库认识它

1. 在 `wiki/concepts/`（或 `entities/`）新建 `.md`，按 [§5.4](#54-一页的最小结构) 写 frontmatter
2. 重建索引：`python tools/kb_build_index.py`（增量，秒级）
3. 搜索：`python tools/kb_search.py "固态电解质 界面"`

**记住这条：改了页面一定要重建索引，否则搜不到。**

### 6.2 检索：`kb.py` 一个入口

```bash
python tools/kb.py search "固态电解质界面" --mode bm25   # ★ 零额外依赖，先跑这个
python tools/kb.py ask "这个方向的证据充分吗"             # 自动在传统 RAG / Agentic RAG 间选
python tools/kb.py "SSE" --resolve                      # 只做别名解析
python tools/kb.py "固态电解质" --route                  # ★ 分层取证，首选（见下）
python tools/kb.py --corpus "界面阻抗"                   # raw 全文块检索（可回指行号）
python tools/kb.py --doctor                             # 环境诊断
```

### 6.3 分层取证 `kb_route`（为什么它最重要）

它把结果**分三层返回，不混排**：

| 层 | 内容 | 可信度 |
|---|---|---|
| **L1** | concept / entity / topic 页 | 本库的**当前综合**（二手概括） |
| **L2** | source 文献卡 | **单篇论文的主张** + `source_reliability` |
| **L3** | raw 全文块 | **原文字面表述**，可回指 `文件:行号`（一手） |

混排会让 AI 把「本库二手综合」当成「一手证据」直接引用。
输出里的 `low_confidence` 要认真看：**BM25 没有分数下限，任何查询都会凑满 k 条**；
普遍低分应读成「本库对这个问题还没有知识」，而不是硬答。

### 6.4 质量检查

```bash
python tools/kb_lint.py --quick                 # 效率优先：只查最近 ingest
python tools/kb_lint.py --deep                  # 全库全量 + 扩展检查族 A–F
python tools/kb_lint.py --deep --fix            # 干跑预览可修复项（不写盘）
python tools/kb_lint.py --deep --fix --apply    # 真正落盘（自动备份）
python tools/kb_where.py "某表述"                # ★ 断言"库内没有 X"之前必跑
python tools/kb_backlinks.py --suggest          # 孤立页 + 补链建议
python tools/qc_evidence_base.py                # 证据承重机械判定
```

`kb_where` 跨四个目录检索并**逐目录报命中数**——曾出现三处独立检索都断言某文不在库内，
而全文其实一直在第四个目录里。**写明检索范围 ≠ 范围完备。**

---

## 7. 文献流水线：从发现到建卡

把「OpenAlex 上找到论文」→「它会出现在你的库里，还带出处」这条路全部自动化。
先跑一次 `kb-onboard` 配方向与期刊白名单（§4.3）。

### 7.1 阶段总览

| 阶段 | 命令 | 关键产物 | 退出码 |
|---|---|---|---|
| 0 体检 | `lit_doctor.py` | 问题清单 | 0/1/2 |
| A 发现 | `lit_daily.py` ／ `lit_discover.py` | `daily/…/cand_<slug>.json` | 0/2/3/4 |
| A′ 摘要/勾选 | `lit_digest.py --render / --pick` | `picks/…-picks.json` | 0/2 |
| B 取全文 | `lit_fetch.py --in <picks>` | `raw/pdf/*.pdf` + 下载清单 | 0=至少一篇成功／**4=全失败** |
| B′ 收编 | `lit_manual_import.py [--apply]` | 手工下载改名入库 | 0 |
| B″ 补 SI | `lit_si.py fetch [--apply]` | `raw/pdf/si/*` 或手动清单 | 0／**4=有 SI 但没取到** |
| B‴ 浏览器兜底 | `lit_browser_fetch.py --latest --apply` | 反爬站点正文与 SI | 0/2/4 |
| C 提取 | `lit_batch.py --extract` | `raw/text/…md` + 插图 | 0 |
| D 建卡 | `lit_batch.py --ingest [--apply]` | `wiki/sources/*.md` **骨架** + 门禁 | 0=过／**1=写坏**／**2=缺补链** |
| D′ 二次加工 | `lit_enrich.py request → apply` | 带**原文 quote** 的证据化字段 | 0/1/2 |
| E 收尾 | `lit_finish.py --apply` | index.md 行、log_ops、索引 | 0/1 |
| F 缺口 | `lit_gapscan.py --queries` | 下一轮检索式 | 0/1/2 |

### 7.2 四条配置规则

1. **期刊白名单是范围边界**；加刊用 `lit_journals.py --add "Nature Energy"` 解析 ISSN，不要凭记忆写。
2. **tier 阈值必须设在评分下限（0.70）之上**，否则分级形同虚设；T0/T1 宽松是刻意的（顶刊召回优先）。
3. **`uncapped: true`** = 该档不被 `--limit` 截断（顶刊宁可多不能漏）。
4. **OpenAlex 翻页要 API key**：用环境变量 `OPENALEX_API_KEY`，**不要明文写进 `lit_config.yaml`**
   （它被 git 跟踪，明文 key 会永久留在历史里）。

### 7.3 建卡门禁与二次加工

**只建骨架，绝不替你写结论**。门禁硬失败（1）= frontmatter 写坏；软失败（2）= 补链纪律未完成
（出链 < 2 或入站 = 0）——**看到 2 就要去补链，别当成功**；工具不替你补链（那会凭空造出错误关联）。

往骨架里填结论走 `lit_enrich` 两步路：`request` 产出 JSON → 你的模型产出 proposal
（每条 claim 必须带原文逐字 quote）→ `apply` 机械校验后落盘。**这个工具本身不调用任何 LLM**，
价值全在「机械可验」，不在「自动」。

### 7.4 退出码怎么读（重要）

**不要把「失败」读成「这个方向没有新文献」**——那正是这套退出码要防的事。
`lit_fetch` 退 4 = 全部下载失败（看手动清单手工下载，再走 B′）；
`lit_si` 退 4 = 判定有 SI 但一份没取到（RSC/ACS/Science/IOP 对脚本一律 403，属预期）。

### 7.5 每天自动跑

调度**不在 MCP 范围**，放 OS 侧：Linux/macOS 用 cron；Windows 用任务计划程序调包装脚本。

---

## 8. 挂到 AI 客户端（MCP）

装好插件后 MCP 自动注册（Qoder 无需改动；Claude Code 换一步变量，见 §3.2）。
源码直用时：

```bash
pip install -r mcp/requirements.txt
python mcp/server.py --vault /path/to/my-vault                # stdio，只读
python mcp/server.py --vault /path/to/my-vault --allow-write  # 额外允许写工具
python mcp/server.py --list-tools                             # 不装 SDK 也能看清单
```

库根解析：`--vault` > `MATSCI_KB_VAULT` 环境变量 > 当前目录；目标不是知识库会**拒绝启动**。

**20 个工具**：只读 18（`kb_route` 首选、`kb_search`、`kb_resolve`、`kb_where`、
`kb_corpus_search`、`kb_graph`、`kb_backlinks`、`kb_stats`、`kb_tags`、`kb_dois`、`kb_cite`、
`lit_batch`、`lit_gapscan`、`kb_doctor`、`kb_lint`、`kb_selftest`、`kb_toolcheck`、`lit_doctor`）；
写 2（`kb_build_index`、`kb_init`）——**双钥门禁**：server 以 `--allow-write` 启动
**且**调用方传 `apply=true`，缺一即拒。`kb_init` 的 `target` 必须是绝对路径。

---

## 9. 技能一览

| 技能 | 用途 |
|---|---|
| `kb-onboard` | 首跑配置向导：4 轮访谈 → profile.md + lit_config.yaml |
| `kb-query` | 库内检索协议：分层证据、多跳、原文回指 |
| `kb-lint` | 健康检查与批量修复：--quick/--deep、扩展族 A–F、校验器纪律 |
| `lit-watch` | 文献全链：发现→下载→提取→建卡→收尾→缺口驱动 |
| `lit-pipeline` | 文献流水线本地约定：产物落点、tier 红线、去重源、已知坑 |
| `lit-browser-fetch` | 真实浏览器 + 类人鼠标兜底下载；按域配额/冷却/熔断 |
| `kb-qc-loop` | QC 串行循环：核查 ingest 产物里原文不存在的数字与结论 |
| `kb-review-cycle` | 综述工程「审稿 ⇄ 修改」循环与逐条处置纪律 |
| `kb-ingest-batch` | 批次 ingest 编排：台账、批次文件格式、batch_close |

会话内技能带插件前缀（如 `matsci-knowledge-base:kb-onboard`）；说触发词即可。

---

## 10. 常见问题排错

**Q：`--doctor` 报「嵌入索引不存在」** — 正常，语义检索是可选增强。
装 `sentence-transformers` 后 `python tools/kb.py index embed`。

**Q：`kb.py search` 退 3（RetrievalUnavailable）** — 默认 hybrid 不静默降级。
① `--mode bm25`；② 装可选依赖后建嵌入索引。

**Q：搜索 0 命中但库里有页面** — 99% 忘了重建索引：`kb_build_index.py`。

**Q：页面在 Obsidian 里好好的，却从 Bases 视图消失** — frontmatter 写坏
（长字段含冒号没加引号）。跑 `kb_lint --quick` 与 `qc_base_check --check`。

**Q：`lit_ingest --apply` 退 2** — 不是写坏，是补链没做完。去补链后重跑。

**Q：`lit_fetch` 退 4** — 全部下载失败，不是「没有新文献」。看手动清单。

**Q：刚建的空库 `lit_doctor` 一堆 ❌** — 空库正常态，onboard 配好后消失。

**Q：库目录能改名/搬家吗** — 能。工具用 `__file__` 派生库根，不写死路径。

**Q：需要一直开着 `kb_serve` 吗** — 不需要，可选加速器。

**Q：索引可以删吗** — 可以，纯派生数据，重建即可。

**Q：Claude Code 里出现第二个 matsci-kb 条目（Pending approval）** — 那是项目配置
兼加载的条目，不是插件服务状态；认准 `plugin:matsci-knowledge-base:matsci-kb`。

---

## 11. 设计要点（为什么这么做）

- **库根靠 `__file__` 派生**：整个目录可随意改名／迁移／复制。
- **空库也必须能启动**：0 页面产出合法空索引；检索返回「0 命中 + low_confidence」而不是崩溃。
- **「索引存在但为空」≠「索引不存在」**：前者正常，后者真故障，明确报错。
- **元数据静默丢失是头号失效**：frontmatter 一律走 `kb_lib` 唯一解析器。
- **校验装置与生成装置同源**：不另写"差不多"的宽松校验器。
- **写盘默认干跑**：`--apply` 才写；写前备份、写后复算。
- **退出码是信号**：不把失败静默成没有结果；可选层缺失明确报错。
- **不强制依赖 Obsidian**：纯 Markdown + 目录约定 + wikilink 工具链解析；Bases 只是加分项。

---

## 12. 给维护者：生成物 vs 手写件

本仓库的许多文件是**由一份源知识库经 `build/build_plugin.py` 过滤 + 去个人化生成的派生数据**。

| 类别 | 文件 | 怎么改 |
|---|---|---|
| **生成物** | `tools/**`、`skills/**`、`scaffold/CLAUDE.md`、`docs/METHODOLOGY.md`、`docs/TOOLS.md`、`plugin.yaml` | ❌ 勿手改；改真源或规则层后重跑生成器 |
| **手写件** | `build/**`、`mcp/**`、`scripts/**`、`README.md`、`CLAUDE.md`、`scaffold/`（除 CLAUDE.md）、`docs/`（除两篇生成物）、清单与许可 | ✅ 直接改，但须列入泄漏扫描 `SCAN_TARGETS` |

**重新生成与验证**：

```bash
python build/build_plugin.py --src <真源库根>   # 真源不内置；源库 dirty 硬门禁
python scripts/verify_plugin.py                # 9 项验收
python -m unittest discover -s tests
python scripts/export_plugin.py                # 白名单导出 + 终审泄漏审计
```

**隐私架构**（红线，详见 [`build/rules/README.md`](build/rules/README.md)）：

- 真实专名只存 `build/rules/private/`（gitignored）；公开词表只收通用形态（家目录/用户名路径）。
- 生成后全树泄漏扫描，任一命中即构建失败；**私有规则缺失时导出立即中止（rc=2）**，不静默降级。
- `private/` 永不发布：git 靠 `.gitignore`；npm 靠 `files` **逐文件白名单**
  （🔴 files 白名单压过 .gitignore，旧 kit 实测整目录白名单曾把私有规则发出去）。
- CI 在 ubuntu 跑 `verify_plugin.py` + unittest（`.github/workflows/verify.yml`）；
  干净 checkout 无 private，扫描用公开半份词表并打印 warn，导出类测试自动 skip。
  **CI 绿 ≠ 本地终审绿**：发布前本地带 private 全量跑。
- **Python 版本兼容**：活库跑较新 Python，插件声明 ≥3.10（CI 3.11）。PEP 701
  f-string 表达式内反斜杠这类词法病灶经公开 `build/rules/compat_scrub.yaml`
  在构建期转 `.format`（不手改生成物、不动活库）；`TestCompatScrub` 钉住。

`plugin.yaml` 记录生成溯源：源 commit、生成时间、逐文件 sha256。

---

## 许可

- **代码**（`tools/**`、`mcp/**`、`scripts/**`、`build/**`）：**MIT**，见 [`LICENSE`](LICENSE)。
- **方法论文档**（`CLAUDE.md`、`docs/**`、`skills/**`、`scaffold/**`）：建议 **CC-BY-4.0**。详见 [`NOTICE.md`](NOTICE.md)。

工具链的最初构想来自 [karpathy/llm-wiki](https://github.com/karpathy/llm-wiki)。
本插件为去个人化派生作品，不含源库知识内容与个人信息。
