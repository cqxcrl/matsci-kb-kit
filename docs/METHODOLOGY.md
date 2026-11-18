# CLAUDE.md — 知识库 Schema

> **配置中枢**。常驻上下文只放「每次都要用」的东西：库的骨架、不可违背的铁律、入口与指针。
> 流程细节按需加载项目技能。
> **本文件不写会过期的统计数字**——一切以命令输出为准。

## 〇、怎么读这个文件

- **落点**看 §一，**流程**看 §三，**写页**看 §二/§五，**踩坑**看 §六，**其余**看 §七 索引表。
- 常用口径：页数 `python tools/kb_stats.py`；Bases `python tools/qc_base_check.py`；
  索引 `python tools/kb.py doctor`。
- 文中日期只标注**规则生效日**，不是现状快照；冲突时以工具输出与代码为准。
- 项目技能随插件发布在 `skills/`，在插件级注册；`kb_init` 不复制 skills 进 vault，
  库内无 `.claude/skills/` 属正常。改技能内容请改插件 `skills/` 下的文件。

## 一、库的骨架

| 目录 | 层 | 职责 |
|---|---|---|
| `wiki/` | 知识层 | `concepts/` `entities/` `sources/` `topics/` `outputs/` `experiments/` ＋ 根下元文件 `index.md` `tags.md` `log*.md` ＋ `.index/`（派生，可重建） |
| `raw/` | 资料层 | `pdf/`（含 `si/`）`text/`（全文提取）`clippings/` `assets/` `notes/`（运行产物） |
| `tools/` | 工具层 | `kb.py` 统一入口；`kb_*` 检索、`qc_*` 质检、`lit_*` 文献获取 |
| `projects/` | 工程层 | 可选：与知识层分离的写作 / 工程；项目卡 `projects/*/sources/` 可进检索层 |
| `_archive/` | 归档层 | **只移不删**，登记册 `_archive/README.md` |

**库根只允许**：上表 5 目录 ＋ 基础设施（`.obsidian/` `.git/` `.claude/` `.dsh/` `.claudian/` `.qc/`）
＋ `_scratch/` ＋ 根文件（`CLAUDE.md`、`*.base`）。**不得为新流程开新目录**：
运行产物 → `raw/notes/`；临时/派生/工作区 → `.qc/`；历史件 → `_archive/`；脚本 → `tools/`。
`_scratch/` 与 `.dsh/` 不计入知识层（`_scratch/backup/` 是在用备份，不可整目录清理）。

⚠️ 根下 `*.base` 是 Obsidian **Bases** 核心插件，不是 Dataview（仅 `--with-obsidian` 建库时适用）。

## 二、页面规范

**命名**：中文或英文，空格用 `-`；实体/概念按主题命名，来源页以来源标题命名（`YYYY-标题`）。

**Frontmatter**（每个 wiki 页必备）：

```yaml
---
created: YYYY-MM-DD
updated: YYYY-MM-DD        # 每次实质性编辑时更新
type: entity | concept | source | topic | output | experiment
tags: [tag1, tag2]
aliases: [别名]
summary: "一句话摘要"
sources:
  - "[[sources/某来源.md]]"
---
```

- `evidence_base`（concept / topic 专属）：`strong | mixed | single-source | secondhand`，
  由 `python tools/qc_evidence_base.py` **机械判定，勿手填**；综述引用按此判权重，
  `single-source` 的结论不得写成领域共识。
- `source_url`（source 专属，**必填**）：`https://doi.org/<DOI>` → arXiv → 官网原文。
  只认 frontmatter `doi:` 或 raw 原文中的 DOI，**不得用正文里被引文献的 DOI**（会指错论文）。
- `authors_source`：仅当作者值库内不可回溯时写，声明实际出处；**不得**因此抹掉已正确的作者值。
- 长字段含冒号必须整体加双引号（`summary` / `authors` / `institution` / `published` 等），
  否则 YAML 把冒号后当新键，**整页元数据丢失**。

**正文**：`# 标题` → 一句摘要 → `##` 分块 → 术语首现 `[[wikilink]]` → 必要时 `## 参见` / `## 参考`。
**Wikilink**：库内 `[[相对路径/文件名]]`，跨页用最短可用路径，等价概念用 `[[note|显示文本]]`。

