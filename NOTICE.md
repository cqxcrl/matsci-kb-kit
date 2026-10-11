# NOTICE

## 许可

- **代码**（`tools/**`、`mcp/**`、`scripts/**`、`build/**`）：**MIT**，见 [`LICENSE`](LICENSE)。
- **方法论文档**（`CLAUDE.md`、`docs/**`、`skills/**`、`scaffold/**`）：建议采用
  **CC-BY-4.0**（署名即可自由使用/改编）。若你只关心代码，可忽略此项。

## 来源与生成

本仓库的 `tools/`、`skills/`、`CLAUDE.md`、`docs/METHODOLOGY.md`、`docs/TOOLS.md`、`kit.yaml`
是**由一份源知识库经 `build/build_kit.py` 过滤 + 去个人化生成的派生数据**——
即：它们**不是**在此手写维护，改动请改真源后重跑生成器（见 `build/README`）。

手写件仅：`build/**`、`mcp/**`、`scripts/**`、顶层 README/LICENSE/NOTICE/pyproject/requirements、
`docs/GETTING-STARTED.md`、`docs/ARCHITECTURE.md`、`docs/MCP.md`。

## 致谢

工具链的最初构想来自 [karpathy/llm-wiki](https://github.com/karpathy/llm-wiki)。
