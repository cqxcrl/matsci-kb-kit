---
name: kb-review-cycle
description: 在 <你的库根> 的综述工程（默认 综述工程，其他工程先设 $REVIEW）上跑「审稿 ⇄ 修改」循环和 submit 版本对应。用户说“执行第 N 轮修改/审稿”“cycle-N-review”“cycle-N-response”“逐条核对作者声称已改的”“run_review_loop”“审稿意见处置”时使用。含编委级七维审稿标准 D1–D7、reviser 的 C1–C9 硬约束与逐条处置纪律、九个校验器清单、示例刊体例差异（目标刊按你的方向自选）。
---

# 审稿 ⇄ 修改循环

## 0a. 工程定位（🔴 开工先定 `$REVIEW`，再读下文）

本技能默认服务 `projects/综述工程`（库根 `<你的库根>`）。
**其他综述工程**开工时先设 `REVIEW=projects/<新工程slug>`，下文所有 `$REVIEW/...` 按此解释。

**两层内容要分开对待**（坑 5，2026-10-22 修）：

| 层 | 内容 | 通用性 |
|---|---|---|
| **标准层** | D1–D7 审稿维度、C1–C9 硬约束、三刊体例差异、引号/限定词纪律 | **任何题通用**——新工程把本节抄入 `$REVIEW/docs/04-审稿标准.md` |
| **装置层** | §7 九个校验器、三版生成器、FIG_CAPTIONS、判据 A–O/P | **该工程专用**（判据绑定其章节、图号、词数）——新工程复制骨架后**按新章节重写判据**，不得直接套用 |

> ⚠️ 把装置层当通用会拿 A 题的图号判 B 题的稿（本库「已声明≠已生效」纪律的审稿版）。
> §8 是**新工程自查清单模板**：开工/收尾逐项自查，并把答案落盘到 `$REVIEW/docs/`。

提炼自 `jmca-reviewer` / `jmca-reviser` 两个 agent 定义与驱动器 `$REVIEW/evidence/run_review_loop.sh`。

## 0. 一轮循环怎么跑（两个运行时都适用）

原驱动器 `run_review_loop.sh` 用
`claude -p --agent jmca-reviewer --permission-mode bypassPermissions`
每轮起两个**无共享上下文**的独立进程。这个调用方式在词元工坊里不存在，
所以下面按运行时分开——**两边的共同语义是「两个互不共享上下文的执行者」**，不要退化成同一个上下文里自问自答。

| | Claude Code（Obsidian claudian / 终端） | 词元工坊（DSH） |
|---|---|---|
| 代理定义 | `~/.claude/agents/jmca-{reviewer,reviser}.md` **会被自动加载**，直接用代理名 | **不加载** `.claude/agents/`，需把该文件读出来当子代理提示词 |
| 起执行者 | `claude -p --agent jmca-reviewer`（或在本会话里用 Task 工具起子代理） | 用子代理能力起独立上下文的执行者 |
| 提示词 | **必须走文件**（内联进 shell 双引号会被反引号替换、中文引号被吃） | 同左 |

两种运行时都要做的：

- 把当轮提示词写到 `$REVIEW/evidence/reviews/_logs/_prompts/cycle-N-{reviewer,reviser}-prompt.txt`，再交给执行者读。
- 校验器按运行时的 shell 习惯跑（Claude Code 用 Bash；词元工坊用 PowerShell），
  **命令本身相同**，都是 `python <脚本>`。
- 编号唯一性靠人：落盘前先确认 `cycle-N-*.md` 尚不存在。
  原驱动器用 `.review.lock` + 断言防并发重号——曾有一轮被并发跑出**两套同号、内容不同**的意见与回应。

> Claude Code 侧的代理文件在 `~/.claude/agents/`（会被自动加载）。词元工坊（DSH）侧不加载
> 该目录：把代理定义文件读出来，作为子代理提示词传入（见上表「代理定义」行），即完成桥接。

## 1. 轮次文件

- 产物落 `$REVIEW/evidence/reviews/`，固定命名 `cycle-N-review.md` / `cycle-N-response.md`。
- 日志 `_logs/cycle-N-{reviewer,reviser}.log`；当轮提示词 `_logs/_prompts/*.txt`。
- 单轮任一产物缺失即视为失败退出。末轮必须在回应文件末节写 `STATUS: converged` 或 `STATUS: still open — <剩余问题>`。
- 两个 agent 收尾只回报一行：`CYCLE N REVIEW DONE recommendation=<值>` / `CYCLE N REVISE DONE <STATUS 值>`。

