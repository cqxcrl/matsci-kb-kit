# Sci-Assistant 决策层

> 13 个 `sci_*` 工具 ｜ 3 大核心能力（C1 切入点 / C2 方案 / C3 统筹）+ 1 条贯穿三层的链路溯源

Sci-Assistant 是基于知识库的**科研课题辅助系统**——从切入点发现、实验方案设计到进展追踪，形成"知识→决策→行动→反馈"的闭环。

它不生产知识，只**把知识层已有的证据组织成决策**：任何推荐、参数、判断都必须能回指一张 source 卡或原文段落，否则标"库内无证据"。

---

## 三大核心能力

| # | 能力 | 场景 | 工具 |
|---|---|---|---|
| **C1** | **切入点发现** | 已有大方向，找未被充分探索的细分点 | `sci_landscape.py` `sci_gap_scan.py` `sci_topic_rec.py` |
| **C2** | **实验方案推荐** | 确定切入点后，设计实验路线 | `sci_method_extract.py` `sci_protocol_gen.py` `sci_lab_match.py` `sci_method_chain.py` |
| **C3** | **课题进展统筹** | 实验推进中，记录、分析、调整 | `sci_progress.py` `sci_data_analysis.py` `sci_ecsa_qc.py` `sci_review.py` |
| **贯穿** | **链路溯源** | C1→C2→C3 三层产物之间的主键一致性与沿革 | `sci_links.py` |

辅助：`sci_reagent_import.py`（试剂入库，服务 C2 的实验室匹配）。

---

## 工具速查

### C1 切入点发现

| 工具 | 功能 |
|---|---|
| `sci_landscape.py` | 方向景观分析：分面聚合（year/journal/institution）、子方向聚类（concept 出链分组） |
| `sci_gap_scan.py` | 科学内容空白扫描：6 个信号（comp-no-expt / synth-no-char / single-lab-claim / temporal-gap / method-orphan / cross-domain-gap） |
| `sci_topic_rec.py` | 切入点推荐：可行性 = 0.45×空白 + 0.35×文献充分度 + 0.20×方向相关度 |

```bash
python tools/sci_landscape.py  --direction "<你的方向>"            # 景观：分面 + 子方向
python tools/sci_gap_scan.py   --topic "<你的方向>"                # 空白信号
python tools/sci_topic_rec.py  --topic "<你的方向>" --top 3        # 切入点排名
python tools/sci_topic_rec.py  --refine "<你的方向>" --interested 1,3 --apply
```

### C2 实验方案

| 工具 | 功能 |
|---|---|
| `sci_method_extract.py` | 方法提取：L1 概念页逐字提取 + L2 Source 卡分批提取（quote 机械校验） |
| `sci_protocol_gen.py` | 方案生成：策略层（方法对比）→ 操作层（参数/步骤/设备，逐条带 quote）→ 判断层（优势/条件/局限） |
| `sci_lab_match.py` | 实验室匹配：设备/表征/计算/试剂四类需求 vs 实验室档案（available/partial/missing/unregistered/purchased） |
| `sci_method_chain.py` | 方法链：构建方法间依赖关系（术语共享边 + 类别级弱边） |
| `sci_reagent_import.py` | 试剂入库：从 Excel 提取试剂清单（隐私保护：不导出价格/客户/照片） |

```bash
python tools/sci_method_extract.py --from sources --auto --topic "<你的方向>" --out-dir _scratch/l2
python tools/sci_protocol_gen.py   --topic "<你的方向>"          # 策略层 → 操作层 → 判断层
python tools/sci_lab_match.py      --protocol <protocols/你的方案>
python tools/sci_method_chain.py   --report <protocols/你的方案>
```

### C3 进展统筹

| 工具 | 功能 |
|---|---|
| `sci_progress.py` | 课题管理：课题/日志/里程碑/摘要（yaml 写后复算） |
| `sci_data_analysis.py` | 数据分析：CHI/DIGISIM/CSV 解析 + 统计/导出 + 出图（matplotlib/Origin 双后端） |
| `sci_ecsa_qc.py` | ECSA 五道门：G1–G5 门禁（扫速≥3 / 统一 e0 / Cs 元数据 / R² 分级 / 回原始 CV 对账） |
| `sci_review.py` | 复盘建议：失败日志 → KB 证据 → 建议（逐条 quote 校验） |

