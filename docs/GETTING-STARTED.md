# 快速上手

## 0. 前置

- Python ≥ 3.10（**3.14 已实测**）
- 核心依赖 4 包：`pyyaml` `jieba` `numpy` `PyMuPDF`（见 §2）
- Git（可选，但强烈建议；库的文本部分适合版本化）
- **不需要 Obsidian**：库本体是纯 Markdown，Obsidian 只是可选渲染层（见 §6）

## 1. 安装插件（双平台）

### Claude Code（安装链路已实测）

```bash
claude plugin marketplace add <本目录>
claude plugin install matsci-knowledge-base@matsci-local
```

- **dist 分发包不含本地 marketplace 件**：`dist/` 分发包（npm 包内容）刻意不含
  `.claude-plugin/marketplace.json`，在 dist 包内照做上面的 `marketplace add <本目录>`
  会失败。Claude Code 安装请指向**仓库根**（含 `.claude-plugin/marketplace.json`）。
- marketplace 名为 `matsci-local`（本地 Folder 源）；安装后 `claude plugin list` 应显示
  `matsci-knowledge-base@matsci-local` enabled，`claude plugin details matsci-knowledge-base`
  列出 9 个技能 + 1 个 MCP 服务。会话内技能带前缀 `matsci-knowledge-base:`。
- **MCP 需一步手动换用变体**：仓库 `.mcp.json` 默认是 Qoder 变体
  （`${QODER_PLUGIN_ROOT}`），Claude Code 不展开该变量。按 docs/MCP.md 的
  「Claude Code 启用 MCP」一节换成 `${CLAUDE_PLUGIN_ROOT}` 即 Connected（已实测，
  含真实工具调用）。技能主路径不受此影响。
- ⚠️ **已知坑：project-config 重复条目**。在插件源目录内运行 claude 时，仓库的
  `.mcp.json` 会被兼作项目配置再加载一次，出现第二个 `matsci-kb` 条目
  （Pending approval / CONNECTION_CLOSED）。那是项目配置条目，**不是插件服务的状态**；
  判断插件 MCP 请认准 `plugin:matsci-knowledge-base:matsci-kb` 这一条。
- 卸载：`claude plugin uninstall matsci-knowledge-base@matsci-local`，
  再 `claude plugin marketplace remove matsci-local`。

### Qoder（安装链路已实测；运行时加载待验收）

设置 → 插件 → 从本地安装，选择本目录（或按白名单打包 zip 后经安装器安装）。
打包 → 安装器 → 启用 → 落盘链路已实测通过，`.mcp.json` 的 `${QODER_PLUGIN_ROOT}`
变体无需改动。**新会话中的技能可见性与 MCP 启动请在验收时确认**——本文不声称
该运行时面已验证。

## 2. 安装 Python 依赖

```bash
pip install -r requirements.txt            # 核心：pyyaml jieba numpy PyMuPDF
pip install -r requirements-optional.txt   # 可选：语义检索/精排、浏览器兜底、出图、剪贴板
```

可选依赖是**分层**的（检索增强 / 浏览器抓取 / CAJ 转换 / 其它），逐项注明
「不装会失去什么」，按需取舍。

> 🔴 **不装可选依赖也能用**，但 `kb.py search` 的默认 `--mode hybrid` 会**退出码 3**
> （它要求嵌入索引 + 本地 Reranker，且刻意不静默降级）。此时请显式用 `--mode bm25`。
> 装了 `sentence-transformers` 后再跑 `python tools/kb.py index embed` 建嵌入索引。

## 3. 建库（kb_init）

```bash
python scripts/kb_init.py --target /path/to/my-vault
```

它做这些事（**幂等**，已存在文件默认不覆盖；要覆盖加 `--force`）：

1. 按 `scaffold/dirs.txt` 建 `wiki/`（含 `experiments/`）、`raw/`、`projects/`、
   `_archive/`、`_scratch/` 等目录（含 `.gitkeep`）
2. 放根元文件：`index.md` `tags.md` `log_ops.md` `log_insights.md`
3. 放 `profile.md`（首跑访谈用的空白档案）、`.gitignore`、`.gitattributes`、
   `_archive/README.md`（归档登记册骨架）
4. 放 `tools/`（工具链）与 `CLAUDE.md`（方法论）
5. 由模板写 `tools/lit_config.yaml`（占位，待 `/kb-onboard` 访谈后填写）
6. **跑一次索引构建**（空库也产出合法空索引；`--no-index` 可跳过）

默认**纯 Markdown**：不铺任何 Obsidian 专属文件；也**不复制 skills 进库**——
技能在插件级注册，由插件运行时提供（避免双份漂移）。

> 目录清单的唯一来源是 `scaffold/dirs.txt`；`kb_init.py` 靠 `__file__` 定位插件，
> 所以库放哪、叫什么名字都不用改配置。
> 只查依赖不建库：`python scripts/kb_init.py --target x --check-deps`。

