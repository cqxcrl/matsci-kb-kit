# CLAUDE.md — 知识库 Schema

> 本文件是本知识库的配置中枢：定义页面结构、约定，以及 ingest/query/lint 三大工作流。
> 由 matsci-kb-kit 提供，随你的库一起演化。

---

## 🔴 项目技能索引（按需加载）

本工具链的工作流细节已抽出为**项目技能**。本文件常驻上下文，技能只在触发时进入上下文
⇒ **做对应工作前先加载对应技能，不要凭本文件的摘要硬做。**

`lit-pipeline` 文献流水线本地约定 ｜ `lit-watch` 文献发现→下载→建卡全链 ｜
`lit-browser-fetch` 浏览器兜底下载（自动取全文失败后补正文与 SI） ｜
`kb-query` 库内检索与作答 ｜ `kb-lint` 健康检查与补链 ｜ `kb-onboard` 建库访谈

🔴 **技能真源在 `.dsh/skills/`**；`scripts/kb_init.py` 会同时复制一份进 `.claude/skills/`
（Claude Code 只从后者发现项目技能）。技能仅在**项目根**被发现。

---

## 目录结构

**顶层 5 个目录**（页数 / 文件数一律以工具实算为准，本文件不写死数字）：

| 目录 | 层 | 说明 |
|---|---|---|
| `wiki/` | 知识层 | `concepts/` `entities/` `sources/` `topics/` `outputs/` `experiments/`（实验方案，`type: experiment`）＋ 根下**元文件** `index.md` `tags.md` `log*.md` ＋ `.index/`（派生数据，可重建）。页数见 `python tools/kb_stats.py` |
| `raw/` | 资料层 | `pdf/` `text/`(全文提取 md) `clippings/`(剪藏) `assets/`(正文图) `notes/`(运行产物)。`pdf/` 与 `text/` 可按学科分子目录 |
| `tools/` | 工具层 | `kb.py` **统一入口**（`ask/search/route/corpus/resolve/stats/doctor/index/serve/lit/qc/sci/lint/toolcheck/tools/selftest`）｜ `kb_*.py` 检索层（含 `kb_rag.py` 传统 RAG、`kb_agentic.py` Agentic RAG、`kb_serve.py` 常驻服务、`kb_manifest.py` 静态工具清单）｜ `qc_*.py` 质检层 ｜ `lit_*.py` **文献获取层**（含 `lit_enrich.py` 证据化二次加工、`lit_si.py` 补充材料判定/获取、`lit_browser_fetch.py` 浏览器兜底） |
| `projects/` | 工程层 | 可选：与知识层分离的写作 / 工程（综述稿、科研辅助等）。项目卡可进检索层，但与 wiki 统计口径不同 |
| `_archive/` | 归档层 | **只移不删**；建议分组 `restructure/` `lit-watch/` `qc/` `retired/`(含隔离区 `quarantine/`) `scratchpad/` |

> 🆕 **不计入知识层的两个目录**：`_scratch/`（gitignored 工作区，存备份 / 任务草稿 / 绘图中间件）
> 与 `.dsh/`（项目技能真源）。
> ⚠️ `_scratch/` 下若有**在用备份**，不可当临时垃圾整目录清理。

⚠️ 根下 `*.base` 是 Obsidian 核心插件 Bases，**不是** Dataview（两者语法不同，勿混）。

> **工具链全部用 `__file__` 派生库根**：库文件夹改名、整体搬迁都不需要改任何脚本。

## 页面规范

### 文件命名
- 使用中文或英文，空格用 `-` 连接
- 实体/概念页面以主题命名：`wiki/entities/张三.md`、`wiki/concepts/深度学习.md`
- 来源页面以来源标题命名：`wiki/sources/2024-某论文标题.md`

### Frontmatter（YAML 头）
每个 wiki 页面必须包含：

```yaml
---
created: YYYY-MM-DD
updated: YYYY-MM-DD        # 每次实质性编辑时更新
type: entity | concept | source | topic | output | experiment
tags: [tag1, tag2]
aliases: [别名1, 别名2]     # 便于 wikilink 引用
summary: "一句话摘要"        # 用于 index.md
sources:                    # 引用来源
  - "[[sources/某来源.md]]"
---
```

**按页面类型附加的字段**：

