#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""kb_init.py — 把 matsci-kb-kit 的工具与方法论初始化进一个**空** Obsidian 库。

幂等：已存在的文件在无 --force 时绝不覆盖。

用法：
  python scripts/kb_init.py --target /path/to/your/vault
  python scripts/kb_init.py --target <vault> --force        # 允许覆盖已存在文件
  python scripts/kb_init.py --target <vault> --no-index     # 跳过索引构建
"""
import argparse
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.dirname(HERE)
SCAFFOLD = os.path.join(KIT, "scaffold")
PY = sys.executable


def read_lines(p):
    out = []
    if os.path.isfile(p):
        for ln in open(p, encoding="utf-8"):
            ln = ln.strip()
            if ln and not ln.startswith("#"):
                out.append(ln)
    return out


def _disp(p):
    try:
        return os.path.relpath(p)
    except ValueError:                    # 跨盘符（Windows 上两个不同盘符之间无相对路径）
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", required=True, help="目标库根（将创建/填充）")
    ap.add_argument("--force", action="store_true", help="覆盖已存在文件")
    ap.add_argument("--no-index", action="store_true", help="不构建索引")
    args = ap.parse_args()

    tgt = os.path.abspath(args.target)

    def log(m):
        print(m, flush=True)

    log(f"目标库: {tgt}")

    # 1) 建目录
    for d in read_lines(os.path.join(SCAFFOLD, "dirs.txt")):
        full = os.path.join(tgt, *d.split("/"))
        os.makedirs(full, exist_ok=True)
        gk = os.path.join(full, ".gitkeep")
        if not os.path.exists(gk):
            open(gk, "w").close()
    os.makedirs(os.path.join(tgt, "wiki", ".index"), exist_ok=True)
    log(f"[1] 目录已建（{len(read_lines(os.path.join(SCAFFOLD, 'dirs.txt')))} 个）")

    # 2) 元文件
    log("[2] 根元文件")
    copytree(os.path.join(SCAFFOLD, "meta"), os.path.join(tgt, "wiki"), args.force, log)

    # 3) .base 视图
    log("[3] Bases 视图")
    copytree(os.path.join(SCAFFOLD, "bases"), tgt, args.force, log)

    # 4) .obsidian
    log("[4] .obsidian 配置")
    obs = os.path.join(tgt, ".obsidian")
    copytree(os.path.join(SCAFFOLD, "obsidian"), obs, args.force, log)

    # 5) .gitignore
    copy_if_absent(os.path.join(SCAFFOLD, "gitignore.template"),
                   os.path.join(tgt, ".gitignore"), args.force, log)

    # 5b) profile.md（首跑访谈产物，供 /kb-onboard 填写）
    copy_if_absent(os.path.join(SCAFFOLD, "profile.template.md"),
                   os.path.join(tgt, "profile.md"), args.force, log)

    # 6) tools/ + CLAUDE.md（生成物，随 kit 发布）
    log("[5] tools/")
    copytree(os.path.join(KIT, "tools"), os.path.join(tgt, "tools"), args.force, log)
    log("[6] CLAUDE.md")
    claude = os.path.join(KIT, "CLAUDE.md")
    if os.path.isfile(claude):
        copy_if_absent(claude, os.path.join(tgt, "CLAUDE.md"), args.force, log)
    else:
        log("  （kit 未生成 CLAUDE.md，跳过）")

    # 7) lit_config.yaml 由模板写（仅当不存在）
    log("[7] tools/lit_config.yaml")
    copy_if_absent(os.path.join(SCAFFOLD, "lit_config.template.yaml"),
                   os.path.join(tgt, "tools", "lit_config.yaml"), args.force, log)

    # 8) skills（若 kit 有生成）—— 同时装进 .dsh/skills（真源）与 .claude/skills
    #    （Claude Code 从 .claude/skills 发现项目技能）。用**复制**而非 junction，
    #    以保证跨平台（junction 是 Windows 专有）。
    skill_src = os.path.join(KIT, "skills")
    if os.path.isdir(skill_src):
        log("[8] skills/（.dsh + .claude 双入口）")
        copytree(skill_src, os.path.join(tgt, ".dsh", "skills"), args.force, log)
        copytree(skill_src, os.path.join(tgt, ".claude", "skills"), args.force, log)

    # 9) 构建索引（空库也产出合法空索引）
    if not args.no_index:
        log("[9] 构建索引")
        bi = os.path.join(tgt, "tools", "kb_build_index.py")
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        r = subprocess.run([PY, bi, "--lite"], cwd=tgt, env=env)
        log(f"  kb_build_index --lite → exit={r.returncode}")

    log("")
    log("完成。下一步：")
    log(f"  1. 用 Obsidian 打开：{tgt}")
    log(f"  2. 自检：python {os.path.join(tgt, 'tools', 'kb.py')} --doctor")
    log("  3. 把文献放进 raw/，或跑 tools/lit_discover.py 找新文献")
    return 0


if __name__ == "__main__":
    sys.exit(main())
