# MCP server

`mcp/server.py` 把库的工具链暴露为 **MCP 工具**，任何支持 MCP 的 AI 客户端
（Claude Desktop / Claude Code / 其他）都能直接调用。

## 运行

```bash
pip install -r mcp/requirements.txt          # 官方 mcp SDK
python mcp/server.py --vault /path/to/vault               # stdio（只读工具）
python mcp/server.py --vault /path/to/vault --allow-write # 额外允许写工具
```

库根解析顺序：`--vault` 参数 > `MATSCI_KB_VAULT` 环境变量 > 当前目录。
若目标不是知识库（缺 `tools/kb_lib.py`）会**拒绝启动**。

不带 SDK 也能用 `--list-tools` / `--selftest`（CI 用）。

## 客户端配置示例（Claude Desktop / Claude Code）

```json
{
  "mcpServers": {
    "matsci-kb": {
      "command": "python",
      "args": ["/path/to/matsci-kb-kit/mcp/server.py", "--vault", "/path/to/my-vault"]
    }
  }
}
```

## 工具清单（19 个）

**只读（默认即可用）**：`kb_route`（首选，分层取证）、`kb_search`、`kb_resolve`、
`kb_where`、`kb_corpus_search`、`kb_graph`、`kb_backlinks`、`kb_stats`、`kb_tags`、
`kb_dois`、`kb_cite`、`lit_batch`、`lit_gapscan`，以及诊断类 `kb_doctor`、`kb_lint`、
`kb_selftest`、`kb_toolcheck`、`lit_doctor`。

**写（需双钥）**：`kb_build_index`——需 server 以 `--allow-write` 启动 **且** 调用方传 `apply=true`。

## 两条设计选择

1. **不用常驻 daemon**。server 以 subprocess 调库自己的 CLI，因此天然继承
   `kb.py` 的「若 `kb_serve` 在跑就代理、否则进程内」逻辑。
   `kb_serve` 是**可选加速器**，不是硬依赖——避免 daemon 生命周期带来的支持负担。
2. **调度不进 MCP**。MCP 协议没有调度器。`lit_daily` 的每日发现应放在 OS 侧：
   - Linux/macOS（cron）：`47 7 * * * cd /path/to/vault && python tools/lit_daily.py`
   - Windows（任务计划程序）：写一个两行的包装脚本，把**库根**当参数传进去，例如
     ```bat
     @echo off
     cd /d "%~1"
     set OPENALEX_API_KEY=<你的key>
     python tools\lit_daily.py
     ```
     计划任务调用它并传库根路径。把 key 放在包装脚本里（而非 `lit_config.yaml`）
     是因为库通常被 git 跟踪，而包装脚本可以留在库外。
   详见 `docs/GETTING-STARTED.md` 与技能 `lit-watch`。