## 三、三条工作流

### Ingest（摄入）

1. **读**来源；不读不写摘要。
2. 与用户确认 3–5 个关键要点。
3. 建 `wiki/sources/<标题>.md`（摘要 300–500 字）：`sources:` **首条**必须是
   `"[[raw/<子目录>/<原始文件名>]]"`（带 `[[ ]]`、含子目录、不能只写文件名）——这是摄入统计的唯一依据。
   同时写 `source_url`。
4. **证据化二次加工**：`kb.py lit enrich request --page sources/X.md` → 外部 LLM 提交 proposal →
   默认干跑、确认后 `--apply`。每条 claim 必须有指定行内逐字 quote；机器加工不等于精读。
5. 更新实体/概念页（无则建；冲突标 `> ⚠️ 矛盾：`）。新建/大改 concept、topic 后
   `python tools/qc_evidence_base.py --apply`。
6. **作者门禁**：写 `authors` / `corresponding_author` / `institution` 前确认 raw 确有作者栏；
   没有就留白并标 `> ⚠️ 信息缺口：raw 无作者信息栏`，**不得凭印象补写**。
   跑 `qc_author_gate.py`，缺声明用 `qc_author_gate_apply.py --apply`；
   AI 分析报告类来源页一律 Crossref / OpenAlex 反查。
7. **补链**：每个新页出链 ≥2、入站 ≥1（先 `kb.py search "<主题>" -k 8` 找互链对象）。
   孤立页是检索质量头号杀手。
8. **收尾**：更新 `wiki/index.md` → `kb.py index build`（按影响面加 `embed` / `corpus`）→
   追加 `wiki/log_ops.md`（`## [日期] ingest | 标题`）。
9. **汇报**：把新建/大改的页面列成可点击 wikilink 清单；纯路径或纯文本标题＝未完成。

> 🔴 重提取已有 Extract 会丢原标题：`lit_extract --force` 的 H1 取输出 stem。
> 必须从备份恢复 H1，并逐行 diff 正文确认零差异。

**SI 强制（不按 tier）**：研究论文有 SI 的一律随主文取回；取不到必须写进手动下载清单，
**每条附可点击链接**；clipping 与综述不挂 `si_status`。判据只看原文（两套编号都要认）。
命令、命名三档与三家直链见技能 `lit-watch` §B″。

### 更正：先做全库同源检索

1. 就地改。2. `python tools/qc_same_text.py "<表述>"`（数字用 `--num`）扫全部副本，逐条判断
同源（一并改）vs 同词不同义（不动）。3. `log_ops` 记「改 N 处，名单外 M 处」。

### Query（查询）

简单事实 `kb.py ask --strategy simple`；比较/机制/争议/多子问题 `--strategy agentic`；不确定 `auto`。
读候选与 L2/L3 原文定位后综合作答，附 `[[页面]]` 与必要行号；有长期价值 → 问是否存 `wiki/outputs/`。
**只有全貌浏览才读 `wiki/index.md`**。完整协议（分层、多跳、自适应深度）见技能 `kb-query`。

### Lint（健康检查）

| 模式 | 用途 |
|---|---|
| `--quick` | 只查最近 ingest，跳过 O(全库) |
| `--deep` | 全库 17 项 ＋ 扩展族 A–F |
| `--deep --fix` | 干跑预览可机械修复项 |
| `--deep --fix --apply` | 落盘（自动备份 `.qc/backups/YYYYMMDD/`） |

- 改任何 lint/校验脚本 → `kb_lint.py --selftest` 与 `--selftest-deep`
  （**每个** `qc_*` 的 `--selftest` 也须跑）；底座 `kb_selftest.py`。
- 工具「实际能否运行」用 `kb_toolcheck.py`（实跑），必须**静止态**：并发写盘会被记成工具「意外写盘」。
- A–F 明细、自动修复边界、日期修复纪律见技能 `kb-lint`。
- 报告落 `wiki/outputs/`，追加 `log_ops.md`；人工抽查矛盾/过时/孤立/缺失/缺口 + **证据标记未继承**。
- 「待精读」骨架卡缺 `诚实边界`/`批判性评估` 是真实欠账，**不得在 lint 层豁免**。