```yaml
# —— concept / topic 页专属（2026-09-25 新增，QC 建议 1）——
evidence_base: strong | mixed | single-source | secondhand
#   该页结论的「证据承重」。取值由 tools/qc_evidence_base.py 机械判定（勿手填）：
#     strong        一手源 ≥5、无二手无预印本、其中同行评审 ≥2
#     mixed         一手源 ≥2 且二手占比 <1/3
#     single-source 有效一手源 ≤1
#     secondhand    二手源占比 ≥1/3
#   ⇒ **综述引用时按此判权重**；读到 single-source 的结论不得写成领域共识。

# —— source 页专属 ——
source_url: "https://doi.org/…"   # 🆕 2026-10-06：**每个 source 页必填**的可点击原文链接
#   取值优先级：① 真实 DOI → `https://doi.org/<DOI>`；② arXiv 预印本 →
#   `https://arxiv.org/abs/<id>`；③ 微信公众号/其他 → 官网原文 URL。
#   ⚠️ 只接受 **frontmatter `doi:` 字段**或 raw 原文中定位到的 DOI，**不得用页面正文里
#   被引文献的 DOI**（会把链接指到别的论文）。新增 source 页须同步回填，缺失会被 lint 拦下。
authors_source: "…"   # 仅当 authors 值**库内不可回溯**时写，声明其实际出处
#   触发条件：raw 回链中检索不到作者/单位信息栏（publisher HTML 剥空等）。
#   ⚠️ 此时**不得**把已正确但无出处的作者值抹掉——应保留并加此字段声明不可追溯。
#   AI 分析报告类来源页，作者/通讯字段**一律须走 Crossref / OpenAlex 反查**。
```

> 🔴 **为什么加 `evidence_base`**：`source_reliability` 在 source 页几乎全覆盖，
> 但综合页（concept/entity）没有地方记录「这条结论的来源可靠到什么程度」。
> 批判性纪律**全部为 source 型页设计**，从未定义综合页如何承载限定词
> ⇒ 限定词在 `source → concept` 这一跳**必然丢失，因为综合页没有地方记**。
> 该字段就是那个「地方」。

### 页面内容结构
- 以 `# 标题` 开头
- 开篇用一句摘要（紧跟标题）
- 用 `## 二级标题` 组织板块
- 关键术语首次出现时用 `[[wikilink]]`
- 底部如有必要加 `## 参见`（交叉引用）
- 如有需要加 `## 参考`（外部链接）

### Wikilink 约定
- Vault 内用 `[[相对路径/文件名]]`，如 `[[entities/张三.md]]`
- 跨页面引用优先使用最短可用路径
- 等价概念用 `[[note|显示文本]]`

---

## 操作流程

### Ingest（摄入新资料）

触发：用户说 "处理这个"、"ingest"、"消化这份资料" 等。

1. **读取**来源文件
2. **对话讨论**：提炼 3-5 个关键要点，与用户确认重点
3. **创建来源页面**：`wiki/sources/<标题>.md`（摘要 300-500 字 + 关键要点 + 连接）。
   - **必须写 raw 回链**：`sources:` 字段**首条**写 `"[[raw/<子目录>/<原始文件名>]]"`
     （**带 `[[ ]]`，含子目录，不能只写文件名**）。这是摄入统计的唯一依据，漏写即被误判「未摄入」。
   - **必须写 `source_url`**：可点击原文链接（`https://doi.org/<DOI>` / arXiv）。取值只认
     frontmatter `doi:` 或 raw 原文 DOI，**不得用正文里被引文献的 DOI**。`lit_ingest.py` 已自动带。
   - `lit_ingest` 骨架须再做**证据化二次加工**：`kb.py lit enrich request --page sources/X.md` 生成请求，
     外部 LLM 提交 proposal，`apply` 默认干跑、确认后 `--apply`。每条 claim 必须有指定行内逐字 quote；
     机器加工后仍须人工复核，不能冒充精读。
4. **更新实体/概念页面**（无则建、冲突标 `> ⚠️ 矛盾：`、改则 `updated`）。
   **新建/大改 concept、topic 页后重算 `evidence_base`**：`python tools/qc_evidence_base.py --apply`
5. **作者字段门禁（必做）**：写 `authors`/`corresponding_author`/`institution` 前先确认
   **raw 原文确有作者栏**。未落库 → **强制留白并标 `> ⚠️ 信息缺口：raw 无作者信息栏`**，
   **不得凭印象补写**；已有值但库内不可回溯 → 保留值 + `authors_source` 声明。
   跑 `qc_author_gate.py` 复查、`qc_author_gate_apply.py --apply` 补声明。
   AI 分析报告类来源页 → 一律走 Crossref / OpenAlex 反查。
6. **强制补链（不可省略）**：每个**新建**页面出链 ≥2、**且**入站 ≥1（在既有页补 `[[新页面]]`）。
   先 `kb.py search "<主题>" -k 8` 找互链对象。孤立页是检索质量头号杀手。
7. **更新 `index.md`** → 8. **刷新索引** `kb.py index build`，并按影响面跑 `index embed` / `index corpus`
   → 9. **追加 `log_ops.md`**（`## [日期] ingest | 资料标题`）
   → 10. **向用户汇报时，把本次新建/大改的卡片与页面用 wikilink 列成可点击清单**
   （如 `[[sources/2026-xxx.md]]`、`[[concepts/yyy.md]]`）——**只给路径或纯文本标题＝未完成**。

#### 🆕 更正流程：更正任何数字/表述前必做「全库同源检索」

> QC 实测**一个更正平均有 3–7 处副本，其中常有 1–3 处在批次名单之外**。

1. 就地修正你正在编辑的那一处
2. **`python tools/qc_same_text.py "<被修正的表述>"`**（数字用 `--num`）—— 扫全部副本；
   逐条判断同源副本（一并改）vs 同词不同义（不动）。默认已排除 `wiki/log.md` 与 `.index/`
3. `log_ops.md` 记下：改了 N 处，其中**名单外 M 处**（M 就是本流程的价值）