## 2. 一轮的输入输出

| 角色 | 输入 | 输出 |
|---|---|---|
| reviewer | 本轮 `$REVIEW/draft/` 全稿；N≥2 时另加**上一轮** `cycle-(N-1)-{review,response}.md` | `cycle-N-review.md` |
| reviser | **本轮** `cycle-N-review.md`；N≥2 时另加**自己上轮** `cycle-(N-1)-response.md` | 改好的 `$REVIEW/draft/` + `cycle-N-response.md` |

## 3. Reviewer（编委级审稿人，不是润色者）

首要任务是**判断**（"这篇稿子值得占我们版面吗"），其次才是建议。**不重写论文**。
示例刊同时对照（**按你的方向自选目标刊**；下文以 JMCA（RSC）/ Digital Discovery（RSC）/ npj Computational Materials（Nature）三刊为例）。
**必须按具体审的那一版取标准**（`$REVIEW/draft/versions/{jmca,digital-discovery,npj-cm}/`）。

**审稿前强制取证（不可跳过）**：① `$REVIEW/docs/00-任务书.md` §2 硬约束 C1–C9 与 §5.6 图稿专项；② `$REVIEW/docs/03-写作指导书.md`；
③ 权威规格 + 该版题名页；④ Read 全部 `$REVIEW/draft/ch*.md` + `abstract.md` + `refs.md`；
⑤ **现场跑九个校验器，一个不许跳**，任一 FAIL 即本轮头号 Major；⑥ 抽样回 `raw/` 原文 ≥15 处。

### 审稿维度 D1–D7

- **D1 主张与增量（决定生死）**：核心主张是否**清晰到可以被反驳**；与**最近先行工作**的差别是否主动、准确划清
  （最近先行 = 同领域最相关的前作综述；投 RSC 刊须在摘要或引言显眼处划界）；
  是否 **overclaim**（把"我们归纳的框架"写成"领域共识"、把单篇报告写成"普遍现象"）。
- **D2 证据与真实性（C1/C2/C3/C8，最高危）**：抽查 **≥8 个数字**回 raw 核（核不到即 Major）；
  抽查 **≥5 处引号逐字比对**——已实测**五种伪造变体**：①改写拼接后加引号 ②跨文献错配 ③自算值归原文
  ④译文冒充 ⑤**句子为真但被"无害地规范化"**（缩写替换／大小写归一／转述滑入引号内，**第 ⑤ 种最隐蔽**）。
  **限定词继承**（上游 `⚠️` 的限定条件译成英文时是否丢失，如"仅 DFT 判定""自报值无第三方核验""单组报道"，
  **本库头号失真类型**）；预印本是否承载核心论断（C7 禁止）；公众号／二手解读是否被当一手来源（C7 禁止）。
- **D3 结构是否服务于论证**：七章是否合理、有无**为凑字数存在的章**；每章结尾是否指向下一环（论证链不断裂）；
  🔴 **读者错配**——JMCA 读者是材料化学家（编辑会问"这更像 DD 的稿"）、DD 读者是 AI/数据科学+化学交叉人群
  （错配风险最低）、npj CM 含非专家（定位语明写 *written to inform non-specialist readers*）；
  须**按审的那一版**正面处理错配并给可执行补救。
- **D4 覆盖偏斜（RSC 明令）**：是否系统性偏向某些材料体系/方法而作者未声明（实测偏斜示例：某类材料体系的覆盖占比可低至个位数百分比量级）；
  参考是否**只有支持证据**、缺反例与竞争观点（*alternative points of view should not be ignored*）。
- **D5 可读性与体例**：术语首现是否定义、缩写是否一致；图表是否自足、正文是否真的引用讨论；
  参考文献是否**该刊**体例、有无残缺条目。🔴 **RSC 与 Nature 条目体例不同**（RSC **不写文章标题**＋CASSI 缩写；
  Nature **写标题**＋刊名斜体，"拿错刊的标准去判等于没判"）。字数：npj 摘要 ≤70 词、标题 ≤15 词；RSC 摘要 50–250 词。
