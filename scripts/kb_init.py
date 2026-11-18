#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""kb_init.py — 把 Matsci Knowledge Base 插件的工具与方法论物化进一个空知识库。

默认纯 Markdown 模式：产物不含任何 Obsidian 专属文件，工具链独立运作。
--with-obsidian 额外铺设可选层（.base 视图 + .obsidian 配置）。
幂等：已存在的文件在无 --force 时绝不覆盖。

用法：
  python scripts/kb_init.py --target /path/to/vault
  python scripts/kb_init.py --target <vault> --with-obsidian
  python scripts/kb_init.py --target <vault> --update-tools   # 插件升级后重新物化 tools/
  python scripts/kb_init.py --target <vault> --check-deps     # 只检查核心依赖
"""
import argparse
import importlib.util
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.dirname(HERE)
SCAFFOLD = os.path.join(PLUGIN, "scaffold")
PY = sys.executable
CORE_DEPS = [("yaml", "pyyaml"), ("jieba", "jieba"),
             ("numpy", "numpy"), ("fitz", "PyMuPDF")]


def read_lines(p):
    out = []
    if os.path.isfile(p):
        with open(p, encoding="utf-8") as fh:
            for ln in fh:
                ln = ln.strip()
                if ln and not ln.startswith("#"):
                    out.append(ln)
    return out


def _disp(p):
    try:
        return os.path.relpath(p)
    except ValueError:
        return p


def copy_if_absent(src, dst, force, log):
    if os.path.exists(dst) and not force:
        log(f"  跳过（已存在）{_disp(dst)}")
        return
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    log(f"  写入 {_disp(dst)}")


def copytree(src, dst, force, log):
    for dp, _, fs in os.walk(src):
        rel = os.path.relpath(dp, src)
        if "__pycache__" in rel.split(os.sep):
            continue
        for f in fs:
            if f.endswith((".pyc", ".pyo")):
                continue
            s = os.path.join(dp, f)
            d = os.path.join(dst, rel, f) if rel != "." else os.path.join(dst, f)
            copy_if_absent(s, d, force, log)


def check_deps(log):
    missing = [pip for mod, pip in CORE_DEPS
               if importlib.util.find_spec(mod) is None]
    if missing:
        log("[deps] 缺少核心依赖：")
        log(f"       {PY} -m pip install {' '.join(missing)}")
        return 1
    log("[deps] 核心依赖齐全（pyyaml/jieba/numpy/PyMuPDF）")
    return 0


def update_tools(tgt, log):
    """重新物化 tools/：顶层文件全量替换（lit_config.yaml 除外，保留用户配置）、
    子目录合并（同名覆盖、多余文件保留）、旧件整体备份到 _archive/tools-backup-<时间戳>
    （同秒冲突时追加 -2/-3… 序号后缀）。知识数据不动。"""
    tools_dst = os.path.join(tgt, "tools")
    if not os.path.isdir(tools_dst):
        log("[ABORT] --update-tools 需要已建好的库（缺 tools/）；先跑普通建库。")
        return 2
    stamp = time.strftime("%Y%m%d-%H%M%S")
    backup = os.path.join(tgt, "_archive", f"tools-backup-{stamp}")
    n = 2
    while os.path.exists(backup):
        backup = os.path.join(tgt, "_archive", f"tools-backup-{stamp}-{n}")
        n += 1
    shutil.copytree(tools_dst, backup,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    log(f"[update] 旧 tools 已备份 → {_disp(backup)}")
    for f in os.listdir(tools_dst):
        fp = os.path.join(tools_dst, f)
        if os.path.isfile(fp) and f != "lit_config.yaml":
            os.remove(fp)
    copytree(os.path.join(PLUGIN, "tools"), tools_dst, True, log)
    tpl = os.path.join(SCAFFOLD, "lit_config.template.yaml")
    cfg = os.path.join(tools_dst, "lit_config.yaml")
    if not os.path.exists(cfg):
        copy_if_absent(tpl, cfg, False, log)
    log("[update] 完成：知识数据未动，仅 tools/ 重新物化。")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", required=True, help="目标库根（将创建/填充）")
    ap.add_argument("--force", action="store_true", help="覆盖已存在文件")
    ap.add_argument("--no-index", action="store_true", help="不构建索引")
    ap.add_argument("--with-obsidian", action="store_true",
                    help="铺设 Obsidian 可选层（.base 视图 + .obsidian 配置）")
    ap.add_argument("--check-deps", action="store_true", help="只检查核心依赖")
    ap.add_argument("--update-tools", action="store_true",
                    help="插件升级后重新物化 tools/（备份旧件，不动知识数据）")
    args = ap.parse_args()
    tgt = os.path.abspath(args.target)

    def log(m):
        print(m, flush=True)

    if args.check_deps:
        return check_deps(log)
    if args.update_tools:
        return update_tools(tgt, log)

    log(f"目标库: {tgt}（{'纯 Markdown + Obsidian 可选层' if args.with_obsidian else '纯 Markdown'}）")

    for d in read_lines(os.path.join(SCAFFOLD, "dirs.txt")):
        full = os.path.join(tgt, *d.split("/"))
        os.makedirs(full, exist_ok=True)
        gk = os.path.join(full, ".gitkeep")
        if not os.path.exists(gk):
            open(gk, "w").close()
    os.makedirs(os.path.join(tgt, "wiki", ".index"), exist_ok=True)
    log("[1] 目录已建")

    log("[2] 元文件")
    copytree(os.path.join(SCAFFOLD, "meta"), os.path.join(tgt, "wiki"), args.force, log)

    if args.with_obsidian:
        log("[3] Obsidian 可选层（.base + .obsidian）")
        copytree(os.path.join(SCAFFOLD, "bases"), tgt, args.force, log)
        copytree(os.path.join(SCAFFOLD, "obsidian"),
                 os.path.join(tgt, ".obsidian"), args.force, log)
    else:
        log("[3] 跳过 Obsidian 层（默认纯 Markdown；需要时 --with-obsidian）")

    copy_if_absent(os.path.join(SCAFFOLD, "gitignore.template"),
                   os.path.join(tgt, ".gitignore"), args.force, log)
    copy_if_absent(os.path.join(SCAFFOLD, "gitattributes.template"),
                   os.path.join(tgt, ".gitattributes"), args.force, log)
    copy_if_absent(os.path.join(SCAFFOLD, "profile.template.md"),
                   os.path.join(tgt, "profile.md"), args.force, log)
    copy_if_absent(os.path.join(SCAFFOLD, "archive-README.template.md"),
                   os.path.join(tgt, "_archive", "README.md"), args.force, log)

    log("[4] tools/")
    copytree(os.path.join(PLUGIN, "tools"), os.path.join(tgt, "tools"), args.force, log)
    log("[5] CLAUDE.md")
    copy_if_absent(os.path.join(SCAFFOLD, "CLAUDE.md"),
                   os.path.join(tgt, "CLAUDE.md"), args.force, log)

    log("[6] tools/lit_config.yaml（模板占位，/kb-onboard 访谈后填写）")
    copy_if_absent(os.path.join(SCAFFOLD, "lit_config.template.yaml"),
                   os.path.join(tgt, "tools", "lit_config.yaml"), args.force, log)

    if not args.no_index:
        log("[7] 构建索引")
        bi = os.path.join(tgt, "tools", "kb_build_index.py")
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        r = subprocess.run([PY, bi, "--lite"], cwd=tgt, env=env)
        log(f"  kb_build_index --lite → exit={r.returncode}")
        if r.returncode != 0:
            log("[ABORT] 索引构建失败，退出码透传；请检查上方输出。")
            return r.returncode

    log("")
    log("完成。下一步：")
    log(f"  1. 自检：python {os.path.join(tgt, 'tools', 'kb.py')} --doctor")
    log("  2. 在 agent 中跑 /kb-onboard 访谈，填写 profile.md 与 lit_config.yaml")
    log("  3. 把文献放进 raw/，或跑 tools/lit_discover.py 找新文献")
    log("  （本库为纯 Markdown，任何编辑器可读；Obsidian 仅为可选渲染器）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