### Query（查询）

触发：用户提问。

**统一入口 `kb.py`，不要先读 `index.md` 全表**：

1. **简单事实**用 `python tools/kb.py ask "<查询>" --strategy simple --json`；
   **比较/机制/争议/多子问题/证据核验**用 `--strategy agentic`，不确定用 `auto`。
2. 传统 hybrid 为 **BM25 + 向量 → RRF → 本地 CrossEncoder → Top-K**；精排失败必须显式报错，不得静默降级。
   也可显式 `kb.py search "<关键词>" --mode hybrid -k 10 --json`。
3. Agentic 返回有界步骤、分层去重证据、gaps 与 `synthesis_request`，由调用方模型综合，不内置外部 LLM。
4. **阅读**关键候选与 L2/L3 原文定位，**综合回答**附 `[[页面名]]` 和必要的原文行号。
5. 有长期价值 → 询问是否存 `wiki/outputs/`。

> 仅「全貌浏览」时才读 `wiki/index.md`。进阶协议见技能 `kb-query`。

### 检索层工具（tools/）

全部工具与参数用 `python tools/kb.py tools --json` 静态生成；该命令不导入或执行被扫描脚本。
旧 `kb_search.py` / `kb_route.py` / `kb_semantic_search.py` 等是薄兼容层，新调用优先 `kb.py`。

**🔴 兼容分层证据包**：

```bash
python tools/kb.py route "固态电解质 界面 稳定性" --budget 5,5,8
python tools/kb.py route "<查询>" --layer 1
python tools/kb.py corpus "<原文字段>" -k 8 --json
```

分层**不是**为了好看：L1 是「本工具链的当前综合」，L3 是「某篇论文某一段的字面表述」，
可信度不是一回事，混排会让 Agent 把二手综合当一手证据用。
输出含 `signal.top_score` 与 `low_confidence`——**BM25 没有分数下限，任何查询都会凑满 k 条**，
不给出这个信号就无法区分「命中」与「凑数」。

**完整工具表与选型规则见技能 `kb-query`（检索层）与 `kb-lint`（质检层）。**
此处只留三条**不可由 `--help` 推导**的要点：

- 🔴 检索首选 `kb.py ask/search`；需要旧分层包时用 `kb.py route`，查询类问题**不要**先读 `index.md` 全表。
- 🔴 断言「库内无 X」**必跑** `python tools/kb_where.py "X"`（跨四目录、**逐目录报命中数**；见 §已知陷阱 的「四目录完备检索」）。
- 🆕 **项目卡已进检索层**（2026-10-22）：`projects/*/sources/*.md` 会被 `kb_search` / `kb_route` / `kb_graph` / 语义索引命中。
  ⚠️ **统计口径已分裂，勿混用**：`kb_lint.py` 的页面扫描仍**只数 wiki 页**（`iter_page_files` 默认 `include_projects=False`）；
  而 `kb_stats.py` 读 `meta_full.json`，**已把项目卡计入**（2026-10-24：1099 页＝wiki 934 ＋ 项目卡 165，其中 source 842）。
  新建卡后跑一次 `kb_build_index.py`（全量扫描会带上；`--add` 需给库根相对路径）。
- 🆕 **`kb.py tools --json | python …` 在 Windows 下会 `JSONDecodeError`**：不是输出不合法，
  而是管道另一端按 GBK 解码 UTF-8。改为**重定向到文件 ＋ `python -X utf8` 读取**；
  **不要**为此改 `kb.py` 的编码。
- 各脚本用法以 `python tools/<脚本>.py --help` 或 `--stats` 为准，本文不赘列。

**文献获取层（`lit_*.py`）**：五阶段流水线与去重、期刊分级细节见技能 `lit-pipeline`。
配置唯一来源 `tools/lit_config.yaml`（路径一律相对库根）。

##### 🔴 SI（补充材料）随主文下载 —— 强制，不按 tier（2026-10-22 定规）

**下载任何一篇文献时都必须先判「它有没有 SI」**；**研究论文有 SI 的一律随主文取回，
取不到必须进手动下载清单**；综述/评论若确无 SI 则不下。工具：`tools/lit_si.py`。

1. **判存在（判据只能是原文）**：`python tools/lit_si.py scan "<PDF>"`
   —— 逐页扫 `supporting/supplementary information|data|materials`、
   `Electronic supplementary information`、`Supplementary material for this article`、
   `SupportingFile: <文件名>`，并**二次核验 `Fig. S#` / `Table S#` 引用**。
   有声明**或**有 S-编号引用 ⇒ 有 SI；两者皆无 ⇒ `not_applicable`。
2. **先自动取**：`python tools/lit_si.py fetch "<PDF>" --apply`。
   可直接推直链的**只有三家**：Nature/Springer（`static-content.springer.com/.../MediaObjects/...`，
   年份取卡片 `year:`，DOI 里的 `026` 是截断值）、Elsevier（`ars.els-cdn.com/...-mmc1.docx`，
   PII 走 Crossref；**不过 Cloudflare**）、Wiley（文件名从 PDF 的 `SupportingFile:` 读，
   拼 `action/downloadSupplement?doi=…&file=…`）。RSC/ACS/Science/IOP 对脚本 403/302 ⇒ 进清单。
