# Sci-Assistant 决策层

> **v0 全量完成 2026-10-21** ｜ 12 个工具 ｜ 3 大核心能力（C1 切入点 / C2 方案 / C3 统筹）

Sci-Assistant 是基于知识库的**科研课题辅助系统**——从切入点发现、实验方案设计到进展追踪，形成"知识→决策→行动→反馈"的闭环。

---

## 三大核心能力

| # | 能力 | 场景 | 工具 |
|---|---|---|---|
| **C1** | **切入点发现** | 已有大方向（如"电解液设计"），找未被充分探索的细分点 | `sci_landscape.py` `sci_gap_scan.py` `sci_topic_rec.py` |
| **C2** | **实验方案推荐** | 确定切入点后，设计实验路线 | `sci_method_extract.py` `sci_protocol_gen.py` `sci_lab_match.py` `sci_method_chain.py` |
| **C3** | **课题进展统筹** | 实验推进中，记录、分析、调整 | `sci_progress.py` `sci_data_analysis.py` `sci_ecsa_qc.py` `sci_review.py` |

---

## 工具速查

### C1 切入点发现

| 工具 | 功能 |
|---|---|
| `sci_landscape.py` | 方向景观分析：分面聚合（year/journal/institution）、子方向聚类（concept 出链分组） |
| `sci_gap_scan.py` | 科学内容空白扫描：6 个信号（comp-no-expt / synth-no-char / single-lab-claim / temporal-gap / method-orphan / cross-domain-gap） |
| `sci_topic_rec.py` | 切入点推荐：可行性 = 0.45×空白 + 0.35×文献充分度 + 0.20×方向相关度 |

### C2 实验方案

| 工具 | 功能 |
|---|---|
| `sci_method_extract.py` | 方法提取：L1 概念页逐字提取 + L2 Source 卡分批提取（quote 机械校验） |
| `sci_protocol_gen.py` | 方案生成：策略层（方法对比）→ 操作层（参数/步骤/设备，逐条带 quote）→ 判断层（优势/条件/局限） |
| `sci_lab_match.py` | 实验室匹配：设备/表征/计算/试剂四类需求 vs 实验室档案（available/partial/missing/unregistered/purchased） |
| `sci_method_chain.py` | 方法链：构建方法间依赖关系（术语共享边 + 类别级弱边） |

### C3 进展统筹

| 工具 | 功能 |
|---|---|
| `sci_progress.py` | 课题管理：课题/日志/里程碑/摘要（yaml 写后复算） |
| `sci_data_analysis.py` | 数据分析：CHI/DIGISIM/CSV 解析 + 统计/导出 + 出图（matplotlib/Origin 双后端） |
| `sci_ecsa_qc.py` | ECSA 五道门：G1–G5 门禁（扫速≥3 / 统一 e0 / Cs 元数据 / R² 分级 / 回原始 CV 对账） |
| `sci_review.py` | 复盘建议：失败日志 → KB 证据 → 建议（逐条 quote 校验） |
| `sci_reagent_import.py` | 试剂入库：从 Excel 提取试剂清单（隐私保护：不导出价格/客户/照片） |

---

## 设计原则

1. **证据链不可断**：任何推荐/参数必须能回指 source 卡或原文；无出处的结论标"库内无证据"
2. **事实型输出**：不生成"优势/适用条件"等判断（方法库无此字段），判断层单独走 LLM + quote 校验
3. **写前备份**：覆盖固定落点文件前自动备份到 `_scratch/backup/`
4. **数字不写死**：阈值、路径从配置文件读
5. **自检纪律**：所有工具带 `--selftest`（含正例与反例夹具）

---

## 实测案例

### 电解液设计方向（C1）

- **候选集**：BM25 前 200 张 source 卡
- **子方向**：10 个（SEI 界面 44 / 锂金属 33 / AI 电解质 33 / 锌负极 33 …）
- **空白信号**：9 个（comp 2 / single 3 / cross 3 / orphan 1）
- **切入点**：5 个（2 high：AI 电解质设计 0.552 / 机器学习势函数 0.519）

### 锌电解液方案（C2）

- **3 个候选**：AHTech 高通量平台（测试，引文 44 条）/ MLMD 壳外共溶剂筛选（计算，31）/ MACE 单齿乙酸电解液（合成，27）
- **参数/材料用量**：逐条带 quote，0 无引文
- **判断层**：32 条判断，quote 校验 32/32
- **方法链**：5 条（MLMD→LFP/LMFP、MLMD→HBN …）

### ECSA 重算与复盘（C3）

- **失效案例**：原 CSV R²=1.1e-16、ECSA=3.2e-15 cm²（机器零）
- **重算**：用原始 5/7/10 mV/s 重算，Cdl 3.05–5.87 mF cm⁻²、ECSA 50.9–97.9 cm²
- **复盘**：5 条建议、6 条证据、0 条校验失败

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

## 工具健康

`kb_toolcheck.py` 实跑：**78 工具全部 PASS**（kb_* 19 + lit_* 14 + qc_* 3 + sci_* 12 + journals.yaml 1）。

所有 12 个 `sci_*.py` 工具自检通过，总计 **178 项 selftest**（landscape 25 + gap_scan 23 + topic_rec 13 + method_extract 27 + protocol_gen 16 + lab_match 16 + progress 13 + data_analysis 25 + ecsa_qc 7 + review 7 + method_chain 9 + reagent_import 16）。

---

## 已知边界

1. **C1 候选集非全库普查**：BM25 前 200 张卡，不是全库 665 张 source
2. **C2 方法库无"优势/局限"字段**：策略层只做事实排列，判断层单独走 LLM
3. **C2 试剂库存需用户补**：`lab_profile.yaml` 的 reagents 从入库表提取 84 条，但当前余量仍需口述补充
4. **C3 归因是"可能原因"**：复盘建议不是因果，证据不足即丢弃
5. **方法链依赖是推断**：不是作者明示的依赖关系，跨论文链需人工适配

---

## 参考文献

- 工作计划：`projects/sci-assistant/docs/工作计划.md`（v0.17，727 行）
- 开工指导书：`projects/sci-assistant/docs/开工指导书.md`（v0.15）
- 诊断意见：`projects/sci-assistant/docs/Sci-Assistant 诊断意见1.md`
