#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""audit_tools.py — 在空库上实跑每个随包工具的 --selftest / --help，输出 JSON 报告。

用法：python scripts/audit_tools.py --vault <空库根> [--report build/audit-results.json]
纳入标准（spec §3）：两项均通过才保留；失败项人工判定"可 scrub 修复"或"排除"。
退出码：0 = 全部通过；1 = 存在 FAIL（含 vault/tools 缺文件——先 kb_init --update-tools
同步再审计，缺文件记 FAIL 而不是裸崩）。Task 6 fix 轮起默认非零，无需 --strict。
"""
import argparse
import json
import os
import subprocess
import sys

PY = sys.executable
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run(argv, cwd, timeout=180):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    try:
        r = subprocess.run(argv, cwd=cwd, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=env, timeout=timeout)
        return r.returncode, (r.stdout or "")[-400:], (r.stderr or "")[-400:]
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", required=True)
    ap.add_argument("--report", default=os.path.join(ROOT, "build", "audit-results.json"))
    args = ap.parse_args()
    vault = os.path.abspath(args.vault)
    results = []
    for f in sorted(os.listdir(os.path.join(ROOT, "tools"))):
        if not f.endswith(".py"):
            continue
        fp = os.path.join(vault, "tools", f)
        if not os.path.isfile(fp):
            results.append({"tool": f, "selftest_rc": None, "help_ok": False,
                            "pass": False,
                            "selftest_tail": "MISSING: vault/tools/ 无此文件"
                                             "（先 kb_init --update-tools 同步）"})
            print(f"  [FAIL] {f}  MISSING（vault/tools 缺文件）", flush=True)
            continue
        rc_s, out_s, err_s = run([PY, fp, "--selftest"], vault)
        rc_h, out_h, err_h = run([PY, fp, "--help"], vault, timeout=60)
        help_ok = rc_h == 0 or "用法" in out_h + err_h or "usage" in (out_h + err_h).lower()
        results.append({"tool": f, "selftest_rc": rc_s, "help_ok": help_ok,
                        "pass": rc_s == 0 and help_ok,
                        "selftest_tail": out_s + err_s})
        print(f"  [{'PASS' if results[-1]['pass'] else 'FAIL'}] {f}"
              f"  selftest={rc_s} help={'ok' if help_ok else 'FAIL'}", flush=True)
    with open(args.report, "w", encoding="utf-8") as fh:
        json.dump(results, fh, ensure_ascii=False, indent=1)
    failed = [r["tool"] for r in results if not r["pass"]]
    print(f"\n=== 审计：{len(results) - len(failed)}/{len(results)} 通过 ===")
    for t in failed:
        print(f"  FAIL {t}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())