3. **失败必须进清单**：`lit_fetch` 会把「有 SI 但没取到」写进手动下载清单的
   **📎 SI 待手动下载**小节（带 DOI、SI 专题页、Wiley 文件级直链）。**不得静默跳过。**
   🔴 **小节里每一条都必须带可点击链接**，只写标题不算（见 §通用规则·始终做）。
4. **写进卡**：`present`（已取）/ `missing`（有 SI 未取，**必须在清单里**）/
   `not_applicable`（**核查后**判定无 SI，不是"没查"）。

⚠️ **不准用机读字段代替原文判断**：Crossref `relation` 对实测 18 个 DOI **全为空**；
Europe PMC `hasSuppl` 对 `inEPMC=N` 的文章**一律返回 `N`**——实测 4 篇白纸黑字的 SI
被判成"没有"。**判据只能是原文。**
⚠️ **按「有没有 SI」判，不按「是不是综述」判**：综述也可能有 SI（Chem. Soc. Rev. 2026 即为一例）。

##### 🆕 期刊分级 / 去重源 / 自动收尾（2026-10-06）

- **期刊分级**：白名单每刊带 `tier: T0..T4`，驱动**检索阈值**与 **ingest 档**
  （T0/T1=enhanced 增强精读、不被 `--limit` 截断）。详见技能 `lit-pipeline` 与 `tools/_README.md`。
- **两道红线**：`kb_lib.load_lit_config` 必须**透传** `tiers`/`default_tier`（漏则分级静默失效）；
  `discover()` 的 OpenAlex `source.id` OR 列表**上限 100**（101+ 报 400）⇒ 白名单须**分片检索后合并**。
- **去重源**：`lit_discover` 阶段A 去重键 = 本机文献目录 ∪ 库内 DOI 清单，
  扫描源由 `lit_config.yaml: dedup_sources` 给出（详情见技能 `lit-pipeline`）。
- **自动收尾**：`lit_ingest.py --apply` 写页后**自动**重跑去重清单（`refresh_dedup()`，幂等）；
  加 `--with-index` 连 `kb_build_index.py` 一起建。

#### 🔴 常驻服务：Agentic RAG 的**前提**，不是优化项

**99.9% 的时间花在进程初始化上**（`import sentence_transformers` 8.3s + 模型 12.9s），
真正的计算是亚毫秒级。一次「查询分解 + 多跳 + 交叉比对」要 5–20 次检索，用 CLI 是 5–19 分钟纯等待
（实测 BM25 冷启动 820ms→常驻 177ms；语义 30s→231ms；混合 56s→480ms）。

```bash
python tools/kb.py serve start --warm            # 启动（放后台）
python tools/kb.py serve status                  # 或 serve stop
python tools/kb.py doctor --check-reranker       # 索引新鲜度 + 真实精排加载
```

接口（全部 GET + JSON；`/graph` 于 2026-10-21 加入）：

| 端点 | 用途 |
|---|---|
| `/health` `/stats` | 服务/索引状态（含 `graph_loaded`） |
| `/search?q=&k=10&mode=bm25\|semantic\|hybrid` | 检索（含 type 过滤） |
| `/ask?q=&strategy=auto\|simple\|agentic` | 自动选择传统 RAG 或 Agentic RAG（返回 `kb.rag.v1` / `kb.agentic.v1`） |
| `/resolve?q=` | 别名解析 |
| `/route?q=&budget=5,5,8&no_corpus=1` | **分层上下文包**（L1 综合 / L2 文献卡 / L3 原文，不混排；`no_corpus=1` 跳过 L3） |
| `/corpus?q=&k=8` | raw 全文分块检索 |
| `/graph?node=<页名>&hops=1` | 知识图谱邻域（`direction=out\|in\|both`、`type=`、`limit=`；`truncated` 明示截断） |
| `/graph?path=A,B` | 最短**有向**路径（沿出链） |
| `/graph?hubs=1&top=20` | 入度最高枢纽页（**条数用 `top`**，不是 `limit`） |
| `/graph?bridges=1&top=20` | 割点=图谱骨架页 |
| `/graph?stats=1` | 节点/边/连通块/孤立页计数 |

> `/graph` 的邻域与枢纽结果已与 `kb_graph.py` CLI 文本输出逐条对齐（2026-10-21 实测 156/156 邻居一致）。
> 2026-10-24 起 BM25/meta 索引签名变化会自动重载索引并清空图缓存；`&reload=1` 仍可用于强制重载。

必记的三条指令（不可由 `--help` 推导）：

- **改完任何 lint/校验脚本后必跑** `python tools/kb_lint.py --selftest`（**每个** `qc_*` 的 `--selftest` 亦须跑，见 §校验器自检纪律）。
  底座自检：`python tools/kb_selftest.py`。⚠️ 写盘类脚本若用 `required=True` 必填参数，
  **会让 `--selftest` 到不了**（argparse 先报缺参）⇒ 须在 `main()` 内显式校验。
