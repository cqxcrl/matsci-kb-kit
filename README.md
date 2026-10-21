# matsci-kb-kit

> 一套给 **Obsidian 知识库**用的**工具箱 + 方法论**。
> 一条命令起一个空库，之后用**检索层**（BM25／语义／分层取证）、**文献流水线**（发现→下载→提取→建卡）、
> **健康检查**（lint／QC）把它养成你的「第二大脑」。附一个 **MCP server**，让 AI 客户端直接调用这些工具。

**它不是**一份现成的内容库——**不含任何文献或笔记**。
它只给你**结构、工具与纪律**，内容由你自己灌。

> 一句话区分：**Obsidian 给你笔记软件，本 kit 给你「一个知识库该怎么长」的操作系统。**

---

## 目录

- [1. 30 秒看懂它是什么](#1-30-秒看懂它是什么)
- [2. 它给你什么](#2-它给你什么)
- [3. 5 分钟跑起来](#3-5-分钟跑起来)
- [4. 你的库长什么样](#4-你的库长什么样)
- [5. 日常怎么用（最常用）](#5-日常怎么用最常用)
- [6. 文献流水线：从发现到建卡](#6-文献流水线从发现到建卡)
- [7. 挂到 AI 客户端（MCP）](#7-挂到-ai-客户端mcp)
- [8. 工具速查表](#8-工具速查表)
- [9. Sci-Assistant 决策层](#9-sci-assistant-决策层)
- [10. 常见问题排错](#10-常见问题排错)
- [11. 设计要点（为什么这么做）](#11-设计要点为什么这么做)
- [12. 给维护者：生成物 vs 手写件](#12-给维护者生成物-vs-手写件)
- [许可](#许可)

---

## 1. 30 秒看懂它是什么

### 它解决什么问题

用 Obsidian 记笔记的人，几乎都会撞到同一面墙：

| 症状 | 后果 |
|---|---|
| 笔记越写越多，**找不到东西** | 只能靠记忆和文件夹，检索等于翻箱倒柜 |
| 同一个概念在 5 个页面里说法不一 | 不知道哪个是最新、最可信的 |
| 从论文里抄了结论，**忘了是哪篇、哪一段** | 写作时无法回溯，等于白抄 |
| 让 AI 帮忙，它**读不到你的笔记** | AI 只能靠通用知识瞎猜 |

本 kit 就是针对这四点的一套**约定 + 工具**：

1. **约定**（`CLAUDE.md`）：页面该长什么样、字段怎么填、证据怎么写——**AI 也按同一套约定工作**。
2. **工具**（`tools/`）：建索引、检索、分层取证、lint、文献流水线——把约定变成可执行的命令。
3. **纪律**（写在方法论里）：什么算证据、什么只能算单篇主张、哪些错误必须报警。

### 一个类比

把库想成一座**图书馆**：

- `raw/` = **书库**（原始资料，只进不改）
- `wiki/` = **阅览室 + 你自己写的书评**（知识，会被反复整理）
- `wiki/.index/` = **卡片目录**（派生数据，随时可重做；目录丢了，书还在）
- `tools/` = **管理员**（帮你上架、找书、校对）

**关键**：卡片目录（索引）不是知识。搞坏了就重建，一秒的事。

### 它不是什么

- ❌ 不是文献库：不含任何 PDF 或笔记。
- ❌ 不是 Obsidian 插件：工具是独立 Python 脚本，Obsidian 只用来「看图」。
- ❌ 不会替你写结论：建卡只建**骨架**，正文留 `## 待精读` 给你（或 AI）填。
- ❌ 不绑定 Obsidian：任何 Markdown 编辑器都能用；Bases 视图是 Obsidian 专属的加分项。

---

## 2. 它给你什么

| 层 | 内容 | 在哪 |
|---|---|---|
| **结构** | `wiki/{concepts,entities,sources,topics,outputs}` + `raw/` + 5 个 Obsidian Bases 视图 | `scaffold/` |
| **工具** | **48 个** Python 工具（`kb_*` 检索与质检 19 个、`lit_*` 文献流水线 14 个、`qc_*` 3 个、**`sci_*` 决策层 12 个**）+ 1 份多学科期刊池 | `tools/` |
| **纪律** | `CLAUDE.md`：页面 schema、`evidence_base` 证据承重、批判性标记、元数据静默丢失防线、L1/L2/L3 分层检索 | `CLAUDE.md` |
| **流程技能** | 5 个技能：`lit-watch` 文献全链 ｜ `lit-pipeline` 本地约定 ｜ `kb-query` 检索 ｜ `kb-lint` 体检 ｜ **`kb-onboard` 首跑配置向导** | `skills/` |
| **客户端** | `mcp/server.py`：把 **19 个**工具暴露给任何支持 MCP 的 AI 客户端 | `mcp/` |
| **决策层** | **Sci-Assistant**：C1 切入点发现 / C2 实验方案推荐 / C3 课题进展统筹（12 个 `sci_*` 工具，v0 全量完成） | `docs/SCI-ASSISTANT.md` |

---

## 3. 5 分钟跑起来

### 3.1 前置

| 需要 | 说明 |
|---|---|
| **Python ≥ 3.10** | 推荐 3.11+。`python --version` 确认 |
| **Node.js ≥ 14**（npm 安装方式） | `node --version` 确认 |
| **pip**（本地安装方式） | 随 Python 附带 |
| **Obsidian**（可选但推荐） | 只是用来看 `.base` 视图；工具本身不依赖它 |
| **Git**（可选但强烈推荐） | 你的库是纯文本，适合版本化 |

> ⚠️ 本 kit 自身**不需要**放在你的库里面。它是「施工队」，你的库是「房子」。

### 3.2 安装方式

#### 方式一：npm 全局安装（推荐）

```bash
npm install -g matsci-kb-kit
```

安装完成后，可以直接使用 `matsci-kb` 命令：

```bash
# 查看帮助
matsci-kb help

# 列出所有工具
matsci-kb list

# 初始化知识库
matsci-kb kb_init ./my-vault

# 检索知识库
matsci-kb kb_search "电解液设计"

# 运行 Sci-Assistant 工具
matsci-kb sci_landscape --direction "电解液设计"
```

> 💡 npm 安装会自动检查 Python 依赖，缺失时会提示安装命令。

#### 方式二：npm 本地安装

在你的项目目录下：

```bash
npm install matsci-kb-kit
```

然后通过 `npx` 使用：

```bash
npx matsci-kb help
npx matsci-kb kb_init ./my-vault
```

或在 `package.json` 的 scripts 中调用：

```json
{
  "scripts": {
    "kb:init": "matsci-kb kb_init ./my-vault",
    "kb:search": "matsci-kb kb_search"
  }
}
```

#### 方式三：本地安装（从源码）

如果你更喜欢直接管理 Python 依赖，可以克隆仓库后本地安装：

```bash
git clone https://github.com/cqxcrl/matsci-kb-kit.git
cd matsci-kb-kit
pip install -r requirements.txt
```

装上 `pyyaml` `jieba` `numpy` `PyMuPDF`——**这四个是必需**（检索分词、索引、PDF 提取）。

可选增强：

```bash
pip install -r requirements-optional.txt   # 语义检索（sentence-transformers / scikit-learn）+ 剪贴板
pip install -r mcp/requirements.txt        # 只有要用 MCP 才装
```

缺了可选包不会崩，只会**优雅降级**（例如语义检索退回 TF-IDF）。

### 3.3 建库（一条命令）

**npm 安装方式：**

```bash
matsci-kb kb_init /path/to/my-vault
```

**本地安装方式：**

在 **kit 目录**下执行，`--target` 指向你想要的库位置：

```bash
python scripts/kb_init.py --target /path/to/my-vault
```

Windows 示例：

```powershell
python scripts/kb_init.py --target "E:\MyVault"
```

它做的事（**幂等**：已存在的文件默认**不覆盖**）：

1. 建 **15 个**目录（含 `.gitkeep`）＋ `wiki/.index/`
2. 放 **4 个**根元文件：`index.md` `tags.md` `log_ops.md` `log_insights.md`
3. 放 **5 个** `.base` 视图（4 个在库根，`剪藏文集.base` 在 `optional/`）
4. 放 `.obsidian/`（app.json / core-plugins.json）与 `.gitignore`
5. 放 `profile.md`（首跑访谈用的空白档案）
6. 放 `tools/`（**48 个**工具）与 `CLAUDE.md`（方法论）
7. 由模板写 `tools/lit_config.yaml`
8. 装 5 个技能到 `.dsh/skills/` 与 `.claude/skills/`（双入口）
9. **跑一次索引构建**——空库也会产出一个**合法的空索引**

常用开关：

```bash
python scripts/kb_init.py --target <vault> --force      # 允许覆盖已存在文件
python scripts/kb_init.py --target <vault> --no-index   # 跳过索引构建
```

### 3.4 用 Obsidian 打开

用 Obsidian 的「打开文件夹作为库」选中 `/path/to/my-vault`。
你会看到 5 个 Bases 视图（此刻都是空的）和 `wiki/index.md`。

### 3.5 自检

```bash
python /path/to/my-vault/tools/kb.py --doctor      # 环境与索引诊断
python /path/to/my-vault/tools/kb_toolcheck.py     # 实跑全部工具的 --selftest/--help
```

> 注意：此后所有命令都在**你的库根**下执行（脚本靠 `__file__` 自动定位库根，
> 所以库目录**随便改名、随便搬家**都不用改任何配置）。

### 3.6 怎么算成功

`kb.py --doctor` 应该以 **`=== doctor PASS ===`** 结尾，并列出：

```
  [ok] meta.json        0 KB
  [ok] bm25.json        0 KB
  [ok] meta_lite.json   0 KB
  [ok] meta_full.json   0 KB
  索引版本: bm25 v2  页面 0  词表 0
  [MISS] 嵌入索引不存在
  [--] 常驻服务未运行（http://127.0.0.1:8791）
=== doctor PASS ===
```

**这两条 `[MISS]` / `[--]` 是正常的**：

- `嵌入索引不存在` → 语义检索是**可选增强**。想要就装 `sentence-transformers` 后跑
  `python tools/kb_semantic_search.py --build`。
- `常驻服务未运行` → `kb_serve` 只是**加速器**，不是硬依赖（见 [§10](#10-设计要点为什么这么做)）。

另外，刚建的空库跑 `lit_doctor.py` 会报一些 ❌/⚠️（期刊白名单为空、方向未配）——
这是**空库的正常态**，配好研究方向后自然消失（见 [§6.0](#60-先配研究方向只做一次)）。

---

## 4. 你的库长什么样

### 4.1 目录地图

```
my-vault/
├── wiki/                      ← 知识层：你会不断长大的一层
│   ├── concepts/              概念页（"固态电解质是什么"）
│   ├── entities/              实体页（人 / 机构 / 材料 / 软件）
│   ├── sources/               文献卡（一篇论文 = 一页）
│   ├── topics/                主题综述页（把一个概念簇讲成一个知识模块）
│   ├── outputs/               产出（lint 报告、综述稿、分析结论）
│   ├── index.md               全库总览（Pages 表）
│   ├── tags.md                标签清单
│   ├── log_ops.md             操作日志（每次操作追加一行）
│   ├── log_insights.md        方法论洞察
│   └── .index/                ★ 派生索引（可重建，已 gitignore）
│
├── raw/                       ← 资料层：一手资料，工具**只读**不写
│   ├── pdf/                   PDF 原件
│   ├── text/                  提取出的全文 Markdown
│   ├── assets/                正文插图
│   ├── clippings/             网页剪藏
│   └── notes/                 笔记 + lit-watch 运行产物
│       └── lit-watch/
│           ├── daily/         每日发现：候选 JSON + 摘要
│           ├── picks/         勾选结果
│           ├── downloads/     下载清单（拿不到的列在这里）
│           └── state/         去重目录、提取台账等缓存
│
├── tools/                     ← 工具层（kb_* 检索 / lit_* 文献 / qc_* 质检）
├── CLAUDE.md                  ← 方法论：AI 按它工作，你也该读一遍
├── profile.md                 ← 你的研究档案（首跑访谈产物）
├── projects/                  ← 工程层（可选：写作/课题，与知识层分离）
├── *.base                     ← 4 个 Bases 视图（Obsidian 数据库视图）
└── _archive/                  ← 归档（**只移不删**）
```

### 4.2 三层数据的区分（这条最重要）

| 层 | 目录 | 性质 | 进 git？ | 丢了怎么办 |
|---|---|---|---|---|
| **知识** | `wiki/`（除 `.index/`） | 人／AI 维护，会被反复整理 | ✅ 要 | **不可丢** |
| **资料** | `raw/` | 原始一手资料，**只读** | 视情况（PDF 常忽略） | 重新下载／重新提取 |
| **派生** | `wiki/.index/` | 由 `wiki/` 算出来的索引 | ❌ 不用 | **重建即可（秒级）** |

搞混这三层是本类库最常见的错误来源：

- 把索引当知识去手工编辑 → 下次重建就被覆盖，白干。
- 把 `raw/` 当笔记去改 → 回链与证据全部失真。

### 4.3 页面的五种类型

| 类型 | 目录 | 写什么 | 谁写 |
|---|---|---|---|
| `concept` | `wiki/concepts/` | 概念／方法／机理的综合 | 你或 AI（读多篇源后综合） |
| `entity` | `wiki/entities/` | 人／机构／材料／软件 | 同上 |
| `source` | `wiki/sources/` | **一篇文献一页**：摘要 + 要点 + 批判性评估 | 文献流水线建骨架，你补正文 |
| `topic` | `wiki/topics/` | 把一簇概念讲成一个独立知识模块 | 你（达到触发条件时才建） |
| `output` | `wiki/outputs/` | 报告、综述稿、分析结论 | 工具或你 |

### 4.4 一页的最小结构

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

两类页面的**附加字段**（`CLAUDE.md` 有完整说明）：

- **concept / topic**：`evidence_base`（证据承重）——由 `qc_evidence_base.py` **机械判定，勿手填**：
  `strong` / `mixed` / `single-source` / `secondhand`。**综述引用时按此判权重**。
- **source**：`source_url`（可点开的原文链接，必填）、`source_reliability`、`authors_source` 等。

> 🔴 **元数据静默丢失是本类库的头号失效**：页面能正常打开、正文可读，**人工浏览完全看不出**，
> 但元数据在索引层整个消失。成因通常是**长字段含冒号没加引号**（如 `summary: 结论: 有三点`）。
> 纪律：frontmatter 一律走 `kb_lib` 的解析／重组函数，写完跑一次 `kb_lint.py --quick`。

### 4.5 五个数据库视图（Bases）

Obsidian 的 **Bases**（核心插件，**不是** Dataview，语法不同）把 frontmatter 变成表格视图：

| 视图 | 看什么 |
|---|---|
| `数据库.base` | 全库总览 |
| `文献总览.base` | 所有 source 页 |
| `概念索引.base` | 所有 concept 页 |
| `实体名录.base` | 所有 entity 页 |
| `optional/剪藏文集.base` | 公众号／剪藏类来源 |

> ⚠️ **视图会静默收窄**：如果 frontmatter 字段缺失或 YAML 写坏，页面会**从视图中悄悄消失**且 Obsidian 不报错。
> 所以改完大批页面后跑一次 `python tools/qc_base_check.py --check`（重算选中集合 + 漂移守门）。

### 4.6 根目录的四个元文件

- `wiki/index.md`——全库总览表（新页由 `lit_finish.py` 自动插入）
- `wiki/tags.md`——标签清单
- `wiki/log_ops.md`——**操作日志**，每次操作追加一行：`## [日期] <操作> | <描述>`
- `wiki/log_insights.md`——方法论洞察

---

## 5. 日常怎么用（最常用）

### 5.1 写笔记 → 让库认识它

**最朴素的用法**（不碰文献流水线也能玩）：

1. 在 `wiki/concepts/`（或 `entities/`）新建 `.md`，按 [§4.4](#44-一页的最小结构) 写 frontmatter
2. 重建索引：

```bash
python tools/kb_build_index.py          # 增量（只重算变化的页面），秒级
```

3. 搜索：

```bash
python tools/kb_search.py "固态电解质 界面"
```

就这三步。**记住这条：改了页面一定要重建索引，否则搜不到。**

### 5.2 检索：`kb.py` 一个入口

`kb.py` 是检索的统一入口，把最常用的几种模式收在一个命令里：

```bash
python tools/kb.py "固态电解质界面"                 # 默认 BM25
python tools/kb.py "固态电解质界面" --mode semantic  # 语义（需先建嵌入索引）
python tools/kb.py "锂沉积效率"     --mode hybrid    # BM25 + 语义 RRF 融合
python tools/kb.py "SSE" --resolve                  # 只做别名解析
python tools/kb.py "固态电解质" --route              # ★ 分层取证，首选（见下）
python tools/kb.py --corpus "界面阻抗"               # raw 全文块检索（可回指 行号）
python tools/kb.py --stats                          # 索引概览
python tools/kb.py --doctor                         # 环境诊断
```

常用参数：`-k 10`（条数）、`--type concept,entity`（限定页面类型）、`--json`（机器可读）。

### 5.3 分层取证 `kb_route`（为什么它最重要）

```bash
python tools/kb_route.py "固态电解质 界面 稳定性"
python tools/kb_route.py "锂枝晶" --budget 5,5,8 --json
python tools/kb_route.py "锂枝晶" --layer 1          # 只要综合层
```

它把结果**分三层返回，不混排**：

| 层 | 内容 | 可信度 |
|---|---|---|
| **L1** | concept / entity / topic 页 | 本库的**当前综合**（二手概括） |
| **L2** | source 文献卡 | **单篇论文的主张** + `source_reliability` |
| **L3** | raw 全文块 | **原文字面表述**，可回指 `文件:行号`（一手） |

**为什么必须分层**：L1 和 L3 的可信度**不是一回事**。混排会让 AI 把「本库二手综合」
当成「一手证据」直接引用。

> ⚠️ 输出里的 `signal.top_score` 与 `low_confidence` 要认真看：
> **BM25 没有分数下限，任何查询都会凑满 k 条**。普遍低分应该读成
> **「本库对这个问题还没有知识」**，而不是硬答。

**推荐姿势**：把 `kb_route --json` 的输出整段交给你的 AI，让它基于**带引用的三层证据**回答。

### 5.4 质量检查

```bash
python tools/kb_lint.py --quick          # 效率优先：只查最近 ingest 的页面
python tools/kb_lint.py --deep           # 全面优先：全库全量 + 扩展检查族 A–F
python tools/kb_lint.py --deep --fix              # 干跑预览可修复项（不写盘）
python tools/kb_lint.py --deep --fix --apply      # 真正落盘（自动备份）
```

`kb_lint` 会查：frontmatter 完整性、source 页专项、wikilink 有效性、出度／入度、
孤立页面、topic 覆盖、index 一致性、重复别名、**证据标记未继承**等。

配套的其它体检命令：

```bash
python tools/kb_backlinks.py --suggest   # 孤立页 + 补链建议
python tools/kb_stats.py                 # 统计仪表板
python tools/kb_where.py "某表述"         # ★ 断言"库内没有 X"之前必跑
python tools/qc_base_check.py --check    # 5 个 Bases 视图是否被静默收窄
python tools/kb_toolcheck.py             # 实跑每个工具的自检（工具"能不能用"的唯一判据）
```

> 🔴 **`kb_where.py` 的用途**：它跨四个目录检索并**逐目录报命中数**。
> 说「库里没有 X」之前必须先跑它——曾出现过三处独立检索都断言某文不在库内，
> 而全文其实一直在第四个目录里。

### 5.5 让 AI 替你干

两条路，可以同时用：

1. **把 `CLAUDE.md` 给 AI 读**（Claude Code 会自动读项目根的同名文件）。
   它定义了 ingest/query/lint 三大工作流与全部纪律，AI 读完就能按同一套约定帮你消化资料。
2. **挂 MCP**（见 [§7](#7-挂到-ai-客户端mcp)），让 AI 直接调用库的工具，而不是靠你转述。

---

## 6. 文献流水线：从发现到建卡

这是本 kit 最有价值、也最复杂的一环。它的目标是把
**「OpenAlex 上找到论文」→「它会出现在你的库里，还带出处」**这条路全部自动化。

### 6.0 先配研究方向（只做一次）

刚建的空库，`tools/lit_config.yaml` 里全是**占位示例**。用 **`kb-onboard` 技能**访谈一次：

> 用 kb-onboard 帮我配置研究方向

它会分 4 轮问你（专业 / 关键词 / 偏好期刊 / 机器与习惯），产出两个文件：

| 文件 | 作用 |
|---|---|
| `profile.md` | 给人看与 AI 读的**研究档案** |
| `tools/lit_config.yaml` | **真正生效**的配置：方向（`automation.directions`）+ 期刊白名单（`journals`） |

也可以手填，重点是 `lit_config.yaml` 的这几段：

```yaml
journals:                      # 期刊白名单 = 检索的"范围边界"
  - {issn_l: "2058-7546", name: "Nature Energy", tier: T1}

tiers:                         # 档位：决定复筛阈值 / 精读认真度 / 是否被截断
  T0: {label: "正刊/权威综述", relevance_min: 0.40, ingest_depth: enhanced, uncapped: true}
  T1: {label: "大子刊",       relevance_min: 0.45, ingest_depth: enhanced, uncapped: true}
  T2: {label: "领域一区 top",  relevance_min: 0.80, ingest_depth: standard}
  T3: {label: "普通一区",      relevance_min: 0.90, ingest_depth: standard}
  T4: {label: "二区/专业刊",   relevance_min: 0.95, ingest_depth: light}
default_tier: T3

defaults:
  lookback_days: 7
  max_candidates: 20
  lower_tier_floor_factor: 0.5 # 截断时低档至少占 limit 的这个比例（0 = 旧行为，低档可能被挤成 0 篇）

dedup_sources:                 # 本机已有文献目录：扫过就不再重复下载
  - {id: "kb_raw", path: "raw", scope: "kb"}

automation:
  directions:
    - {slug: battery, label: 电池, limit: 15,
       query: "battery lithium sodium zinc electrolyte solid-state interphase"}
```

三条要记住的规则：

1. **期刊白名单是范围边界**：白名单为空 = 退化成全网关键词检索。
   要加刊**不要凭记忆写 ISSN**，用 `python tools/lit_journals.py --add "Nature Energy"` 解析。
2. **`tiers` 的阈值必须设在 `relevance()` 的评分下限（0.70）之上**，否则
   **永远无物可滤**、五档行为完全相同（分级形同虚设）。T0/T1 保持宽松是刻意的：
   顶刊召回优先，靠 `uncapped` + 增强精读兜底。
3. **`uncapped: true`** = 该档文献**不被 `--limit` 截断**（顶刊宁可多不能漏）。

### 6.1 阶段总览

| 阶段 | 命令 | 关键产物 | 退出码 |
|---|---|---|---|
| 0 体检 | `lit_doctor.py` | 问题清单、体检快照 | 0/1/2 |
| A 发现 | `lit_daily.py`（按配置方向）／`lit_discover.py`（单方向） | `daily/…/cand_<slug>.json` + `status.json` | daily 0/2/3/4 |
| A′ 摘要 | `lit_digest.py --render` | `daily/…/digest.md` | 0 |
| A″ 勾选 | `lit_digest.py --list` / `--pick` | `picks/…-picks.json`（**全字段，零损失**） | 0/2 |
| B 取全文 | `lit_fetch.py --in <picks> --outdir raw/pdf` | `raw/pdf/*.pdf` + 下载清单 | 0=至少一篇成功／**4=全部失败** |
| B′ 收编 | `lit_manual_import.py` | 手工下载的 PDF 改名入库 + 台账 | 0 |
| C 提取 | `lit_batch.py --extract` | `raw/text/…/<标题>.md` + `raw/assets/<slug>/fig_*.png` | 0 |
| D 建卡 | `lit_batch.py --ingest [--apply]` | `wiki/sources/*.md` **骨架** + 门禁报告 | 0=过／**1=写坏**／**2=缺补链** |
| E 收尾 | `lit_finish.py --apply` | `index.md` 行、`log_ops.md`、索引 | 0/1 |
| F 缺口 | `lit_gapscan.py` | 下一轮检索式（带出处与信号） | 0/1/2 |

### 6.2 逐阶段命令

**0 · 体检**

```bash
python tools/lit_doctor.py          # 46 项：配置 / 去重对账 / 欠账 / 索引 / 任务
python tools/lit_doctor.py --fix    # 安全修复
```

**A · 发现**

```bash
python tools/lit_daily.py            # 按配置里的方向各跑一轮（推荐）
python tools/lit_daily.py --dry-run  # 只看会跑什么
python tools/lit_daily.py --resume   # 今天被中断后续跑（跳过已成功方向）

python tools/lit_discover.py "固态电解质 界面" "近一周" --limit 20   # 单方向
```

**A′/A″ · 摘要与勾选**

```bash
python tools/lit_digest.py --render                   # 生成/重渲摘要
python tools/lit_digest.py --list                     # 列出可勾选 ID（形如 battery#3）
python tools/lit_digest.py --pick "battery#1,battery#3,oer#2-5"
python tools/lit_digest.py --pick all --min-rel 0.9 --only-oa
```

**B · 取全文**

```bash
python tools/lit_fetch.py --in raw/notes/lit-watch/picks/<日期>-<时分秒>-picks.json \
       --outdir raw/pdf --label "<方向>"
```

来源顺序：OpenAlex `oa_url` → Unpaywall → 出版社直链；逐条校验 `%PDF-` 魔数。
**拿不到的会写进下载清单**（含可点 DOI 与直链），你手工下载后走 B′。

**B′ · 手工下载收编**

```bash
python tools/lit_manual_import.py          # 干跑：看配对结果
python tools/lit_manual_import.py --apply  # 改名并移入 raw/pdf/
```

收件箱默认 `raw/pdf/Manual Download/`。未匹配的隔离到 `raw/pdf/_unmatched/`，**永不删除**。

**C · 提取（PDF → 文本 + 插图）**

```bash
python tools/lit_batch.py --reconcile   # 首次对账：判定哪些其实已提取
python tools/lit_batch.py --status      # PDF / 全文 / 卡片 三段各欠多少
python tools/lit_batch.py --extract --limit 5

python tools/lit_extract.py "<单个pdf>" --json   # 单篇
```

**D · 建卡**

```bash
python tools/lit_batch.py --ingest           # 干跑
python tools/lit_batch.py --ingest --apply   # 写骨架
```

**只建骨架，绝不替你写结论**：frontmatter 只用可核验元数据；作者取不到就留白并标
`> ⚠️ 信息缺口`；正文只有标题 + 摘要 + `## 待精读`。

写完后**自动跑骨架门禁**：

- **硬失败（退出码 1）**：frontmatter 不可解析 / 缺 `type` / `authors` 不是列表 /
  `sources:` 首条不是 `[[raw/...]]` / 回链文件不存在。
- **软失败（退出码 2）**：出站链接 < 2 或入站 = 0——页面本身完好，但**补链纪律未完成**。
  工具**不替你补链**（那会凭空造出错误关联），只把缺口列出来。
  **看到 2 就要去补链，别当成功。**

**E · 收尾**

```bash
python tools/lit_finish.py --since 2026-10-09            # 干跑
python tools/lit_finish.py --since 2026-10-09 --apply     # 写入 + 重建索引
```

它把新页插进 `wiki/index.md`、给 `wiki/log_ops.md` 追加一行、重建 BM25 索引。
**没跑语料／语义索引 = 新页搜不到**，命令末尾会提醒你。

**F · 缺口驱动下一轮**

```bash
python tools/lit_gapscan.py                 # 按「缺口严重度 × 页面重要性」排序
python tools/lit_gapscan.py --queries       # 只出检索式，直接喂回阶段 A
```

信号来自库自身：`evidence_base: single-source/secondhand`、`si_status: missing`、
正文里的 `⚠️ 单源论断 / 无实验验证 / 信息缺口`。

### 6.3 退出码怎么读（**重要**）

这批工具**用退出码当信号**，不是 0 就代表一切正常：

| 命令 | 退出码 |
|---|---|
| `lit_daily.py` | **0** 全成功 ／ **2** `--directions` 与配置不匹配 ／ **3** 有方向失败 ／ **4** 全失败 |
| `lit_discover.py` | 0 ／ **3** = 有分片失败 |
| `lit_fetch.py` | 0 = 至少一篇成功 ／ **4 = 全部失败** |
| `lit_ingest.py` 门禁 | 0 = 过 ／ **1 = 写坏** ／ **2 = 缺补链** |
| `lit_gapscan.py` | 0 ／ **1 = 降级**（索引读不到，权重会失真）／ 2 = 写盘失败 |

> ⚠️ **不要把「失败」读成「这个方向没有新文献」**——那正是这套退出码要防的事。

### 6.4 每天自动跑

调度**不在 MCP 范围**（MCP 协议没有调度器），请放在 OS 侧：

- **Linux/macOS（cron）**：`47 7 * * * cd /path/to/vault && python tools/lit_daily.py`
- **Windows**：任务计划程序调用一个包装脚本，把库根作为参数传入。

---

## 7. 挂到 AI 客户端（MCP）

```bash
pip install -r mcp/requirements.txt

python mcp/server.py --vault /path/to/my-vault                # stdio，只读工具
python mcp/server.py --vault /path/to/my-vault --allow-write  # 额外允许写工具
python mcp/server.py --list-tools                             # 不装 SDK 也能看清单
python mcp/server.py --selftest                               # CI 用
```

库根解析顺序：`--vault` 参数 > `MATSCI_KB_VAULT` 环境变量 > 当前目录。
目标不是知识库（缺 `tools/kb_lib.py`）会**拒绝启动**。

**客户端配置示例**（Claude Desktop / Claude Code）：

```json
{
  "mcpServers": {
    "matsci-kb": {
      "command": "python",
      "args": ["/path/to/matsci-kb-kit/mcp/server.py", "--vault", "/path/to/my-vault"]
    }
  }
}
```

**暴露 19 个工具**：

- **只读（默认可用）**：`kb_route`（首选）、`kb_search`、`kb_resolve`、`kb_where`、
  `kb_corpus_search`、`kb_graph`、`kb_backlinks`、`kb_stats`、`kb_tags`、`kb_dois`、
  `kb_cite`、`lit_batch`、`lit_gapscan`，以及诊断类 `kb_doctor`、`kb_lint`、
  `kb_selftest`、`kb_toolcheck`、`lit_doctor`
- **写（需双钥）**：`kb_build_index`——需 server 以 `--allow-write` 启动 **且** 调用方传 `apply=true`

---

## 8. 工具速查表

### 检索与索引（`kb_*`）

| 工具 | 用途 |
|---|---|
| `kb.py` | **统一入口**（bm25/语义/混合/route/corpus/doctor） |
| `kb_route.py` | ★ **分层上下文包** L1/L2/L3 不混排（Agent 首选） |
| `kb_search.py` | BM25 + 语义 + 混合检索 |
| `kb_build_index.py` | 构建／增量更新索引（`--full` `--lite` `--embed` `--stats` `--add`） |
| `kb_semantic_search.py` | 语义检索引擎（`--build` / `--add` / `--query` / `--hybrid`） |
| `kb_corpus.py` | raw 全文分块索引与检索（可回指行号） |
| `kb_where.py` | ★ 四目录完备检索（断言"库内没有 X"之前必跑） |
| `kb_graph.py` | 多跳推理／枢纽与桥接页 |
| `kb_backlinks.py` | 链接图分析 + 补链建议 |
| `kb_stats.py` | 统计仪表板 |
| `kb_cite.py` | GB/T 7714 引用格式化（`--copy` 到剪贴板） |
| `kb_dois.py` | 库内 DOI 清单（去重键之一，缓存增量） |
| `kb_tags.py` | 标签统计 |
| `kb_serve.py` | 常驻检索服务（可选加速器，`--warm` / `--status` / `--stop`） |

### 质检与自检

| 工具 | 用途 |
|---|---|
| `kb_lint.py` | 分级 lint：`--quick` / `--deep` / `--fix` |
| `kb_lint_deep.py` | 扩展检查族 A–F（由 `--deep` 调度） |
| `kb_toolcheck.py` | ★ **实跑**每个工具的 `--selftest`/`--help` + 编译 + 写盘防呆 |
| `kb_selftest.py` | 底座不变量自检 |
| `kb_lib.py` | 共享库（被其它工具导入） |
| `qc_base_check.py` | 5 个 Bases 视图选中集合重算 + 漂移守门 |
| `qc_evidence_base.py` | 机械判定 concept/topic 页的 `evidence_base` |
| `qc_schema_check.py` | frontmatter schema 校验 |

### 文献流水线（`lit_*`）

| 工具 | 用途 |
|---|---|
| `lit_doctor.py` | 流水线体检（46 项，`--fix` 安全修复） |
| `lit_daily.py` | 每日发现（配置驱动、可续跑） |
| `lit_discover.py` | 单方向检索（tier 阈值、分片并行、翻页） |
| `lit_digest.py` | 摘要渲染与勾选 |
| `lit_fetch.py` | 取 OA 全文（含 SI 尽力抓取） |
| `lit_manual_import.py` | 手工下载 PDF 收编入库 |
| `lit_batch.py` | 批量提取／建卡的欠账台账（单篇失败不中断整批） |
| `lit_extract.py` | 单 PDF 图文提取（原子写） |
| `lit_ingest.py` | 建卡骨架 **＋ 骨架门禁** |
| `lit_finish.py` | 入库收尾（index.md / log_ops.md / 索引） |
| `lit_gapscan.py` | 缺口扫描 → 下一轮检索式 |
| `lit_catalogue.py` | 去重目录构建（缓存增量） |
| `lit_journals.py` | 期刊白名单维护（`--groups` / `--add` / `--list`） |
| `lit_report.py` | 归纳报告生成 |

> ⚠️ **运行产物落点**：`raw/notes/lit-watch/`（由 `lit_config.yaml: paths.runs_dir` 与
> `kb_lib.lit_runs_dir()` 派生）。逐阶段详表见技能 `lit-watch`。

---

## 9. Sci-Assistant 决策层

> **v0 全量完成 2026-10-21** ｜ 12 个 `sci_*` 工具 ｜ 3 大核心能力

Sci-Assistant 是基于知识库的**科研课题辅助系统**——从切入点发现、实验方案设计到进展追踪，形成"知识→决策→行动→反馈"的闭环。

### 三大核心能力

| # | 能力 | 场景 | 工具 |
|---|---|---|---|
| **C1** | **切入点发现** | 已有大方向（如"电解液设计"），找未被充分探索的细分点 | `sci_landscape.py` `sci_gap_scan.py` `sci_topic_rec.py` |
| **C2** | **实验方案推荐** | 确定切入点后，设计实验路线 | `sci_method_extract.py` `sci_protocol_gen.py` `sci_lab_match.py` `sci_method_chain.py` |
| **C3** | **课题进展统筹** | 实验推进中，记录、分析、调整 | `sci_progress.py` `sci_data_analysis.py` `sci_ecsa_qc.py` `sci_review.py` |

### 设计原则

1. **证据链不可断**：任何推荐/参数必须能回指 source 卡或原文
2. **事实型输出**：不生成"优势/适用条件"等判断，判断层单独走 LLM + quote 校验
3. **写前备份**：覆盖固定落点文件前自动备份
4. **自检纪律**：所有工具带 `--selftest`（总计 178 项）

### 实测案例

- **电解液设计方向（C1）**：200 卡候选 → 10 个子方向 → 9 个空白信号 → 5 个切入点（2 high）
- **锌电解液方案（C2）**：3 个候选方法对比，参数逐条带 quote，32 条判断 0 失败
- **ECSA 重算与复盘（C3）**：失效案例重算，5 条建议 6 条证据 0 失败

详见 [`docs/SCI-ASSISTANT.md`](docs/SCI-ASSISTANT.md)。

---

## 10. 常见问题排错

**Q：`--doctor` 报「嵌入索引不存在」**
正常。语义检索是**可选增强**。想要就 `pip install sentence-transformers` 后
`python tools/kb_semantic_search.py --build`。

**Q：搜索返回 0 命中，但库里有页面**
99% 是**忘了重建索引**：`python tools/kb_build_index.py`（增量，秒级）。

**Q：改了页面但检索看不到变化**
同上——索引是**派生数据**，改完必须重建。

**Q：报告 `[ERROR] broken wikilink: [[...]]`**
链接目标不存在。检查路径拼写；记住 wikilink 有两种目标（页面链接查**页面名集合**，
`[[raw/...]]` 资源链接查**文件系统**），混用会被误报。

**Q：页面在 Obsidian 里好好的，却从 Bases 视图里消失了**
frontmatter 被写坏（最常见：长字段含冒号**没加引号**）。
跑 `python tools/kb_lint.py --quick` 与 `python tools/qc_base_check.py --check`。

**Q：`lit_ingest --apply` 退出码是 2，是不是失败了？**
不是写坏，是**补链没做完**（出站 < 2 或入站 = 0）。工具刻意不替你补链。去补链后重跑。

**Q：`lit_fetch` 退出码 4**
**全部下载失败**（不是"没有新文献"）。看 `downloads/manifest-<时间戳>.md` 里的清单手工下载，再走 B′。

**Q：`lit_fetch` 提示 Unpaywall 回退被跳过**
`lit_config.yaml: datasource.mailto` 为空。填**你的真实邮箱**可进 OpenAlex 礼貌池
（更快、更少 429）。**绝不编造联系地址**——假的比留空更糟。

**Q：刚建的空库跑 `lit_doctor` 一堆 ❌**
空库正常态（期刊白名单为空、方向未配）。用 `kb-onboard` 配好后自然消失。

**Q：能把整个库目录改名/搬家吗？**
可以。所有工具用 `__file__` 派生库根，**不写死任何路径**。

**Q：需要一直开着 `kb_serve` 吗？**
不需要。它是**可选加速器**：在跑就用（更快），不在跑就退化为进程内执行。

**Q：索引可以删吗？**
可以。`wiki/.index/` 是纯派生数据，`rm -rf wiki/.index && python tools/kb_build_index.py` 即可重建。

---

## 11. 设计要点（为什么这么做）

- **库根靠 `__file__` 派生**：所有工具不写死库路径，所以整个目录可随意改名／迁移／复制。
- **空库也必须能启动**：`kb_build_index.py` 在 0 页面时**产出合法的空索引**，
  于是 `kb_search` / `kb_route` 返回「0 命中 + low_confidence」而**不是崩溃**。
- **「索引存在但为空」≠「索引不存在」**：前者正常，后者是真故障。
  用静默空结果掩盖真故障比报错更危险，所以索引缺失时**明确报错**。
- **索引是派生数据**：`wiki/.index/` 可随时重建，已进 `.gitignore`。
- **元数据静默丢失是本类库的头号失效**：所以 frontmatter 一律走 `kb_lib` 的解析／重组函数，
  长字段含冒号必须加引号。
- **校验装置与生成装置必须同源**：导出／修复脚本复用同一套解析器，不另写"差不多"的实现
  ——宽松的校验器等于没有校验器。
- **写盘脚本一律默认干跑**：要有 `--apply` 才写；写前备份、写后复算（写 N 页要能读出 N 页）。
- **退出码是信号**：不把「失败」静默成「没有结果」。

---

## 12. 给维护者：生成物 vs 手写件

本仓库的很多文件是**由一份源知识库经 `build/build_kit.py` 过滤 + 去个人化生成的派生数据**。

| 类别 | 文件 | 怎么改 |
|---|---|---|
| **生成物** | `tools/**`、`skills/**`、`CLAUDE.md`、`docs/METHODOLOGY.md`、`docs/TOOLS.md`、`kit.yaml` | ❌ **勿手改**；改真源后重跑生成器 |
| **手写件** | `build/**`、`mcp/**`、`scripts/**`、`README.md`、`LICENSE`、`NOTICE.md`、`pyproject.toml`、`requirements*.txt`、`docs/GETTING-STARTED.md`、`docs/ARCHITECTURE.md`、`docs/MCP.md`、`scaffold/**` | ✅ 直接改 |

生成物文件头都有醒目横幅：

```
# ── GENERATED by matsci-kb-kit build/build_kit.py — DO NOT EDIT (真源见 kit.yaml) ──
```

**重新生成**：

```bash
python build/build_kit.py                 # 用默认源库生成到本仓库根
python build/build_kit.py --src <库根> --out <kit根>
python build/build_kit.py --check         # 只跑泄漏扫描
```

三条架构不变量：

1. **`--out` 不得落在 `--src` 内**（硬门禁，防止把生成物写回真源）。
2. **生成后全树泄漏扫描**（`build/rules/leak_denylist.txt`），任一命中即**构建失败**。
3. **漂移可见**：`scrub` / `drop_sections` 规则若在真源找不到目标会**告警**；
   残留泄漏由第 2 条兜底为失败。

规则文件在 `build/rules/`：`include.txt`（白名单）、`exclude.txt`（排除审计）、
`scrub.yaml`（字面→替换去个人化）、`drop_sections.yaml`（`CLAUDE.md` 块级替换）、
`leak_denylist.txt`（fail-closed 扫描）。

**验证**（改完 `build/` 必跑）：

```bash
python scripts/verify_kit.py     # 泄漏扫描 + py_compile + --help + 空库冒烟 + MCP
```

CI 在每次 push／PR 跑同一条命令（`.github/workflows/verify.yml`）。

`kit.yaml` 记录了生成溯源：源 commit、生成时间、工具清单与**逐文件 sha256**。

---

## 许可

- **代码**（`tools/**`、`mcp/**`、`scripts/**`、`build/**`）：**MIT**，见 [`LICENSE`](LICENSE)。
- **方法论文档**（`CLAUDE.md`、`docs/**`、`skills/**`、`scaffold/**`）：建议 **CC-BY-4.0**（署名即可自由使用／改编）。
  详见 [`NOTICE.md`](NOTICE.md)。

工具链的最初构想来自 [karpathy/llm-wiki](https://github.com/karpathy/llm-wiki)。
`lit_report.py` 与 `kb-onboard` 技能由早期项目 **lit-watch-workflow** 并入并去分叉。
