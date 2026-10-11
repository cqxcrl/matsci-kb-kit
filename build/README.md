# build/ — 生成器

本 kit 的 `tools/`、`skills/`、`CLAUDE.md`、`docs/METHODOLOGY.md`、`docs/TOOLS.md`、`kit.yaml`
是**派生数据**：由 `build_kit.py` 从一份**源知识库**（真源）过滤 + 去个人化生成。

## 用法

```bash
python build/build_kit.py                       # 用默认源库生成到本仓库根
python build/build_kit.py --src <库根> --out <kit根>
python build/build_kit.py --check                # 只跑泄漏扫描
```

## 规则（`rules/`）

| 文件 | 作用 |
|---|---|
| `include.txt` | 白名单：随包发布的工具（相对 `src/tools`） |
| `exclude.txt` | 审计记录：刻意排除项及理由 |
| `scrub.yaml` | 声明式「字面→替换」去个人化表 |
| `drop_sections.yaml` | `CLAUDE.md` 的块级替换（删库专属计数/更名史/悬空指针） |
| `leak_denylist.txt` | fail-closed 泄漏扫描 denylist，命中即构建失败 |

## 三条不变量

1. **`--out` 不得落在 `--src` 内**（硬门禁，防止把生成物写回真源）。
2. **生成后全树泄漏扫描**（`leak_denylist.txt`），任一命中即构建失败。
3. **漂移可见**：块级替换若在真源找不到目标会告警；残留泄漏由第 2 条兜底为失败。

## 验证

```bash
python scripts/verify_kit.py     # 泄漏扫描 + py_compile + --help + 空库冒烟
```

修改 `build/` 后请重跑生成器与 `verify_kit.py`。