- 断言「库内无 X」**之前必跑** `python tools/kb_where.py "X"`（跨四目录、**逐目录报命中数**，见 §已知陷阱）。
- 更正流程必跑 `python tools/qc_same_text.py "<被修正的表述>"`（数字用 `--num`，见 §操作流程）。

> 🆕 **QC 工作目录（`.qc/`）的解析规则**（2026-10-05 起强制，见 `kb_lib.qc_work_dir`）：
> **`qc_*.py` 一律不得手写相对路径 `.qc/…`**。原 `.qc/` 已在结构精简中迁至
> `_archive/qc/qc-working/.qc/`，硬写相对路径会因父目录不存在而**运行即崩**。改用：
> - `qc_work_dir(create=True)` / `qc_file(..., create=True)` —— **写盘**输出，落**库根 `.qc/`**
>   （该目录按需创建，已在 `.gitignore` 内）；`create=True` 时若解析到归档层会直接报错，
>   防止把产出写进只进不出的 `_archive/`。
> - `qc_input("queue.json")` / `qc_input("LEDGER.md")` —— **读真源**，优先库根、缺失回退归档。
> - 环境变量 `MATSCI_QC_DIR` 可整体覆盖（最高优先级）。
>
> 🔴 **重组 frontmatter 必须走 `kb_lib.join_frontmatter(fm_text, body)`**，不要手写
> `"---" + fm + "\n---" + body`：该写法在两个工具里各犯过一次（开围栏缺换行、闭合缺换行），
> 后果是 frontmatter **静默解析不出来**——本工具链代价最高的一类失效（详见 §已知陷阱）。

> ⚠️ **索引是派生数据，不是知识**（`wiki/.index/` 可随时重建）。修改/新建页面后跑一次 `kb_build_index.py` 即可（增量，秒级）。
> 改了页面后若用到语义/原文检索，还需 `kb.py index embed` 与 `kb.py index corpus`；
> `kb.py doctor` 会检查页面集合、同名内容哈希与语料文件哈希，`--check-reranker` 验证真实模型加载。

### 数据库视图（`*.base`）

五个 Obsidian **Bases** 文件（核心插件，**非 Dataview**）——frontmatter 的**下游消费者**，
字段缺失或 YAML 写坏，页面会**从视图中静默消失**且 Obsidian 不报错。

- **现规模**：各 `.base` 当前选中数**一律以 `python tools/qc_base_check.py` 为准（本文件不写死数字）**。
- 🔴 **改任何 `.base` 后必跑** `python tools/qc_base_check.py`——重算选中集合 + 漂移检测
  （`.base` 是**视图**不是数据，无法「重建」；视图级过滤器被误改会**静默收窄**，
  曾致总览视图大幅收窄且无任何报错）。该工具已挂进 `lit_ingest` 收尾链，建卡后自动跑。
- 📖 **过滤范围表、Bases 语法要点、维护纪律见

### Lint（健康检查）

触发：用户说 "lint"、"检查"、"健康检查" 等。

0. **先跑分级 lint 工具**（**2026-10-05 起 deep 与 quick 定位明确分离**）：

   | 模式 | 定位 | 内容 |
   |---|---|---|
   | `--quick` | **效率优先** | 只查最近 ingest 的页面；跳过 O(全库) 项 |
   | `--deep` | **全面优先，不追求速度** | 全库全量检查：既有 17 项 ＋ **扩展检查族 A–F**（见技能 `kb-lint`），并支持 `--fix` |

   - `python tools/kb_lint.py --quick` 快速检查最近 ingest 的页面
   - `python tools/kb_lint.py --deep` 全库详尽检查
   - `python tools/kb_lint.py --deep --fix` **附加修复**：对可机械修复项**干跑预览**（不写盘）
   - `python tools/kb_lint.py --deep --fix --apply` **真正落盘**（自动备份到 `.qc_backup_YYYYMMDD/`）
   - `python tools/kb_backlinks.py --suggest` 看孤立页/弱连接页 + 补链建议
   - 索引新鲜度：`python tools/kb_build_index.py --stats`
   - 🔴 **工具「实际能否运行」用** `python tools/kb_toolcheck.py`（**实跑**每个工具的
     `--selftest`/`--help` + 写盘防呆 + 编译检查）。**这是 E 族的执行层**——
   - **改动 lint/校验工具后必须跑** `kb_lint.py --selftest` 与 `--selftest-deep`。

   > 📖 **扩展检查族 A–F 明细表、各族的自动修复边界、日期修复器的「宁可不修」纪律，
   > 见技能 `.dsh/skills/kb-lint/SKILL.md`**（避免与技能重复）。

1. 读 `wiki/index.md` 获取全貌
2. 抽查页面，检查：**矛盾 / 过时 / 孤立 / 缺失 / 缺口**，以及
   **🆕 证据标记未继承**（`kb_lint` 的 `check_evidence_inheritance` 自动检测
   「本页复述了上游带限定标记的数字、却没有承接表述」——**这是 QC 实证的头号失真类型**）
3. 生成 Lint 报告到 `wiki/outputs/`
4. 追加 log_ops.md：`## [日期] lint | 发现 X 个问题`