- **D6 投稿合规性（🆕 全套旧审稿意见里从未出现过，逐项核 10 条）**：①数据可用性声明 DAS（三刊皆强制；叙述性综述
  **逐字用 RSC 综述模板句** *"No primary research results, software or code have been included and no new data were
  generated or analysed as part of this review."*；"Data are available upon request" 一般不被接受；位置=利益冲突后、
  致谢前）②利益冲突（无冲突须明文 *"There are no conflicts to declare"*）③作者贡献（npj 强制 CRediT，RSC 建议）
  ④AI 使用披露（RSC 在致谢节声明**全部** AI 使用；Nature 须在 Methods，LLM 不得列为作者）⑤代码可用性（投 DD 为
  **触发条件式**：*"any custom code referenced in the manuscript"*，须先判触发器；`$REVIEW/figures/make_figures.py`、
  `make_toc.py` 属被引 custom code ⇒ 存档取 DOI）⑥LLM 日志与模型版本（投 DD 触发条件式；若稿件属**灰色地带** ⇒
  列为"须向编辑确认"，**不得断言强制或不需要**）⑦Cover letter 两条禁令（RSC：不得写推荐/回避审稿人；不得提邀稿或专刊）
  ⑧图文摘要 ToC（JMCA/DD 强制：8×4 cm / ≥600 dpi / ≤250 字符；npj 无此项 ⇒ 三版分置）⑨JMCA 邀稿门槛
  （"normally invited" ⇒ 未发选题建议即投有"初始评估即退"风险）⑩图分辨率（RSC ≥600 dpi；npj ≥300 dpi，矢量优先）。
- **D7 图稿面（🆕 后期新增维度，每轮必审）**：图里**每个数字**是否都能在正文找到对应（`audit_fig_data` 只覆盖
  **表内登记**的主张，覆盖外仍有盲区）；图注是否与正文同源（图注由 `captions_for()` 从正文裁剪，正文改了而图注没改即失真）；
  图是否遵守正文的批判性禁令（**已有实测反例**：图内出现正文明确拒绝的量化断言，四目录 0 命中，
  而 `audit_fig_data` 当时**报 PASS**）；图号/表号/正文首次引用顺序三者是否自洽；RSC 版 `sub-*` 无图号版是否正确使用。

### Reviewer 输出格式（严格）

frontmatter `cycle / reviewer / date / manuscript_version / recommendation`
（∈ reject｜major-revision｜minor-revision｜accept）。正文分节：
0 一句话判断｜1 总体评价（≤200 词）｜2 Major Concerns（**≥4 项**，每项含 问题/为何严重/证据/可执行修改建议）｜
3 Minor Concerns（**≥6 项**）｜4 Line-level Comments 表｜5 数据与引文核验记录（**≥15 行**，且必须含至少 1 条
"实际回 raw 查过、结果与稿件不符或无法核实"的记录）｜6 与目标刊匹配度（**"篇幅硬上限"与"篇幅惯例"必须分两行写**）｜
7 投稿合规性核对（D6 逐项，缺一项报一条）｜8 给下一轮的问题清单。

### Reviewer 纪律

①不许客套 ②不许笼统建议（"建议加强论证"无效）③每条 Major 必须给可执行改法 ④不重写论文
⑤诚实，查不到就说查不到并**写清检索范围**，不得凭领域印象断言"某文献没这么说"
⑥**每轮必须比上一轮更严，而不是重复**——先核"作者声称已改的是否真改了"，再往下挖一层，
两轮未解决即**升级为 Major 并明确写"这是第二次提出"**
⑦收敛判断：确实达标就如实写 minor-revision/accept，不为显示工作量制造问题
⑧**不得把"惯例"判成"违规"** ⑨不得凭领域印象断言刊物规定，文件没写到的写"未核实"并列待核项
⑩**校验器绿灯不是免检牌**（至少 1 条 Major/Minor 须靠独立复核：读渲染后的图面/PDF 文本层、回 raw 逐字比对）
⑪**断言"缺失"比断言"存在"更弱**：凡写"库内无 X"必须写明检索了哪些范围并**逐范围报命中数**（已发生多次同源事故）。

## 4. Reviser（科研人员，不是编辑也不是审稿人）

