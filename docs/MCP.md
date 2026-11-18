# MCP server

`mcp/server.py` 把库的工具链暴露为 **MCP 工具**，任何支持 MCP 的 AI 客户端
（Claude Code / Qoder / Claude Desktop / 其他）都能直接调用。随插件安装时由
`.mcp.json` 自动声明；也可脱离插件手动运行。

## 运行

```bash
pip install -r mcp/requirements.txt          # 官方 mcp SDK
python mcp/server.py --vault /path/to/vault               # stdio（只读工具）
python mcp/server.py --vault /path/to/vault --allow-write # 额外允许写工具
```

不带 SDK 也能用 `--list-tools` / `--selftest`（CI 用）。

### 懒 vault 解析

库根解析顺序：`--vault` 参数 > `MATSCI_KB_VAULT` 环境变量 > 当前目录。
解析是**懒**的：vault 未就绪（缺 `tools/kb_lib.py`）时 server **仍可启动**，
只是除 `kb_init` 外的工具不可用——`kb_init` 走插件自带的 `scripts/kb_init.py`，
不依赖已有库，纯 MCP 也能从零建库。建好库后重启 server 或传 `--vault` 即可。

### 写工具双钥门禁

写工具（`kb_build_index`、`kb_init`）需要**两把钥匙同时到位**：

1. server 以 `--allow-write` 启动（默认关；未开启时任何 `apply=true` 一律拒绝）；
2. 调用方显式传 `apply=true`（默认干跑）。

这与工具链「默认干跑、`--apply` 显式开启」的写盘纪律同构。

## 工具清单（20 个）

**只读（默认即可用，18 个）**：`kb_route`（首选，分层取证）、`kb_search`、`kb_resolve`、
`kb_where`、`kb_corpus_search`、`kb_graph`、`kb_backlinks`、`kb_stats`、`kb_tags`、
`kb_dois`、`kb_cite`、`lit_batch`、`lit_gapscan`，以及诊断类 `kb_doctor`、`kb_lint`、
`kb_selftest`、`kb_toolcheck`、`lit_doctor`。

**写（需双钥，2 个）**：`kb_build_index`（重建索引）、`kb_init`（从零建库；
`with_obsidian=true` 铺可选层。升级已有库的 `--update-tools` 走 CLI，见 GETTING-STARTED §9）。

工具注册表真源是 `mcp/server.py` 的 `TOOLS` 列表；`--list-tools` 可机器可读地核对。

## 插件配置：两个根变量变体

两平台的插件根变量不同：Qoder 展开 `${QODER_PLUGIN_ROOT}`，Claude Code 展开
`${CLAUDE_PLUGIN_ROOT}`，且 Claude Code **不展开** QODER 变量（实测 CONNECTION_CLOSED，
诊断报 Missing environment variables）。仓库提交的 `.mcp.json` 默认 = **Qoder 变体**：

```json
{
  "mcpServers": {
    "matsci-kb": {
      "command": "python",
      "args": ["${QODER_PLUGIN_ROOT}/mcp/server.py"],
      "timeout": 120000
    }
  }
}
```

### Claude Code 启用 MCP（手动一步，已实测有效）

1. 编辑插件源目录的 `.mcp.json`，把 args[0] 的 `${QODER_PLUGIN_ROOT}` 改为
   `${CLAUDE_PLUGIN_ROOT}`：

   ```json
   {
     "mcpServers": {
       "matsci-kb": {
         "command": "python",
         "args": ["${CLAUDE_PLUGIN_ROOT}/mcp/server.py"],
         "timeout": 120000
       }
     }
   }
   ```

2. 重启 Claude Code 会话（或 `/reload-plugins`）。**无需重装**：会话读 live 源目录的
   `.mcp.json`，不是安装缓存（已用判别实验证实）。
3. 需要写工具（如 `kb_init` `apply=true`）时再在 args 追加 `"--allow-write"`
   （双钥门禁之一；默认关）。
4. 验证：`claude mcp list` 应显示 `plugin:matsci-knowledge-base:matsci-kb` ✔ Connected；
   工具名前缀 `mcp__plugin_matsci-knowledge-base_matsci-kb__`（20 个）。

⚠️ 注意：

- 此改动是**用户本机配置行为**，不应提交回仓库（仓库默认保持 Qoder 变体供 Qoder 安装）。
- **project-config 重复条目**：在插件源目录内运行 claude 时，仓库 `.mcp.json` 兼作
  项目配置被再加载一次，出现第二个不带 `plugin:` 前缀的 `matsci-kb`（Pending approval /
  CONNECTION_CLOSED）。那不是插件服务，勿据它判断插件 MCP 状态。
- Qoder 侧 `${QODER_PLUGIN_ROOT}` 的展开机制有同形态先例，但**新会话中的运行时加载
  留待验收确认**，本文不声称已验证。

### 手动配置（脱离插件，任意客户端）

```json
{
  "mcpServers": {
    "matsci-kb": {
      "command": "python",
      "args": ["/path/to/plugin/mcp/server.py", "--vault", "/path/to/my-vault"]
    }
  }
}
```

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
