# build/ — 生成器

本 kit 的 `tools/`、`skills/`、`CLAUDE.md`、`docs/METHODOLOGY.md`、`docs/TOOLS.md`、`kit.yaml`
是**派生数据**：由 `build_kit.py` 从一份**源知识库**（真源）过滤 + 去个人化生成。
真源不在此仓库；生成物请勿手改，改真源后重跑生成器。

## 用法

```bash
export MATSCI_KB_SRC="/path/to/你的知识库"    # Windows: set MATSCI_KB_SRC=...
python build/build_kit.py                     # 生成到本仓库根
python build/build_kit.py --src <库根> --out <kit根>
python build/build_kit.py --check             # 只跑泄漏扫描
```

生成器**不内置任何本机路径**：`--src` 缺省读 `MATSCI_KB_SRC`，两者都没有就中止（退出码 2）。

## 规则（`rules/`）

分**公开件**与 **gitignored 的 `rules/private/`**——去个人化规则本身就含源库专名，
发布它们等于把生成器要抹掉的东西原样公开。分工、目录布局、新用户起步方法见
**[`rules/README.md`](rules/README.md)**（唯一的权威说明，此处不再重复以免漂移）。

## 五条不变量

1. **`--out` 不得落在 `--src` 内**（硬门禁，防止把生成物写回真源）。
2. **生成后全树泄漏扫描**：公开通用词表 + 私有专名词表合并后跑，任一命中即构建失败。
3. **漂移可见**：`scrub` / `drop_sections` / `drop_lines` 规则若在真源找不到目标会告警；
   残留泄漏由第 2 条兜底为失败。
4. **`include.txt` 必须对 import 闭合**（`kb.py` 动态导入 `kb_rag`／`kb_agentic`，
   工具之间也互相 `import`）。漏收一个 ⇒ 生成物在自己仓库里 `ImportError`。
5. **`rules/private/` 永不发布**：git 靠 `.gitignore`，npm 靠 `files` 逐文件白名单
   （`.gitignore` 管不住 npm 包，见 `rules/README.md`）。

私有规则缺失时**不静默降级**：生成中止；`--check` 仍可跑但打印 `[warn]` 说明降级范围。

## 验证

```bash
python build/build_kit.py --check    # 只跑泄漏扫描（快）
python scripts/verify_kit.py         # 泄漏扫描 + py_compile + --help + 空库冒烟 + MCP + npm 白名单
```

CI 在每次 push／PR 跑 `verify_kit.py`（`.github/workflows/verify.yml`）。
修改 `build/` 后请重跑生成器与 `verify_kit.py`。