#### 🔴 三条工具级纪律（浓缩）

1. **断言「某表述/数字在库内缺失」前，必做「四目录完备检索」**（`raw/`、`wiki/`、
   `projects/综述工程/references/`、`projects/综述工程/`），
   并**逐目录报命中数**——用 `python tools/kb_where.py "X"`（自带 `--selftest` 事故回归夹具）。
   *教训*：曾三处独立检索都断言某文不在库内、且**都写明了范围**——但范围只有 `raw/`+`wiki/`，
   而全文一直在 `references/` 内。**写明了范围，反而让错误的「0 命中」显得可信。**
2. **判「某页无出处」前枚举该页全部 raw 并区分体裁**（剪藏常无作者栏、公众号常带通讯栏）。
3. **`authors` 三重校验**：`yaml.safe_load` 通过 ＋ 值为 list ＋ 每项无结构破坏字符
   （反斜杠/双引号/换行）。⚠️ **撇号不是脏值**（`D'Souza`/`Gryn'ova` 是正当姓名）。

> 📖 完整论证、第二实例、以及四条可迁移方法论见
> 因为它从不被写出来、因而不被审查；对「缺失」的断言天然弱于对「存在」的断言。**

---

---

## 通用规则

### 始终做
- ✅ 创建页面时自动更新 `index.md`
- ✅ **完成 ingest 后，把本次新建/大改的卡片与页面以 wikilink（`[[sources/…]]`、`[[concepts/…]]`）列成可点击清单**——纯路径/纯文本标题不算完成
- ✅ **凡是要用户「手动下载 / 手动去取」的条目，必须附可点击链接**（DOI ／ PDF 直链 ／ SI 页面或文件级链接）。
  手动下载清单、文献清单的「待下载」行、任务书里的欠账表，**一律适用**——
  **只给标题、或只给裸 DOI 文本 = 未完成**。连 DOI 都没有时，给按标题的可点击检索链接并注明原因。
  代码侧已有守卫：`lit_fetch` 写清单后**逐条复算**是否含 `](http`，缺链打印 `[warn]`。
- ✅ 每次操作后追加 `log_ops.md`（格式：`## [日期] <操作> | <描述>`）
- ✅ 如有方法论洞察，同步追加 `log_insights.md`
- ✅ 修改页面时更新 `updated` 字段
- ✅ 首次引入术语时创建 wikilink
- ✅ 发现有价值的新连接时主动交叉引用
- ✅ 尊重已有页面结构，增量编辑而非全量替换
- ✅ 中文写作，术语可保留英文
- ✅ **批判性摄入（Critical Ingest）**：来源页必须区分三层——
  **① 作者主张**（论文怎么说）/ **② 作者承认的局限**（`## 诚实边界`）/
  **③ 摄入者自己的质疑**（`## 批判性评估`）。第三层不可省略。
  重点核查：**是否有同行评审**（预印本须标注）、**是否有人类基线**（缺基线则
  "模型表现差"没有分母）、**自报数字是否自洽**（占比/总数/提速比要能相互印证）、
  **"多次独立复现"是否真的独立**（同一课题组不算独立）。
  发现可疑数字（如显著劣于随机）时**保留原值但标出疑点**，不要替作者圆场，
  也不要把单篇论文的主张写成整个库的"常识"。frontmatter 可加 `source_reliability` 字段。

#### 批判性标记（Callout 约定）

在正文中用以下标记**就地标出**可疑论断，与既有 `> ⚠️ 矛盾：...` 并列。
标记只加在**具体句子/数字**旁，不要在文末堆成清单；每条须写明**为什么可疑**。

| 标记 | 触发条件 | 写法示例 |
|------|----------|----------|
| `> ⚠️ 矛盾：` | 两处内容对同一事实说法不一（跨页或页内） | `> ⚠️ 矛盾：frontmatter 标 Sci. Adv. 2021，正文却是 Nat. Energy 2020` |
| `> ⚠️ 单源论断：` | 结论只有**一篇**论文支撑，未被独立复现 | `> ⚠️ 单源论断：该机制目前仅本课题组报道，尚无第二家独立验证` |
| `> ⚠️ 自报数字：` | 作者自报的性能/占比/提速比，无第三方核验或方差 | `> ⚠️ 自报数字：">10000 种稳定材料"为累计口径，非实测产出` |
| `> ⚠️ 预印本：` | arXiv/bioRxiv 等**未经同行评审** | `> ⚠️ 预印本：本文为 arXiv 预印本，引用时须留意尚未同行评审` |
| `> ⚠️ 无实验验证：` | 纯计算/DFT 结论，无合成或表征佐证 | `> ⚠️ 无实验验证：稳定性均由 PBE 泛函判定，未做合成` |
| `> ⚠️ 二次引用失真：` | 页面/公众号/解读的转述比原文**更强**或数字无出处 | `> ⚠️ 二次引用失真："90%"系解读虚构对话中的数字，原文无此表述` |
| `> ⚠️ 立场相关：` | 作者主张与其自身平台/路线/商业利益相关（**描述，非指控**） | `> ⚠️ 立场相关：作者参与 nCAC 平台，其主张以该平台取代现行评估体系` |
| `> ⚠️ 体裁提示：` | 综述/评述/公众号文，证据强度天然低于研究论文 | `> ⚠️ 体裁提示：本文为评述（Comment），属观点文体，非研究数据` |
| `> ⚠️ 范围漂移：` | 综述用相邻领域的成果为本文领域背书，或取样偏离领域分布 | `> ⚠️ 范围漂移：所列"材料 agent"进展实为通用 deep-research 基准` |
| `> ⚠️ 信息缺口：` | 关键前提在可见材料中**无从判定**（非作者回避，而是资料不足） | `> ⚠️ 信息缺口：分母是否含封装，可见正文无法判定` |