## 四、工具、索引与视图

- **唯一入口 `kb.py`**；参数一律 `python tools/kb.py tools --json`（AST 静态生成，不执行被扫描脚本），
  不要凭记忆猜冷门脚本参数。旧 `kb_search.py` / `kb_route.py` 等是薄兼容层；
  需要旧分层包时用 `kb.py route`。
- ⚠️ `kb.py tools --json | python …` 在 Windows 会 `JSONDecodeError`（管道按 GBK 解码 UTF-8）：
  改为重定向到文件 ＋ `python -X utf8` 读取；**不要**改 `kb.py` 的编码。
- **常驻服务**：多次检索前 `kb.py serve start --warm`；`serve status` / `stop`；
  `kb.py doctor --check-reranker` 检查索引新鲜度与真实精排加载。端点表见 `docs/TOOLS.md`。
- **索引是派生数据**：`index build`（秒级，改页后必跑）/ `index embed`（语义）/ `index corpus`（原文块）；
  `doctor` 检查页面集合、同名哈希与语料哈希。
- **断言「库内无 X」必跑** `python tools/kb_where.py "X"`：跨四目录、**逐目录报命中数**。
  写明检索范围 ≠ 范围完备。
- **项目卡已进检索层**，但 lint/stats 的口径不同（lint 只数 wiki 页），引用时说明用哪个口径。
- **Bases**（仅 `--with-obsidian` 建库时适用）：五个 `*.base` 是 frontmatter 的下游视图，字段缺失或 YAML 写坏会让页面**静默消失**。
  改任何 `.base` 后必跑 `python tools/qc_base_check.py`；报缺字段就回去补 frontmatter，
  **不要改视图过滤器**（视图无法「重建」，过滤器被误改会静默收窄）。

## 五、写作与批判

**来源页三层**：① 作者主张 ② `## 诚实边界`（作者承认的局限）③ `## 批判性评估`（摄入者的质疑，**不可省略**）。
核查：有无同行评审（预印本须标注）、有无人类基线、自报数字是否自洽、「多次独立复现」是否真的独立。
原则：**保留原值、标出疑点**；不替作者圆场，不把单篇主张写成领域共识（frontmatter 可加 `source_reliability`）。

**批判性标记**（就地贴，每条写明为什么可疑）：

| 标记 | 触发 |
|---|---|
| `> ⚠️ 矛盾：` | 两处对同一事实说法不一 |
| `> ⚠️ 单源论断：` | 只有一篇支撑、未独立复现 |
| `> ⚠️ 自报数字：` | 作者自报性能/占比/提速比，无第三方核验 |
| `> ⚠️ 预印本：` | arXiv/bioRxiv 等未经同行评审 |
| `> ⚠️ 无实验验证：` | 纯计算/DFT 结论，无合成或表征佐证 |
| `> ⚠️ 二次引用失真：` | 转述比原文更强或数字无出处 |
| `> ⚠️ 立场相关：` | 主张与作者平台/路线/商业利益相关（描述，非指控） |
| `> ⚠️ 体裁提示：` | 综述/评述/公众号文，证据强度天然较低 |
| `> ⚠️ 范围漂移：` | 用相邻领域成果为本文领域背书 |
| `> ⚠️ 信息缺口：` | 关键前提在可见材料中无从判定 |

写法：块引用 `> ⚠️ 类型：…` 或列表项内 `**⚠️ 类型：**…`，同页一致。
范例：`> ⚠️ 矛盾：frontmatter 标 Sci. Adv. 2021，正文却是 Nat. Energy 2020`。
**宁可少标，不可把作者的正常局限写成「可疑」**。

**始终做**：建页即更新 `index.md`；术语首现建 wikilink；主动交叉引用；改页更新 `updated`；增量编辑；
中文写作（术语可英文）；`log_ops` 每次操作一行，方法论洞察进 `log_insights`；
**`wiki/log.md` 已冻结**，新记录一律进 `log_ops.md`；
**手动下载/待取条目一律附可点击链接**（只给标题或裸 DOI＝未完成）。

