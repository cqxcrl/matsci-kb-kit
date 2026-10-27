# build/rules/ — 生成规则（公开件与私有件的分界）

`build/build_kit.py` 从源知识库（真源）生成这个 kit。生成时做两件事：**过滤**（哪些文件随包）
和**去个人化**（把源库的专名换成占位符）。规则就放在这里。

## 🔴 为什么规则要分公开/私有两份

去个人化规则**本身就是敏感数据**：要替换掉源库的专名，就得先把专名写在规则里。

而 `build/` 既进 git 又进 npm 包（见 `package.json` 的 `files`），同时**刻意不在泄漏扫描范围内**
（`SCAN_TARGETS` 不含 `build/`）——因为规则必须以字面量保存这些专名，否则无从替换。

两者相加的后果是：如果规则直接放在 `build/rules/` 下发布，生成器就会把它本该抹掉的东西
原样公开：本机用户名、库根路径、文献管理器的数据目录、个人文献文件夹名，以及整份研究方向清单。

所以：**凡含专名的规则一律放 `build/rules/private/`，该目录 gitignored**，仓库里只留
`examples/` 下的假值模板。

### 🔴 为什么不能整目录白名单（npm 侧的同一个坑）

`.gitignore` **管不住 npm 包**。npm 明确规定：被 `package.json` 的 `files` 字段收进来的文件，
无法再用 `.npmignore` / `.gitignore` 排除。

曾实测：`files` 里写着 `"build/"` 时，`npm pack --dry-run` 把 `build/rules/private/` 下
五个含源库专名的规则文件**整包发了出去**——`.gitignore` 一点作用都没有。

所以 `files` 里的 `build` 条目必须**逐文件列**，不能写 `"build/"`：

```jsonc
"build/README.md",
"build/build_kit.py",
"build/rules/README.md",
"build/rules/include.txt",
"build/rules/exclude.txt",
"build/rules/leak_denylist.txt",
"build/rules/examples/"
```

代价是新增公开件时要手动补一行；方向是安全的（漏补 = 包里少文件，会当场炸，
而不是悄悄多泄一份专名）。`scripts/verify_kit.py` 的第 6 项把这条断言机械化了：
它把 `files` 里所有 `build*` 条目按 glob 展开，命中 `rules/private` 即 FAIL。

## 目录布局

```
build/rules/
├── include.txt            公开 · 随包工具白名单（纯文件名，不含专名）
├── exclude.txt            公开 · 刻意排除项的审计记录 + 理由
├── leak_denylist.txt      公开 · 通用形态规则（家目录/用户名路径）
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
python build/build_kit.py
```

`build_kit.py` **不内置任何本机路径**：`--src` 缺省读 `MATSCI_KB_SRC`，两者都没有就中止。

私有规则缺失时的行为（不静默降级）：

| 场景 | 行为 |
|---|---|
| 生成（无 `--check`） | **中止**，退出码 2，列出缺哪些文件 |
| 只跑扫描（`--check`） | 继续，但打印 `[warn]` 说明「只按通用规则扫描，专名不在拦截范围内」 |

`--check` 之所以能跑，是因为公开那份 `leak_denylist.txt` 独立有效——CI（`.github/workflows/verify.yml`）
正是靠它在没有 `private/` 的干净 checkout 上仍然拦住家目录/用户名泄漏。

## 三层去个人化的顺序

对每个生成物依次施加，顺序有意义（具体在前、兜底在后）：

1. `scrub.yaml` —— 按文件的结构性改写
2. `global_scrub.yaml` —— 全局专名字面替换
3. 载体特有：`drop_sections.yaml`（CLAUDE.md / TOOLS.md）、`skill_scrub.yaml`（skills/）
4. 生成完毕后 `scan_leaks()` 用**公开 + 私有**两份 denylist 扫整个输出树，任一命中即构建失败

第 4 步是 fail-closed 的兜底：前三步漏了什么，构建不会成功。
