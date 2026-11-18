# CLAUDE.md — Matsci Knowledge Base 插件仓库

> **配置中枢**。常驻上下文只放「每次都要用」的东西：仓库骨架、不可违背的铁律、入口与指针。
> 流程细节按需加载 `docs/` 与 `skills/`。**本文件不写会过期的统计数字**——工具计数以
> `plugin.yaml` 为准，库内统计以命令输出为准。
> 本文件治理**插件仓库**；交付给用户库的方法论在 `scaffold/CLAUDE.md`
> （由 `kb_init` 物化到库根），两份不要混。

## 〇、怎么读这个文件

- **落点**看 §一，**铁律**看 §二，**构建与验收**看 §三，**踩坑**看 §四，**其余**看 §五 索引表。
- 冲突时以工具输出与代码为准；文中日期只标注规则生效日，不是现状快照。

## 一、仓库骨架

| 目录 | 层 | 职责 |
|---|---|---|
| `tools/` | 工具层（生成物） | `kb.py` 统一入口；`kb_*` 检索/体检、`qc_*` 质检、`lit_*` 文献流水线 |
| `skills/` | 技能层（生成物＋overlay） | 9 个流程技能；overlay 公开泛化补件在 `build/overlay/skills/` |
| `scaffold/` | 库骨架（手写件） | 目录表、根元文件、配置模板、Obsidian 可选层、Bases 视图 |
| `build/` | 构建管线 | `build_plugin.py` ＋ `rules/` 公开规则；`rules/private/` **gitignored** |
| `scripts/` | 手写脚本 | `kb_init` / `audit_tools` / `verify_plugin` / `export_plugin` |
| `mcp/` | MCP server | 20 个工具；双钥写门禁；懒库根解析 |
| `docs/` | 公开文档 | ARCHITECTURE / GETTING-STARTED / MCP / TOOLS / METHODOLOGY |
| `tests/` | 验收测试 | stdlib unittest；依赖 private 的导出类测试在干净 checkout 自动 skip |
| `dist/` | 本地导出（gitignored） | 白名单导出产物，**不随仓库发布** |

**仓库根只允许**：上表目录 ＋ 根文件（`README.md` `CLAUDE.md` `LICENSE` `NOTICE.md`
`package.json` `plugin.yaml` `requirements*.txt`）＋ 双平台安装件
（`.claude-plugin/` `.qoder-plugin/` `.mcp.json`）＋ `.github/`。
**不得为新流程开新目录**：临时/派生/工作区 → `.qc/`（gitignored）；
本地工作文档 → `docs/superpowers/`（gitignored、**永不导出**）。

## 二、铁律

1. **隐私红线**：真实专名只存 `build/rules/private/` 与 `docs/superpowers/`（均 gitignored）；
   被跟踪文件与 commit message 不得出现真实专名。泄漏扫描 fail-closed；
   导出时私有规则缺失**立即中止**（rc=2），不静默降级。
2. **生成物 vs 手写件**：`tools/` `skills/` `plugin.yaml` `docs/METHODOLOGY.md`
   `docs/TOOLS.md` 是生成物——**勿手改**，改真源或规则层后重跑 build；
   手写件可直接改，但**必须列入 `SCAN_TARGETS`**（手写件同样会泄密，不能豁免）。
3. **干跑优先**：写盘脚本默认干跑，`--apply` 显式开启；写前备份、写后复算。
4. **退出码是信号**：不把「失败」静默成「没有结果」；可选依赖缺失明确报错，
   不静默降级（hybrid 缺嵌入索引/Reranker 退 3；caj 环境未就绪退 3）。
5. **空库必须可用**：任何工具在空库上都要自洽（审计标准，`scripts/audit_tools.py`）。
6. **不强制依赖 Obsidian**：纯 Markdown 是默认形态；`--with-obsidian` 才是可选渲染层。

## 三、构建与验收

