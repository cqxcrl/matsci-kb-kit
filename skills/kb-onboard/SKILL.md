---
name: kb-onboard
description: "知识库首跑配置向导：访谈用户的专业/方向/关键词/偏好期刊，落成 profile.md 并据此配好 lit_config.yaml（方向 + 期刊白名单），随后可跑第一轮文献发现。用于新库初始化后'不知道从哪配起'、或想调整研究方向的场景。触发词：初始化知识库、首次配置、配置文献监控、onboarding、我该配什么方向、帮我配好期刊、设置我的研究方向。"
whenToUse: "当用户刚用 kb_init 建好库、想开始用文献流水线却还没配方向与期刊；或想新增/调整研究方向与期刊白名单时使用。"
trigger: /kb-onboard
---

# kb-onboard — 首跑配置向导

把「你是谁、关心什么」变成库的配置：**一次访谈 → 一份 `profile.md` → 配好的 `tools/lit_config.yaml`**。
之后 `lit-watch` / `lit_discover` 就能按你的方向找文献了。

> 设计原则（与本工具链同源）：**不替用户编研究方向**。他说不清就给例子让他选；
> 「我不知道」留白并在正文写「待确认」，比填一个看上去合理的值好。

---

## 什么时候用

- 刚 `kb_init` 建好一个空库，`tools/lit_config.yaml` 里 `automation.directions` 还是占位示例。
- 想新增/调整研究方向（`lit_config.yaml` 的 `directions`）与期刊白名单（`journals`）。

## 怎么做（四轮访谈，每轮 3–5 问，不要一次全抛）

> 一次抛 20 个问题是审问，不是访谈。答完一轮再问下一轮；用户说「先这样」就落盘，
> 没问到的写进 `profile.md` 正文的「待补」。

### 第 1 轮 · 你是谁、关心什么（必问）
1. **专业大类**？（材料 / 化学化工 / 生物医学 / 计算机·AI / 物理 / 机械电气 / 环境地学 / 经济管理 / 其他）
2. **细分方向** 1–3 个，用你自己的话（例："固态电解质的界面失效"）。
3. 最想**第一眼看到**哪类进展？（新方法 / 新体系 / 新表征 / 工程落地 / 综述与观点）

### 第 2 轮 · 关键词（决定检索准不准）
4. 每个方向的**中文关键词** 3–8 个，以及必须**排除**的词。
5. 对应的**英文关键词/标准说法** 3–8 个（OpenAlex 用英文更稳；缩写、旧称都给，例 `solid-state electrolyte`/`SSE`/`LLZO`）。
6. 有没有**必须追踪的课题组/作者**？（可选）

### 第 3 轮 · 期刊与档位（决定范围）
7. 你平时**必看**的 5–10 个刊（说刊名即可，脚本会用 OpenAlex 解析 ISSN）。
8. 明确**不想看**的刊。
9. 选刊路线：① 从内置多学科池挑领域 ② 报刊名逐个加 ③ 联网查该领域 top 刊再确认。
10. 档位（T0 正刊/权威综述 · T1 大子刊 · T2 领域一区 top · T3 普通一区 · T4 二区/扩容）
    决定**检索阈值**与**精读认真度**；默认能否接受？

### 第 4 轮 · 机器与习惯（决定怎么跑）
11. 库的位置（就在当前库，还是别的路径）。
12. 多久看一次、回溯多长窗口？（默认：一周一次 / 近 7 天）
13. 每轮最多入库几篇？（默认 10；顶刊不被截断）
14. 精读档：`enhanced` / `standard` / `light`。
15. 语种：只要英文 / 中英都要？
16. 只收开放获取（OA），还是被墙的也列清单自己去下？
17. 有没有 **Zotero / 其它 PDF 目录**要纳入去重？（给数据目录或绝对路径）
18. 报告格式：md 就够 / 还要 docx / pdf？
19. 要不要**每日自动发现**（OS 计划任务，只发现不下载）？

---

## 落盘：两个文件

### ① `<库根>/profile.md`（访谈产物，供人看与 AI 读）
用本模板（字段见下）。字段含义见「对照表」。

### ② `tools/lit_config.yaml`（**真正生效**的配置）
- `automation.directions`：每个方向写 `{slug, label, limit, query}`；`query` 是空格分隔的
  **英文关键词族**（OR 语义）。
- `journals`：白名单。**期刊名不要凭记忆写 ISSN**——用内置刊物维护脚本解析：
  ```bash
  python tools/lit_journals.py --groups          # 看多学科池有哪些领域组
  python tools/lit_journals.py --add "Nature Energy"   # 按名解析 ISSN 并归档
  python tools/lit_journals.py --list            # 看当前白名单与 tier
  ```
- `dedup_sources` / `zotero.data_dir`：填用户给的目录（没有就留 `kb_raw` 一项或空）。
- `defaults.lookback_days` / `automation.limit`：按第 12/13 问填。

## 字段对照表（访谈 → profile.md）

| 问题 | 字段 |
|---|---|
| 1 | `discipline` |
| 2 | `subfield`、`directions[].name` |
| 4、5、6 | `directions[].keywords_zh` / `keywords_en`（第 6 条写进正文「必须追踪的课题组」） |
| 7、8 | `preferred_journals` / `excluded_journals`（**真正生效的是 lit_config.yaml 的 journals**） |
| 10 | `tier_policy`（只写与默认不同的档） |
| 12 | `lookback_days` |
| 13 | `max_papers` |
| 14 | `ingest_depth` |
| 15 | `languages` |
| 16 | 正文备注「只收 OA」 |
| 17 | `zotero_data_dir`、`dedup_sources` |
| 18 | `report_formats` |

## 访谈纪律

- **不要替用户编研究方向**：他说不清就给例子让他选，别自己填一个看上去合理的。
- **「我不知道」不要变成默认值**：留白写「待确认」，比填错好。
- 期刊名走 `lit_journals.py --add`，**不要凭记忆写 ISSN**。
- **结束前复述一遍**（方向、窗口、白名单刊数、每轮篇数、精读档），用户说「对」再跑第一轮。
- 别往 stderr 打无谓告警：新库「期刊白名单为空」是正常态，配好即可。

## 完成后

```bash
python tools/lit_doctor.py                       # 体检：确认配置可解析、目录齐全
python tools/lit_discover.py "你的方向" "近一周" --limit 20   # 第一轮检索
```

再往下就是 `lit-watch` 技能的全链（下载 → 提取 → 建卡 → 收尾），以及
`lit_report.py` 出归纳报告。