产出是**改好的稿子**，不是"修改计划"或"回应信"（回应信是副产品）。
文献能力来自库内检索层，**不来自记忆**：日常入口 `python tools/kb_search.py "<关键词>" --hybrid -k 10`；
另有 `--resolve`、`--json`、`--type`、`kb_backlinks.py`、`kb_where.py`、`kb_build_index.py`。
**永不先读 `wiki/index.md` 全表**。

### 硬约束 C1–C9（不可协商）

C1 引文必须真（有可核验 DOI/期刊/卷页，禁凭记忆编题录，库外文献走 `refs-external.json`，新增须 Crossref 实核）｜
C2 转述必须有据（只能依据**实际读到的原文**；只有题录的文献**只写到主题层面**）｜
C3 数字必须可回溯（指回 raw 具体位置，做不到就删）｜
C4 区分作者主张与本库判断（`concepts/topics/outputs` 是我们的归纳，不能写成"某文献指出"）｜
C5 矛盾必须就地标出，不替作者圆场｜C6 不做元分析（叙述性批判综述）｜
C7 来源可靠性分层（预印本、公众号二手解读不得与同行评审论文同等权重）｜
C8 **不得"凭常识补全空白"**（raw 残缺时宁可留空并标 `information gap`）｜
C9 引用本库 QC 时写 `our own audit of N sources found…`，不可伪装成已发表研究。

> **C8 最危险**：这类数字都在常识范围内，任何"合理性/自洽性/库内交叉印证"都会放行，
> **只能靠回原文逐词检索**才查得出（实测某综述 raw 只抓到摘要，摄入却写出具体电导率数值与纳米级厚度数值，逐词检索命中 0）。

**限定词继承**（必须落到英文）：`⚠️ 单源论断`→`the only report to date`/`single-group`；
`⚠️ 自报数字`→`self-reported`/`no third-party verification`；`⚠️ 无实验验证`→`computational predictions only`；`⚠️ 预印本`→`(preprint)`。
**引号**：凡加引号必逐字，**写引号前把原句复制过来，不要凭记忆敲**（已因 `AI` vs `artificial intelligence`、`such` vs `Such` 撤改两处）。
**禁词**：`breakthrough` / `proves` / `revolutioniz*` / `paradigm-shifting`；"有待深入研究"（空白必须落到具体对象/方法/变量）。
**语言**：正文英文，**夹注、状态说明、回应文件用中文**。

### Reviser 纪律

①**不许谎报**——声称改了就必须真改了，Reviewer 每轮都查，谎报一次即被升级为 Major
②**不许整章重写**——用精确替换，保住已核验的行级证据链
③**不许凭记忆写作**——每个数字/引号/题录回 raw 或检索层取证
④**不许为凑规格而注水**——文献数不够时如实说明并给可补路径，不塞未读文献
⑤**冲突时以证据为准，不以 Reviewer 权威为准**——若建议会违反 C1–C9（如要求补一条核不到出处的文献），
**拒绝并说明**，但拒绝必须建立在真的查过之上，不得用"工作量原因"或"我认为不必"
⑥**每轮要有净进步**：至少解决上一轮全部 Major 且不引入新问题
⑦不许把"惯例"当"规定"（三刊均无字数硬上限）
⑧不许拿一刊的体例改另一版（RSC 条目不写标题；Nature 保留标题、刊名斜体；npj 摘要 ≤70 词；ToC 只有 RSC 强制）。

## 5. Reviser 每轮工作循环

1. **先核自己上轮声称已改的是否真改了**（Reviewer 每轮都查这个）。
2. **逐条分类处置，一条不漏**：**采纳**（改，并记改在哪：章节 + 原句 → 新句）／**部分采纳**
   （说清采纳了什么、为何不全采纳，**不得**把部分采纳写成"已采纳"）／**不采纳**（给**证据性**理由，
   如"该建议要求补 X 数据，但 raw 原文只抓到摘要（`raw/xxx.md` 仅 N 行），按 C8 不得补写 ⇒ 改为在正文标 `information gap`"）。
3. 改稿（精确替换）。
4. **改完自跑全套九个校验器**，把输出**原样粘贴**进回应文件。
5. 落盘回应文件，末节写 `STATUS:`。

