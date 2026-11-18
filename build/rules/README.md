# build/rules/ — 生成规则（公开件与私有件的分界）

`build/build_plugin.py` 从源知识库（真源）生成这个插件。生成时做两件事：**过滤**（哪些文件随包）
和**去个人化**（把源库的专名换成占位符）。规则就放在这里。

## 🔴 为什么规则要分公开/私有两份

去个人化规则**本身就是敏感数据**：要替换掉源库的专名，就得先把专名写在规则里。

而 `build/` 进 git，同时**刻意不在泄漏扫描范围内**（`SCAN_TARGETS` 不含 `build/`）——
因为规则必须以字面量保存这些专名，否则无从替换。

两者相加的后果是：如果规则直接放在 `build/rules/` 下发布，生成器就会把它本该抹掉的东西
原样公开：本机用户名、库根路径、文献管理器的数据目录、个人文献文件夹名，以及整份研究方向清单。

所以：**凡含专名的规则一律放 `build/rules/private/`，该目录 gitignored**，仓库里只留
`examples/` 下的假值模板。

### 🔴 npm 侧的同一个坑（历史教训，当前已整体规避）

`.gitignore` **管不住 npm 包**。npm 明确规定：被 `package.json` 的 `files` 字段收进来的文件，
无法再用 `.npmignore` / `.gitignore` 排除。

kit 时代曾实测：`files` 里写着 `"build/"` 时，`npm pack --dry-run` 把 `build/rules/private/` 下
五个含源库专名的规则文件**整包发了出去**——`.gitignore` 一点作用都没有。

本插件的 `package.json` 因此**完全不收 `build/`**：构建管线与规则不随 npm 包分发，
`files` 只列运行时需要的目录与文件（与当前 `package.json` 一致）：

```jsonc
".claude-plugin/", ".qoder-plugin/", ".mcp.json",
"skills/", "tools/", "scaffold/", "scripts/kb_init.py",
"mcp/server.py", "mcp/requirements.txt",
"docs/ARCHITECTURE.md", "docs/GETTING-STARTED.md", "docs/MCP.md",
"docs/TOOLS.md", "docs/METHODOLOGY.md",
"requirements.txt", "requirements-optional.txt",
"README.md", "LICENSE", "NOTICE.md", "plugin.yaml"
```

`tests/test_manifests.py` 把「`files` 不得含任何 `build` 条目」机械化了。
若将来确需随包发布个别 build 公开件，必须**逐文件列**（如 `"build/rules/README.md"`），
绝不能写 `"build/"` 整目录——漏补一行 = 包里少文件，会当场炸，
而不是悄悄多泄一份专名；方向是安全的。

## 目录布局

```
build/rules/
├── include.txt            公开 · 随包工具白名单（纯文件名，不含专名）
├── exclude.txt            公开 · 刻意排除项的审计记录 + 理由
├── leak_denylist.txt      公开 · 通用形态规则（家目录/用户名路径）
├── compat_scrub.yaml      公开 · Python 版本兼容字面替换（PEP 701 f-string → .format），未命中告警
├── examples/              公开 · 私有规则的假值模板，供新用户起步
│   ├── scrub.yaml
│   ├── global_scrub.yaml
│   ├── drop_sections.yaml
│   ├── skill_scrub.yaml
│   └── leak_denylist.txt
└── private/               🔴 gitignored · 一切含专名的规则
    ├── scrub.yaml             按文件的结构性改写（改代码语义/删整段/换实现），未命中告警
    ├── global_scrub.yaml      纯专名 → 占位符，对每个生成物都跑，未命中不告警
    ├── drop_sections.yaml     CLAUDE.md / TOOLS.md 的块级删除（rules / drop_headings / drop_lines）
    ├── skill_scrub.yaml       技能文件的正则替换（散文里专名形态多，字面量覆盖不住）
    └── leak_denylist.txt      源库专名清单，fail-closed 扫描的私有半份
```

## 新用户怎么用

```bash
cp -r build/rules/examples/. build/rules/private/    # 然后逐个文件把假值换成你的专名
export MATSCI_KB_SRC="/path/to/你的知识库"           # 或直接 --src
python build/build_plugin.py --src "$MATSCI_KB_SRC" --out .
```

`build_plugin.py` **不内置任何本机路径**：`--src` 缺省读 `MATSCI_KB_SRC`，两者都没有就中止。

私有规则缺失时的行为（不静默降级）：

| 场景 | 行为 |
|---|---|
| 生成（无 `--check`） | **中止**，退出码 2，列出缺哪些文件 |
| 只跑扫描（`--check`） | 继续，但打印 `[warn]` 说明「只按通用规则扫描，专名不在拦截范围内」 |

`--check` 之所以能跑，是因为公开那份 `leak_denylist.txt` 独立有效——在没有 `private/` 的
干净 checkout 上仍然拦住家目录/用户名泄漏。全量验收脚本 `scripts/verify_plugin.py`
（含私有规则隔离断言）**即将提供**（Task 10）；在它落地前，`--check` + `tests/` 是同等判据。

## 三层去个人化的顺序

对每个生成物依次施加，顺序有意义（具体在前、兜底在后）：

1. `scrub.yaml` —— 按文件的结构性改写
2. `global_scrub.yaml` —— 全局专名字面替换
3. 载体特有：`drop_sections.yaml`（CLAUDE.md / TOOLS.md）、`skill_scrub.yaml`（skills/）
4. 生成完毕后 `scan_leaks()` 用**公开 + 私有**两份 denylist 扫整个输出树，任一命中即构建失败

第 4 步是 fail-closed 的兜底：前三步漏了什么，构建不会成功。

tools 另有一层**公开兼容层** `compat_scrub.yaml`，在全局专名替换之后施加：
活库跑在较新 Python 上，而插件声明 ≥3.10（CI 跑 3.11）。PEP 701 允许 f-string
**表达式内**出现反斜杠仅 py≥3.12，3.11 下是 SyntaxError；且
`ast.parse(feature_version=(3,10))` 检测不到该词法差异。故按逐文件字面量把病灶
转成 `.format`（反斜杠落在表达式外）。本表不含专名、公开可跟踪；未命中即告警
（漂移可见）。守卫：`tests/test_build.py::TestCompatScrub` 钉住两处已知病灶，
并在 py≥3.12 上用 tokenize 深度跟踪全仓扫描表达式内反斜杠（0 命中才过）。