> 原则：**保留原值，标出疑点**（不删改作者数字），也**不替作者圆场**（不写"虽然…但很可能成立"）。
> 标记应就地贴在**具体句子/数字**旁；允许两种写法——块引用 `> ⚠️ 类型：...`，
> 或列表项内行内 `**⚠️ 类型：** ...`（适合逐条编号的批判性评估节）。同一页内保持一致。
> 拿不准就不加：**宁可少标，不可把作者的正常局限写成"可疑"**。

#### 返工存量页（回溯批判）

对**早于本规则确立**（2026-09-14 前）的存量来源页，回溯补写时：
- 正文结构不重写，**只在文末追加** `## 诚实边界（回溯补录）` 与 `## 批判性评估（回溯补录）`；
- 两节各写 3-6 条，必须**基于实际读取 raw 原文**，不得凭页面现有摘要臆测；
- `updated` 与 frontmatter `source_reliability` 同步补写。

### 不要做
- ❌ 不要修改 `raw/` 中的任何文件
- ❌ 不要删除已有页面（除非用户明确要求）
- ❌ 不要猜测来源内容——必须实际读取
- ❌ 不要在未读取来源的情况下创建来源摘要
- ❌ 不要破坏 Dataview 兼容的 YAML 格式

---

## 配置参考

> 📖 **`.obsidian/` 各键值、依赖清单、双运行时技能根（维护向）见
> 改动配置/结构、排查 Obsidian 行为时读。**本文件不再展开。**
>
> ⚠️ 两条**改结构时才需要**的硬约束先记住：`app.json` 归 Obsidian 所有（退出即重写），
> 改它**必须在 Obsidian 关闭时**做；`userIgnoreFilters` 是**排除的唯一来源**
> （旧版在两处硬编码目录名，目录一改即静默失效）。

---

## 已知陷阱

> 📖 **完整事故史（八起校验器事故、六类坏链接、写盘「一次写坏 124 页」事件、跨类方法论）

- 🔴 **「元数据静默丢失」是本工具链头号失效**——页面能正常打开、正文可读，**人工浏览完全看不出**，
  但元数据在索引层整个消失。三条纪律（**读、写两侧都适用**）：
  1. **frontmatter 一律走 `kb_lib`**：读用 `read_text`（二进制解码 + 换行归一），
     拆/合只用 `split_frontmatter` / `join_frontmatter`（**唯一出口**）。
     **不要另写「差不多」的正则**——宽松的校验器 = 没有校验器（曾一次写坏 **124 页**）。
  2. **长字段含冒号必须整体加双引号**：`summary` / `source_reliability` / `authors` /
     `corresponding_author` / `institution` / `published`；否则 YAML 把冒号后当新键 ⇒
     **整页元数据丢失**（曾 **49 页**）。写完跑 `yaml.safe_load` 或 `kb_lint.py --quick`。
  3. **闭合 `---` 后必须有换行**；**写盘后复算**：写 N 页要能读出 N 页。
- **换行符 CRLF/LF 混合**（非统一，且比例随批次变化——**不要引用固定计数**）⇒ **不要对换行做假设**，
  读文件务必二进制读取后显式 `decode("utf-8")` 并归一化。
- **链接一律带 `[[ ]]`；`sources:` 的 raw 回链要写完整相对路径**
  （`"[[raw/<子目录>/file.md]]"`，**不能只写文件名**——raw 分布在多子目录）。
- **wikilink 两类目标、两种解析器**：页面链接（`[[concepts/X]]`）查**页面名集合**；
  资源链接（`[[raw/...]]`）查**文件系统**。混用曾致 **429 条**真实回链被误报为 broken。
  同理，**代码块内的 `[[...]]` 是示例文本，须剔除**。
- **`sources:` 的 raw 回链是摄入统计的唯一依据**：漏写 → 该资料被误判为「未摄入」。

### 校验器自检纪律

> **凡是"用正则/字符串计数做判定"的校验器，必须能对已知答案的样本反算一次。**

本工具链已有 **八次**同类事故——**计数器本身出错，却被读成内容质量问题**。
八个案例的完整症状/根因（含 2026-10-23 新登记的第 8 条：路径里的成对括号被 `[^)]+` 截断，
断图链 104→89）、以及四条可迁移方法论（「已声明≠已生效」「规范写的是 sample 不是 census」
「有字符串≠功能正常」「写出了缺省值也要验证它在起作用」）见

**改动任何 lint/校验脚本后**：