## 4. 自检

```bash
python /path/to/my-vault/tools/kb.py --doctor     # 环境与索引 → 应 PASS
python /path/to/my-vault/tools/kb_toolcheck.py    # 实跑全部工具
```

## 5. 配研究方向（/kb-onboard）

空库的 `tools/lit_config.yaml` 只有占位示例。在 agent 中跑 **`/kb-onboard`** 技能，
访谈一次即可配好研究方向与期刊白名单：

> /kb-onboard

它会分批问你的专业/方向/关键词/偏好期刊，生成 `profile.md`，并把 `lit_config.yaml` 的
`automation.directions` 与 `journals` 填好。联系邮箱（`datasource.mailto`，进 OpenAlex
礼貌池、更快更少 429）可在访谈中一并给出或事后手工补填。之后：

```bash
python tools/lit_doctor.py                                     # 体检
python tools/lit_discover.py "你的方向" "近一周" --limit 20     # 第一轮检索
python tools/lit_report.py --from-sources --days 7             # 出归纳报告
```

## 6. Obsidian（可选）

想要图形化浏览：建库时加 `--with-obsidian`，额外铺设 `.base` 视图（Obsidian Bases
核心插件，不是 Dataview）与 `.obsidian/` 最小配置，然后用 Obsidian 打开库目录。
改任何 `.base` 后必跑 `python tools/qc_base_check.py`。不装 Obsidian 不影响任何工具。

## 7. 开始灌内容

三条路，任选：

- **手动**：把笔记写进 `wiki/`，把资料放 `raw/`，然后跑
  ```bash
  python tools/kb_build_index.py            # 刷新索引
  ```
- **文献流水线**：先经 `/kb-onboard` 或手工填好 `tools/lit_config.yaml` 的
  `journals`（你的学科期刊白名单）、`dedup_sources`（本机已有文献目录）、
  `automation.directions`（发现方向），然后
  ```bash
  python tools/lit_doctor.py                # 体检
  python tools/lit_discover.py "你的方向" "近一周" --limit 20
  ```
  完整链路见插件技能 `skills/lit-watch/SKILL.md`（会话内即 `/lit-watch`）。
- **让 AI 读 `CLAUDE.md` 后按 ingest 流程帮你消化**（会话内即 `/kb-ingest-batch`）。

## 8. 日常

```bash
python tools/kb.py route "某个问题" --json       # 分层检索（取证首选入口）
python tools/kb.py search "关键词" --mode bm25    # 零额外依赖
python tools/kb.py ask "这个方向的证据充分吗"      # 自动选传统 / Agentic RAG
python tools/kb_lint.py --quick                  # 最近 ingest 的质量检查
python tools/kb_lint.py --deep                   # 全库检查（--fix 可修）
python tools/kb_toolcheck.py                     # 工具"能不能用"的唯一判据
```

把 `kb.py route` 的返回交给 AI，它会拿到「L1 综合 / L2 文献卡 / L3 原文」三层带引用的证据。
会话内对应技能：`/kb-query` 检索、`/kb-lint` 体检、`/lit-watch` 文献监测。

## 9. 升级工具

插件更新后，对已有库重新物化工具（知识数据不动，`lit_config.yaml` 保留，
旧工具整体备份到 `_archive/tools-backup-<时间戳>/`）：

```bash
python scripts/kb_init.py --target <vault> --update-tools
```

## 常见问题

- **`--doctor` 报「嵌入索引不存在」**：正常。语义检索是可选增强，需要
  `pip install sentence-transformers` 后 `python tools/kb.py index embed`。
- **`kb.py search` 报 `RetrievalUnavailable`、退出码 3**：默认 `--mode hybrid` 缺嵌入索引
  或本地 Reranker。它**不会**静默降级成 BM25——请加 `--mode bm25`，或装齐可选依赖后建嵌入索引。
- **搜索返回 0 命中但库里有页面**：忘了重建索引 → `python tools/kb_build_index.py`。
- **改了页面看不到变化**：索引是派生的，改完要重建（增量秒级）。
- **`lit_discover` 每个方向都只回同样多条**：多半是缺 OpenAlex API key（cursor 翻页从第 2 页起 401）。
  设环境变量 `OPENALEX_API_KEY`，**不要**把 key 明文写进 `lit_config.yaml`（那文件被 git 跟踪）。
- **`lit_ingest --apply` 退出码 2**：不是写坏，是**补链没做完**。去补链后重跑。
- **Claude Code 下插件 MCP 显示 CONNECTION_CLOSED**：多半是 `.mcp.json` 仍为 Qoder 变体
  （`QODER_PLUGIN_ROOT` 不展开）。按 docs/MCP.md 换用 `${CLAUDE_PLUGIN_ROOT}` 并重启会话。
  若看到的是不带 `plugin:` 前缀的第二个 `matsci-kb` 条目，那是 project-config 重复加载（见 §1）。