```bash
python tools/sci_progress.py new "<课题名>" --direction "<你的方向>" --entry "<子方向>"
python tools/sci_progress.py log <slug> --text "…"
python tools/sci_data_analysis.py --input <数据文件> --plot
python tools/sci_ecsa_qc.py --result <ecsa_result.json>          # G1–G5 硬门
python tools/sci_review.py --project "<课题名>" --data <ecsa_result.json> --build
```

### 链路溯源（`sci_links.py`）

C1/C2/C3 三层各自落盘，久了会**各说各话**：切入点被改名、方案换了主键、课题还指着旧快照。
`sci_links.py` 是只读的对账器——统一主键口径 `<topics 目录名>#<sub_direction>`，并给出三层快照。

```bash
python tools/sci_links.py --status                       # 三层主键一致性总览
python tools/sci_links.py --adopt "<方向>"                # 某切入点被哪些方案/课题采纳
python tools/sci_links.py --trace "<课题 slug>"           # 课题沿革 C1→C2→C3
python tools/sci_links.py --snapshot "<方向>#<子方向>"     # 打印该切入点的快照 JSON
```

---

## 落盘约定

所有 `sci_*` 的读写落点都由一份配置给出，工具内只留兜底默认值：

```
projects/sci-assistant/
├── config/sci_assistant_config.yaml   # 唯一配置源（目录、阈值、期刊别名）
├── config/journal_aliases.yaml        # 期刊名归一白名单
├── topics/<方向>/landscape.json       # C1 产物
├── topics/<方向>/entry_points.json    # C1 产物（切入点主键）
├── protocols/<方案>/…                 # C2 产物
└── progress/<课题 slug>/project.yaml  # C3 产物
```

改目录只需改配置；工具用 `__file__` 派生库根，不写绝对路径。

---

## 设计原则

1. **证据链不可断**：任何推荐/参数必须能回指 source 卡或原文；无出处的结论标"库内无证据"
2. **事实型输出**：不生成"优势/适用条件"等判断（方法库无此字段），判断层单独走 LLM + quote 校验
3. **写前备份**：覆盖固定落点文件前自动备份到 `_scratch/backup/`
4. **数字不写死**：阈值、路径从配置文件读
5. **自检纪律**：所有工具带 `--selftest`（含正例与反例夹具）；`kb_toolcheck.py` 会实跑它们

---

## 与知识库的关系

```
┌─────────────────────────────────┐
│      Sci-Assistant (决策层)      │
│ C1 切入点 │ C2 方案 │ C3 统筹   │
└──────┬──────┬──────┬────────────┘
       │      │      │
       └──────┼──────┘
              ▼
    ┌──────────────────┐
    │  知识库工具层     │
    │  kb_* / lit_*    │
    └────────┬─────────┘
             ▼
    ┌──────────────────┐
    │  wiki/ + raw/    │
    │  知识层 + 资料层  │
    └──────────────────┘
```

Sci-Assistant **复用**知识库的检索层（`kb_search` / `kb_route` / `kb_graph`）与文献流水线（`lit_*`），**不修改**既有 wiki 页面（除经审核新增 `wiki/experiments/`）。

---

## 已知边界

1. **C1 候选集非全库普查**：默认取 BM25 前 N 张 source 卡（N 由配置给出），不是全库普查；
   库越大越要留意召回截断
2. **C2 方法库无"优势/局限"字段**：策略层只做事实排列，判断层单独走 LLM + quote 校验
3. **C2 试剂库存需用户补**：`lab_profile.yaml` 的 reagents 可从入库表提取，但当前余量仍需人工补充
4. **C3 归因是"可能原因"**：复盘建议不是因果，证据不足即丢弃
5. **方法链依赖是推断**：不是作者明示的依赖关系，跨论文链需人工适配
6. **`sci_ecsa_qc.py` 是电化学专用**：G1–G5 门禁针对 ECSA/CV 计算；其它体系请用
   `sci_data_analysis.py` 的通用统计通道

---

## 自检

```bash
python tools/kb_toolcheck.py          # 实跑全部工具的 --selftest / --help + 写盘防呆
python tools/sci_links.py --selftest  # 单个工具
```