1. 跑 `python tools/kb_lint.py --selftest`（**每个** `qc_*` 的 `--selftest` 也须跑）
2. **新增/改动任何工具后，还须跑** `python tools/kb_toolcheck.py`
   —— **实跑**全部工具，报「编译 / 自检 / `--help` / 意外写盘」四类问题。
   （`--selftest` 存在 ≠ 通过 ≠ 可用：`kb_semantic_search` 曾因嵌入索引陈旧实跑 FAIL，
   而静态检查看不见——见事故 #7。）
3. **夹具必须同时含正例与反例**——只测「该过的过了」会漏掉「该报的没报」。

> 🔴 **写盘脚本额外铁律**：① 必须有 `--apply`、默认干跑；② **写前用与校验系统**同一个**
> 解析器复核**（`kb_lib.split_frontmatter`），不另写宽松正则；③ 写前备份（`.qc_backup_YYYYMMDD/`）、
> **写后复算**（写 N 页要能读出 N 页）；④ 会写盘的修复脚本，运行前与**独立实现**对总数，
>
> **判据**：修复前先记一个**基线数字**（如 broken = 403），修复后对照；
> 数字下降必须能逐类解释，否则可能是把真问题一起放过了。

---

## Agentic RAG 检索协议

> 2026-10-24 起，复杂问题首选 `python tools/kb.py ask "<问题>" --strategy agentic --json`：
> 有界规划、分层检索、图扩展、证据去重与 gaps 均由工具执行；最终综合由调用方模型完成。
> 简单事实用 `--strategy simple`，走 BM25/向量/RRF/本地精排/Top-K。

### 🔴 第一原则：先分层，再排序

`kb_agentic.py` / `kb_route.py` 把证据**分三层返回**（**不混排**）：**L1** concept/entity/topic（本工具链的**当前综合**，
二手概括）｜ **L2** source（**单篇论文的主张** + `source_reliability`）｜ **L3** raw 全文块
（**原文字面表述**，可回指 `文件:行号`）。

⚠️ **L1 与 L3 的可信度不是一回事**——混排会让 Agent 把「本工具链二手综合」当成「一手证据」引用。
**引用 L1 时必须意识到它需要 L2/L3 支撑。**
另注 `signal.top_score` / `low_confidence`：**BM25 无分数下限，任何查询都会凑满 k 条**——
普遍低分应视为**知识空白，而非硬答**。

> 📖 **查询分解 / 多跳 / 自适应深度 / 上下文预算的完整协议见技能 `kb-query`**（此处不重复）。

---

## Ingest 工作流增强

> 📖 **SI 缺失标记协议、批量预分类、外部文献接入、Entity 页最低内容标准
> 与 §操作流程 的 Ingest 8 步配合使用。

---

## 知识综合与 Topic 页指引

> 📖 **Topic 页创建触发条件（簇口径 + 独立知识模块双闸门）、页模板、知识图谱健康检查
>
> ⚠️ **`check_topic_coverage` 的告警是提示而非缺陷**（本工具链常驻 40+ 条），
> 只在 concept **同时满足「≥20 source」与「独立知识模块」**时才考虑建页。

---

## 🔎 已知边界台账（建议你自己维护一份）

源库在每轮诊断后都会留下这样一节，**只登记「核验后仍然存在、且本轮不打算处理」的边界**，
免得下一轮把它们当新发现重查一遍。随包发布的这一份已把源库的私有状态摘掉，
只留下方法——请在你自己的库里建一份同结构的：

- **每条边界写清「为什么不处理」**：收益低于误伤风险、受某条纪律约束、需专门一轮……
  没有理由的边界等于没登记，下一轮照样会被翻出来重查。
- **数字一律现场重算，不抄旧结论**：台账里的计数会随每日 ingest 失效。
  写「以命令输出为准，勿引用旧数」，比写一个必然过期的数字诚实。
- **不要把状态字段改好看**：例如 `si_status` 从 `missing` 改成 `present` 充数——
  `present` 的含义是「库内确有该实体文件」，改字段不改事实只是把欠账藏起来。
- **典型条目类型**：重复卡未归档（受「不删除已有页面」纪律约束）、tag 变体并存
  （合并须同步改 `.base` 过滤与检索别名）、`sources:` 语义漂移（逐条改会牵动论证链）、
  统计口径分裂（`kb_stats` 含项目卡而 `kb_lint` 只扫 wiki 页——两个数字都对，问题不同）。

---
## 日志与更新协议

> 📖 **日志分离表、索引重建强制规则、版本快照流程见
> 现行两条硬约束：**每次 `batch_close` 后必跑 `kb.py index build`**，并按影响面刷新 embed/corpus；
> 每次操作后**追加 `log_ops.md`**（格式 `## [日期] <操作> | <描述>`）。

---

## 委托纪律

> ⚠️ **委托前确认运行时真会加载那个文件**——曾把关键流程委托给运行时根本不读的
> `.claude/skills/…`，长期静默失效。**「已声明」≠「已生效」。**

---

_本工具链基于 [karpathy/llm-wiki](https://github.com/karpathy/llm-wiki) 的构想，由用户和 Agent 共同演化。_