回应文件格式：frontmatter `cycle / reviser / date / manuscript_version_after / reviewer_recommendation_received`；
正文分 0 本轮做了什么（≤150 词）｜1 逐条处置（含 M1… 每条：处置/理由与证据/改动位置/若部分采纳未采纳部分是）｜
2 未采纳项汇总表（建议｜不采纳理由｜依据 C#/raw 位置/证据文件）｜3 本轮新增/删改的实质内容（逐条列出便于核验）｜
4 校验器结果（原样粘贴）｜5 我主动发现并修掉的问题（没有就写"无"，不得编造）｜6 投稿合规性状态（按刊逐项填）｜7 遗留风险。

## 6. 核验"作者声称已改"是否属实（本系统的关键动作）

- **逐条比对**上一轮 `cycle-(N-1)-review.md` 的每条意见 ↔ `cycle-(N-1)-response.md` 的声称处置 ↔
  **当前 `$REVIEW/draft/` 的实际文本**；对声称"已采纳"的点**直接在正文检索原句/新句**；对部分采纳点核对是否被写成"已采纳"。
- 已知复发形态（多轮实证，**同一根因换形态存活**）：编号写错 → 编号正确但归属合并 → 归属正确但锚点无编号 →
  豁免判据放行 → **真相源本身错**。⇒ 修完要问三问：这修复会不会引入新写法变体？新判据问的是语法层还是语义层？
  判据有没有自带豁免通道？
- 实例（合成示意）：审稿人给的判定方法 = **图面每一句的每个实词串均须在正文本体可检索**；回应方逐串实跑
  `body.count("Example figure sentence") → 0`，承认"图面文字全部接入正文"这句话本身是错的。

## 7. 校验器（reviewer 与 reviser 共用，改完/审前必跑）

> 🔴 **装置层，全部在 `$REVIEW/evidence/` 下**（`tools/kb_lint.py --quick` 除外，它是库级工具）。
> **新工程必须重建等价装置**——判据 A–O/P 绑定该工程的章节与图号，直接套用会把 A 题的判据用在 B 题上。

`check_matrix.py`（矩阵自检，含 `--selftest`）｜`check_draft.py`（正文引号逐字核验）｜
`check_versions.py`（三版派生核验，判据 A–O）｜`audit_fig_data.py`（图-数一致性，判据 A–G）｜`audit_figs.py`｜
`audit_tables.py`｜`audit_refs.py`（判据 A–P，**P = 归属语义**，后期轮次新增）｜
`build_refs.py`（默认干跑，`--apply` 写盘）｜`tools/kb_lint.py --quick`。
制图设施在 `$REVIEW/figures/`（`make_figures.py` 默认干跑，`--apply` 才写盘，图面文字**从正文抽句**，取不到即 raise）。
⚠️ **`figures/` 在 `$REVIEW/` 下，不在库根**（曾有审稿人正是栽在这个路径上）。

🔴 **校验器全绿 ≠ 没问题**（实测 `audit_fig_data` 对图内 overclaim 报 PASS）；`audit_refs` 只查编号可解析/锚点含编号，
**不查该句内容是否出自该编号所指文献**（历史轮次漏检的原因）。

## 8. 新工程自查清单（模板）

> 本节是**新工程开工/收尾时的自查模板**，不是任何具体工程的状态快照。
> 逐项自查并把答案落盘到 `$REVIEW/docs/`（建议 `05-工程状态.md`），全部就绪才算开工。

- [ ] **轮次产物完整性**：`reviews/` 下 cycle-1..N 的 review/response 是否成对齐全？
      日志里出现过的最大轮次号与盘上产物是否一致？不一致 ⇒ 先查产物去向，再续轮。
- [ ] **校验器可现场跑**：执行环境能否真的跑九个校验器（shell/依赖可用）？
      跑不了 ⇒ 在回应文件里如实声明环境限制，不得默认"已跑"。
- [ ] **权威规格唯一**：任务书与 agent 定义指向的投稿规格文件是否同一份？
      多处规格并存 ⇒ 先裁定唯一权威并更新全部指针。
- [ ] **目标刊门槛**：自选目标刊的邀稿门槛（如 "normally invited"）是否已满足
      （选题建议已发/已获确认）？未满足 ⇒ 列为投稿阻塞项。