**不要做**：改 `raw/` 任何文件；删已有页面（除非用户明确要求）；猜测来源内容；
未读原文就写摘要；破坏 YAML 格式。

**写盘铁律**：① `--apply` 开关、默认干跑；② 写前用**同一解析器** `kb_lib.split_frontmatter` 复核，
不另写宽松正则；③ 写前备份 `.qc/backups/YYYYMMDD/`，**写后复算**（写 N 页要读出 N 页）；
④ 运行前与独立实现对总数，不一致先怀疑工具。frontmatter 重组只走 `join_frontmatter`。

## 六、已知陷阱

> 前三条是**任何会话都可能踩、且静默丢数据**的跨切面陷阱，常驻全文；其余按「常驻面包屑 ＋ 细则按需」组织。

- 🔴 **元数据静默丢失**（本库头号失效）：页面能开、正文可读，索引里整个消失，人工浏览看不出。
  读用 `kb_lib.read_text`，拆/合用 `split_frontmatter` / `join_frontmatter`（唯一出口）。
  写后 `yaml.safe_load` 或 `kb_lint --quick`；**闭合 `---` 后必须有换行**。
- **换行 CRLF/LF 混合**：不要对换行做假设；读文件二进制解码 UTF-8 再归一化。
- **委托纪律**：「已声明」≠「已生效」——委托前确认运行时真的加载该文件（技能只在库根被发现）。
- **解析器与 YAML 对账**：改解析/写盘代码后跑 `python tools/kb_selftest.py --dual-parser`
  （全量含项目卡、逐值对账，列表不一致算硬失败）。抽样自检不算验收。
- **链接两类解析器**：页面链接查页面名集合，资源链接查文件系统；代码块内 `[[...]]` 是示例，须剔除。
- **`qc_*.py` 不得手写 `.qc/…`**：写用 `qc_work_dir(create=True)` / `qc_file`，读用 `qc_input`；
  `MATSCI_QC_DIR` 可覆盖。写盘脚本若用 `required=True`，`--selftest` 会到不了，须在 `main()` 内校验。
- **判「某页无出处」前**：枚举该页全部 raw 并区分体裁（剪藏常无作者栏，公众号常带通讯栏）。
- **`sources:` raw 回链是摄入统计唯一依据**：漏写＝该资料被误判「未摄入」（写法见 §三 Ingest）。
- **图谱 / 项目卡**：项目卡 `sources/index.md` 不进图谱（`iter_project_page_files()` 排除，
  补链须写进会被扫描的页面）；`kb_graph` 读 `wiki/.index/meta_full.json`，改页后先 `index build`；`isolated`（无边）≠「零入站」（有出链无人引）。
- **校验器纪律**（细则技能 `kb-lint`，含 E4 豁免与 `_HEDGE_PAT`）：正则/计数判定须能对已知答案反算、夹具含正反例、每坑追加回归夹具、修前记基线修后逐类解释。
- **`authors` 三重校验**：`safe_load` 通过 ＋ 值为 list ＋ 每项无结构破坏字符；**撇号不是脏值**。
- **批次文件**：动 `batches_v2.json` / `batch_done.json` 前先确认格式版本（技能 `kb-ingest-batch`）。

## 七、细则索引

| 要做的事 | 去哪看 |
|---|---|
| 文献流水线本地约定（路径/产物/分级/去重） | 技能 `lit-pipeline` |
| 文献发现→下载→建卡全链、SI 判定全表 | 技能 `lit-watch` §B″ |
| 浏览器兜底下载 | 技能 `lit-browser-fetch` |
| 检索协议（分层/多跳/自适应深度） | 技能 `kb-query` |
| lint 扩展族与校验器纪律 | 技能 `kb-lint` |
| QC 核查循环 / 审稿—修改循环 | 技能 `kb-qc-loop` / `kb-review-cycle` |
| 批次 ingest 与版本兼容 | 技能 `kb-ingest-batch` |
| 工具清单、常驻服务端点 | `docs/TOOLS.md` |

---
_本工具链基于 [karpathy/llm-wiki](https://github.com/karpathy/llm-wiki) 的构想，由用户和 Agent 共同演化。_
