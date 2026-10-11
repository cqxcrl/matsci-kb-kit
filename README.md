# matsci-kb-kit

> 一套给 **Obsidian 知识库**用的**工具箱 + 方法论**：一个空库跑一条命令就能起库，
> 之后用检索层（BM25/语义/分层取证）、文献流水线（发现→下载→提取→建卡）、
> 健康检查（lint/QC）把它养成「第二大脑」。附一个 **MCP server**，让你的 AI 客户端直接调用这些工具。

**它不是**一份现成的内容库——它**不含任何文献或笔记**，只给你**结构、工具与纪律**，
内容由你自己灌。

---

## 它给你什么

| 层 | 内容 |
|---|---|
| 结构 | `wiki/{concepts,entities,sources,topics,outputs}` + `raw/` + 5 个 Obsidian Bases 视图 |
| 工具 | 30+ 个 `kb_*.py` / `lit_*.py`（检索、索引、lint、文献流水线），全部 `--selftest` |
| 纪律 | `CLAUDE.md`：页面 schema、`evidence_base`、批判性标记、元数据静默丢失防线、L1/L2/L3 分层检索 |
| 客户端 | `mcp/server.py`：把 19 个工具暴露给任何支持 MCP 的 AI 客户端 |
| 技能 | `.dsh/skills/`：lit-watch / lit-pipeline / kb-query / kb-lint 四个流程技能 |

## 快速开始

```bash
# 1. 依赖
pip install -r requirements.txt
# （可选）语义检索 + MCP：
pip install -r requirements-optional.txt && pip install -r mcp/requirements.txt

# 2. 在一个空目录初始化你的库
python scripts/kb_init.py --target /path/to/my-vault

# 3. 用 Obsidian 打开 /path/to/my-vault，然后自检
python /path/to/my-vault/tools/kb.py --doctor
```

初始化会把工具、方法论、`.base` 视图、配置模板、五个根元文件写进你的库，
并**跑一次索引构建**（空库也会产出一个合法的空索引——见下「设计要点」）。

## 挂到 AI 客户端（MCP）

```bash
python mcp/server.py --vault /path/to/my-vault              # stdio server（只读工具）
python mcp/server.py --vault /path/to/my-vault --allow-write # 额外允许写工具
```

在客户端的 MCP 配置里把它作为 stdio server 注册即可。详见 [`docs/MCP.md`](docs/MCP.md)。

## 目录

```
build/       生成器（本 kit 由它从源库生成——改真源后重跑）
tools/       生成：kb_*/lit_* 工具链（勿手改）
skills/      生成：流程技能
scaffold/    逐字拷进你库的模板（目录、元文件、.base、配置、.obsidian）
scripts/     kb_init.py（初始化）、verify_kit.py（自检/CI）
mcp/         MCP server
docs/        GETTING-STARTED / ARCHITECTURE / METHODOLOGY / TOOLS / MCP
CLAUDE.md    生成：方法论载体（放进你的库，AI 按它工作）
kit.yaml     生成溯源（源 commit、工具清单、逐文件 sha256）
```

## 设计要点（为什么这么做）

- **库根靠 `__file__` 派生**：所有工具不写死库路径，所以整个目录可随意改名/迁移。
- **空库也必须能启动**：`kb_build_index.py` 在 0 页面时**产出合法的空索引**，
  于是 `kb_search` / `kb_route` 返回「0 命中 + low_confidence」而不是崩溃。
- **索引是派生数据**：`wiki/.index/` 可随时重建，`.gitignore` 已排除。
- **元数据静默丢失是本类库的头号失效**：frontmatter 一律走 `kb_lib` 的解析/重组函数，
  长字段含冒号必须加引号——`CLAUDE.md` 有完整纪律。

## 许可

代码 MIT（[`LICENSE`](LICENSE)）；方法论文档建议 CC-BY-4.0（见 [`NOTICE.md`](NOTICE.md)）。
工具链构想源自 [karpathy/llm-wiki](https://github.com/karpathy/llm-wiki)。
