#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""verify_kit.py — kit 自检（可作 CI / GitHub Action 用）。

检查：
  1. 泄漏扫描（复用 build_kit.scan_leaks）：0 命中
  2. 全部生成工具 py_compile 通过
  3. 每个随包工具 --help 可运行（不产生副作用）
  4. 空库冒烟：临时目录跑 kb_init → kb_build_index → kb_search（不 exit 2）→ kb_toolcheck
  5. MCP server：注册表可列 + 对空库实跑一个只读工具
  6. npm files 白名单不会把 build/rules/private/ 打进包

用法：python scripts/verify_kit.py [--kit <kit根>]
退出码：0 全绿；非 0 表示失败项数。
"""
import argparse
import os
import subprocess
import sys
import tempfile
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
KIT_ROOT = os.path.dirname(HERE)
BUILD = os.path.join(KIT_ROOT, "build")
sys.path.insert(0, BUILD)
import build_kit as BK                                        # noqa: E402

PY = sys.executable


def run(argv, cwd=None, timeout=300):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run(argv, cwd=cwd, capture_output=True, text=True,
                          timeout=timeout, encoding="utf-8", errors="replace", env=env)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kit", default=KIT_ROOT)
    ap.add_argument("--skip-smoke", action="store_true", help="跳过空库冒烟（CI 快速档）")
    args = ap.parse_args()
    kit = os.path.abspath(args.kit)
    fails = 0

    # 1) 泄漏扫描
    hits = BK.scan_leaks(kit)
    print(f"[1] 泄漏扫描：{len(hits)} 命中")
    for f, i, pat, txt in hits[:20]:
        print(f"      {f}:{i} [{pat}] {txt}")
    fails += len(hits)

    # 2) py_compile
    tools_dir = os.path.join(kit, "tools")
    rc = run([PY, "-m", "compileall", "-q", tools_dir])
    print(f"[2] py_compile：{'OK' if rc.returncode == 0 else 'FAIL'}")
    if rc.returncode != 0:
        print(rc.stdout); print(rc.stderr); fails += 1

    # 3) --help on each tool（手写 argv 工具打印用法后可能非 0 退出；能出用法即算通过）
    bad = []
    for dp, _, fs in os.walk(tools_dir):
        for f in fs:
            if f.endswith(".py"):
                fp = os.path.join(dp, f)
                r = run([PY, fp, "--help"], timeout=60)
                out = (r.stdout or "") + (r.stderr or "")
                ok = r.returncode == 0 or "用法" in out or "usage" in out.lower()
                if not ok:
                    bad.append(os.path.relpath(fp, kit))
    print(f"[3] --help：{len(bad)} 个失败")
    for b in bad:
        print(f"      {b}")
    fails += len(bad)

    # 4) 空库冒烟
    if not args.skip_smoke:
        with tempfile.TemporaryDirectory() as td:
            init = os.path.join(kit, "scripts", "kb_init.py")
            if not os.path.isfile(init):
                print("[4] 空库冒烟：跳过（kb_init.py 尚未生成）")
            else:
                tgt = os.path.join(td, "vault")
                os.makedirs(tgt)
                r1 = run([PY, init, "--target", tgt], timeout=300)
                r2 = run([PY, os.path.join(tgt, "tools", "kb_build_index.py"), "--lite"], cwd=tgt, timeout=300)
                r3 = run([PY, os.path.join(tgt, "tools", "kb_search.py"), "x"], cwd=tgt, timeout=300)
                r4 = run([PY, os.path.join(tgt, "tools", "kb_toolcheck.py")], cwd=tgt, timeout=600)
                ok = (r1.returncode == 0 and r2.returncode == 0
                      and r3.returncode == 0 and r4.returncode == 0)
                print(f"[4] 空库冒烟：{'OK' if ok else 'FAIL'}"
                      f"  (init={r1.returncode} build={r2.returncode}"
                      f" search={r3.returncode} toolcheck={r4.returncode})")
                if not ok:
                    for tag, r in (("init", r1), ("build", r2), ("search", r3), ("toolcheck", r4)):
                        if r.returncode != 0:
                            print(f"      [{tag}] rc={r.returncode}\n{r.stdout[-800:]}\n{r.stderr[-800:]}")
                    fails += 1

                # 5) MCP server（注册表 + 对空库实跑一个只读工具）
                mcp_srv = os.path.join(kit, "mcp", "server.py")
                if os.path.isfile(mcp_srv):
                    r5 = run([PY, mcp_srv, "--list-tools"], timeout=60)
                    r6 = run([PY, mcp_srv, "--vault", tgt, "--selftest"], timeout=180)
                    ok_mcp = r5.returncode == 0 and r6.returncode == 0
                    print(f"[5] MCP server：{'OK' if ok_mcp else 'FAIL'}")
                    if not ok_mcp:
                        print(r5.stdout[-500:]); print(r6.stdout[-500:]); fails += 1

    # 6) npm 包不得含私有去个人化规则
    # 🔴 files 白名单会**压过** .gitignore：npm 明确规定「被 files 收进来的文件无法再用
    #    .npmignore/.gitignore 排除」。曾实测 package.json 写 "build/" 时，npm pack 把
    #    build/rules/private/ 下五个含源库专名的规则文件整包发了出去。
    #    所以这里把 files 里所有 build* 条目按 glob 展开，断言没有一条落在 rules/private。
    import glob as _glob
    import json as _json
    pkg = os.path.join(kit, "package.json")
    leaked = []
    if os.path.isfile(pkg):
        with open(pkg, "r", encoding="utf-8") as f:
            entries = _json.load(f).get("files") or []
        for e in entries:
            if not (e == "build" or e.startswith("build/")):
                continue
            base = os.path.join(kit, e.rstrip("/"))
            paths = (_glob.glob(os.path.join(base, "**"), recursive=True)
                     if e.endswith("/") else [base])
            for p in paths:
                rel = os.path.relpath(p, kit).replace("\\", "/")
                if "rules/private" in rel:
                    leaked.append(f"files 条目 {e!r} → {rel}")
        ok_pkg = not leaked
        print(f"[6] npm files 白名单：{'OK' if ok_pkg else 'FAIL'}")
        if not ok_pkg:
            for x in leaked:
                print(f"      {x}")
            print("      修法：把 files 里的 \"build/\" 换成逐条公开文件"
                  "（见 build/rules/README.md 的「为什么不能整目录白名单」）")
            fails += 1

    print("")
    print(f"=== verify_kit：{'PASS' if fails == 0 else f'FAIL ({fails})'} ===")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