```bash
python build/build_plugin.py --src <真源库根>   # 真源不内置；源库 dirty 硬门禁
python scripts/verify_plugin.py                # 9 项验收（泄漏/编译/help/冒烟/MCP/白名单/模板）
python -m unittest discover -s tests           # 行为级回归
python scripts/export_plugin.py                # 白名单导出 dist/ ＋ 终审泄漏审计
```

CI（`.github/workflows/verify.yml`）在 ubuntu 上跑 verify_plugin ＋ unittest。
干净 checkout 没有 `private/`：扫描只用公开半份词表（降级会打印 warn），
导出类测试自动 skip——**CI 绿不等于本地终审绿**，发布前本地必须带 private 全量跑。

## 四、已知陷阱

- 🔴 **npm files 白名单压过 .gitignore**：`package.json` 的 `files` 里 build 条目
  逐文件列；写整目录会把 private 规则整包发出去（旧 kit 实测踩过）。
  verify_plugin [8] 把这条断言机械化。
- 🔴 **元数据静默丢失**（交付库的头号失效）：frontmatter 拆/合只走
  `kb_lib.split_frontmatter` / `join_frontmatter`；长字段含冒号必须整体加引号。
- **Windows 管道 GBK**：`kb.py tools --json | python …` 会 JSONDecodeError；
  改重定向到文件 ＋ `python -X utf8` 读取。
- **双平台 .mcp.json 变量**：默认 Qoder 变体 `${QODER_PLUGIN_ROOT}`；
  Claude Code 不展开它，需手动一步换 `${CLAUDE_PLUGIN_ROOT}`（docs/MCP.md）。
- **caj_to_pdf 三分退出码**：0 全过 / 3 仅环境未就绪 / 2 真失败；
  `kb_toolcheck` 只豁免 3，不得按工具名宽豁免。
- **PEP 701 f-string 反斜杠**：表达式内 `b'\r\n'` 这类写法仅 py≥3.12 合法，
  CI 3.11 会 SyntaxError，且 `ast.parse(feature_version=(3,10))` 测不出。
  病灶经公开 `build/rules/compat_scrub.yaml` 在构建期转 `.format`；
  不手改生成物、不动活库。守卫见 `TestCompatScrub`。
- **跨平台语义病灶**：Windows-only 反例（不存在盘符 `Z:`）与 `strip("/")` 吃掉
  POSIX 首斜杠（绝对路径误收）都只在 Linux CI 爆；同经 `compat_scrub.yaml`
  构建期字面替换，`TestCompatScrub` 以双 OS 均成立的断言钉住语义。
- **委托纪律**：「已声明」≠「已生效」——技能在**插件级**注册，`kb_init` 不复制技能进库。

## 五、细则索引

| 要做的事 | 去哪看 |
|---|---|
| 库的组织方式与方法论（交付件） | `scaffold/CLAUDE.md` ＋ `docs/METHODOLOGY.md` |
| 安装 / 建库 / 升级工具 | `docs/GETTING-STARTED.md` |
| 架构与分层设计 | `docs/ARCHITECTURE.md` |
| MCP 挂接、双钥、双平台变体 | `docs/MCP.md` |
| 工具速查 | `docs/TOOLS.md` |
| 构建规则与公开/私有分界 | `build/rules/README.md` |
| 首跑配置访谈 | 技能 `kb-onboard` |
| 检索协议 / 体检 / 文献全链 | 技能 `kb-query` / `kb-lint` / `lit-watch` |
| 文献本地约定 / 浏览器兜底 | 技能 `lit-pipeline` / `lit-browser-fetch` |
| QC 循环 / 审稿循环 / 批次 ingest | 技能 `kb-qc-loop` / `kb-review-cycle` / `kb-ingest-batch` |

---
_基于 [karpathy/llm-wiki](https://github.com/karpathy/llm-wiki) 的构想构建；仓库谱系续接 matsci-kb-kit（v0.4.0）。_