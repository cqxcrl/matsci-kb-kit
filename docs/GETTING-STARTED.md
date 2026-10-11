# 快速上手

## 0. 前置

- Python ≥ 3.10（推荐 3.11+）
- Obsidian（用于看图；工具本身不依赖 Obsidian 运行时）
- Git（可选，但强烈建议；库的文本部分适合版本化）

## 1. 安装依赖

```bash
pip install -r requirements.txt            # 核心：pyyaml jieba numpy PyMuPDF
pip install -r requirements-optional.txt   # 可选：语义检索 + 剪贴板
```

## 2. 初始化一个库

```bash
python scripts/kb_init.py --target /path/to/my-vault
```

它做这些事（**幂等**，已存在文件默认不覆盖；要覆盖加 `--force`）：

1. 建 `wiki/` `raw/` `projects/` 等目录（含 `.gitkeep`）
2. 放五个根元文件：`index.md` `tags.md` `log_ops.md` `log_insights.md`
3. 放 5 个 `.base` 视图（Obsidian Bases）
4. 放 `.obsidian/`（app.json / core-plugins.json）与 `.gitignore`
5. 放 `tools/`（工具链）、`CLAUDE.md`（方法论）、`.dsh/skills/`（技能）
6. 由模板写 `tools/lit_config.yaml`
7. **跑一次索引构建**（空库也产出合法空索引）

## 3. 用 Obsidian 打开

打开 `/path/to/my-vault`。你会看到 5 个 Bases 视图（此时为空）与 `index.md`。

## 4. 自检

```bash
python /path/to/my-vault/tools/kb.py --doctor     # 环境与索引
python /path/to/my-vault/tools/kb_toolcheck.py    # 实跑全部工具
```

## 5. 配研究方向（可选，用文献流水线时做）

空库的 `tools/lit_config.yaml` 只有占位示例。用 **`kb-onboard` 技能**访谈一次，即可配好
方向与期刊白名单：

> 用 kb-onboard 帮我配置研究方向

它会分批问你的专业/方向/关键词/偏好期刊，生成 `profile.md`，并把 `lit_config.yaml` 的
`automation.directions` 与 `journals` 填好。之后：

```bash
python tools/lit_doctor.py                                     # 体检
python tools/lit_discover.py "你的方向" "近一周" --limit 20     # 第一轮检索
python tools/lit_report.py --from-sources --days 7             # 出归纳报告
```

## 6. 开始灌内容

三条路，任选：

- **手动**：把笔记写进 `wiki/`，把资料放 `raw/`，然后跑
  ```bash
  python tools/kb_build_index.py            # 刷新索引
  ```
- **文献流水线**：先在 `tools/lit_config.yaml` 填 `journals`（你的学科期刊白名单）、
  `dedup_sources`（本机已有文献目录）、`automation.directions`（发现方向），然后
  ```bash
  python tools/lit_doctor.py                # 体检
  python tools/lit_discover.py "你的方向" "近一周" --limit 20
  ```
  完整链路见技能 `.dsh/skills/lit-watch/SKILL.md`。
- **让 AI 读 `CLAUDE.md` 后按 ingest 流程帮你消化**。

## 7. 日常

```bash
python tools/kb_route.py "某个问题" --json   # 分层检索（首选入口）
python tools/kb_search.py "关键词" -k 10     # BM25/语义/混合
python tools/kb_lint.py --quick              # 最近 ingest 的质量检查
python tools/kb_lint.py --deep               # 全库检查（--fix 可修）
```

把 `kb_route` 的返回交给 AI，它会拿到「L1 综合 / L2 文献卡 / L3 原文」三层带引用的证据。

## 常见问题

- **`--doctor` 报「嵌入索引不存在」**：正常。语义检索是可选增强，需要
  `pip install sentence-transformers` 后 `python tools/kb_semantic_search.py --build`。
- **搜索返回 0 命中但库里有页面**：忘了重建索引 → `python tools/kb_build_index.py`。
- **改了页面看不到变化**：索引是派生的，改完要重建（增量秒级）。
