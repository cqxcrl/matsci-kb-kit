#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""export_plugin.py — 白名单导出干净分发包 + 终审泄漏扫描。

禁止整目录拷贝：只复制 WHITELIST 列出的条目（与 package.json files 同源语义）。
导出后对 dist 目录再跑一次 scan_leaks（fail-closed），命中即删除导出并失败。
"""
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "build"))
import build_plugin as BP  # noqa: E402
sys.path.insert(0, os.path.join(ROOT, "tools"))
from kb_lib import console_encoding  # noqa: E402

VERSION = "0.4.0"
WHITELIST = [
    ".claude-plugin/plugin.json", ".qoder-plugin/plugin.json", ".mcp.json",
    "skills", "tools", "scaffold", "scripts/kb_init.py",
    "mcp/server.py", "mcp/requirements.txt",
    "docs/ARCHITECTURE.md", "docs/GETTING-STARTED.md", "docs/MCP.md",
    "docs/TOOLS.md", "docs/METHODOLOGY.md",
    "requirements.txt", "requirements-optional.txt",
    "README.md", "LICENSE", "NOTICE.md", "plugin.yaml",
]


def main():
    # Windows cp936 控制台下管道输出默认按 ANSI 代码页编码，而调用方
    # （tests/test_export_dist.py 等）按 UTF-8 捕获——复用库内统一策略。
    console_encoding()
    # 终审门禁 fail-closed：私有专名规则缺失时绝不降级为仅公开规则扫描
    # （那会打出虚假的「0 命中」）。导出前即中止，不动既有 dist。
    if not os.path.isfile(os.path.join(BP.PRIVATE, "leak_denylist.txt")):
        print("[ABORT] 私有泄漏规则缺失：build/rules/private/leak_denylist.txt"
              " —— 终审门禁 fail-closed，拒绝降级为仅公开规则扫描")
        return 2
    dist = os.path.join(ROOT, "dist", f"matsci-knowledge-base-{VERSION}")
    if os.path.exists(dist):
        shutil.rmtree(dist)
    n = 0
    for rel in WHITELIST:
        src = os.path.join(ROOT, rel)
        dst = os.path.join(dist, rel)
        if not os.path.exists(src):
            print(f"[ABORT] 白名单条目缺失：{rel}（先跑构建/补齐）")
            return 2
        if os.path.isdir(src):
            shutil.copytree(src, dst,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"))
        else:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
        n += 1
    print(f"[export] {n} 个白名单条目 → {dist}")
    hits = BP.scan_leaks(dist)
    if hits:
        print(f"=== 终审泄漏扫描：{len(hits)} 处命中 → 导出作废 ===")
        for f, i, pat, txt in hits:
            print(f"  {f}:{i} [{pat}] {txt}")
        shutil.rmtree(dist)
        return 1
    print("=== 终审泄漏扫描：0 命中 ===")
    print(f"分发包就绪：{dist}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
