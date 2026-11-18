#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""verify_plugin.py — 插件全量验收（spec §9）。退出码 0 全绿，非 0 = 有失败项。"""
import argparse
import json
import os
import pathlib
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "build"))
import build_plugin as BP  # noqa: E402

PY = sys.executable
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")


def run(argv, cwd=None, timeout=600):
    return subprocess.run(argv, cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=ENV, timeout=timeout)


def smoke(vault, with_obsidian):
    """建库 → doctor → build_index → search → toolcheck；返回 (ok, 详情)。"""
    init = [PY, os.path.join(ROOT, "scripts", "kb_init.py"), "--target", vault]
    if with_obsidian:
        init.append("--with-obsidian")
    r1 = run(init)
    t = pathlib.Path(vault)
    r2 = run([PY, str(t / "tools" / "kb.py"), "--doctor"], cwd=vault)
    r3 = run([PY, str(t / "tools" / "kb_build_index.py"), "--lite"], cwd=vault)
    r4 = run([PY, str(t / "tools" / "kb_search.py"), "x"], cwd=vault)
    r5 = run([PY, str(t / "tools" / "kb_toolcheck.py")], cwd=vault, timeout=900)
    ok = all(r.returncode == 0 for r in (r1, r2, r3, r4, r5))
    detail = (f"init={r1.returncode} doctor={r2.returncode} build={r3.returncode}"
              f" search={r4.returncode} toolcheck={r5.returncode}")
    if not ok:
        for tag, r in (("init", r1), ("doctor", r2), ("build", r3),
                       ("search", r4), ("toolcheck", r5)):
            if r.returncode != 0:
                detail += f"\n[{tag}] {r.stdout[-4000:]}\n{r.stderr[-2000:]}"
    if r5.returncode != 0:
        # toolcheck 的 notes 只留 selftest 末行，定位不了失败子项；
        # 红的时候把对应 selftest 全文重跑 dump 出来（CI 日志即诊断）。
        import re as _re
        names = dict.fromkeys(_re.findall(r"· (\S+\.py): selftest:", r5.stdout or ""))
        for name in names:
            rr = run([PY, str(t / "tools" / name), "--selftest"], cwd=vault, timeout=300)
            detail += (f"\n[selftest-full {name} rc={rr.returncode}]\n"
                       f"{rr.stdout}\n{rr.stderr[-2000:]}")
    return ok, detail, t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-smoke", action="store_true")
    args = ap.parse_args()
    fails = 0

    hits = BP.scan_leaks(ROOT)
    print(f"[1] 泄漏扫描：{len(hits)} 命中")
    for f, i, pat, txt in hits[:20]:
        print(f"    {f}:{i} [{pat}] {txt}")
    fails += len(hits)

    rc = run([PY, "-m", "compileall", "-q", os.path.join(ROOT, "tools")])
    print(f"[2] py_compile：{'OK' if rc.returncode == 0 else 'FAIL'}")
    fails += rc.returncode != 0

    bad = []
    for dp, _, fs in os.walk(os.path.join(ROOT, "tools")):
        for f in fs:
            if f.endswith(".py"):
                fp = os.path.join(dp, f)
                r = run([PY, fp, "--help"], timeout=60)
                out = (r.stdout or "") + (r.stderr or "")
                if not (r.returncode == 0 or "用法" in out or "usage" in out.lower()):
                    bad.append(f)
    print(f"[3] --help：{len(bad)} 个失败 {bad[:10]}")
    fails += len(bad)

    if not args.skip_smoke:
        with tempfile.TemporaryDirectory() as td:
            v1 = os.path.join(td, "plain")
            ok, detail, t = smoke(v1, False)
            no_obs = not (t / ".obsidian").exists() and not list(t.rglob("*.base"))
            print(f"[4] 纯 Markdown 冒烟：{'OK' if ok and no_obs else 'FAIL'} ({detail})")
            fails += not (ok and no_obs)

            v2 = os.path.join(td, "obs")
            ok2, detail2, t2 = smoke(v2, True)
            base_ok = (t2 / ".obsidian").is_dir()
            if base_ok:
                rbc = run([PY, str(t2 / "tools" / "qc_base_check.py")], cwd=v2)
                base_ok = rbc.returncode == 0
                detail2 += f" base_check={rbc.returncode}"
            print(f"[5] Obsidian 可选层冒烟：{'OK' if ok2 and base_ok else 'FAIL'} ({detail2})")
            fails += not (ok2 and base_ok)

            srv = os.path.join(ROOT, "mcp", "server.py")
            r6 = run([PY, srv, "--list-tools"], timeout=60)
            r7 = run([PY, srv, "--vault", v1, "--selftest"], timeout=300)
            ok_mcp = r6.returncode == 0 and r7.returncode == 0 and "kb_init" in r6.stdout
            print(f"[6] MCP：{'OK' if ok_mcp else 'FAIL'}")
            fails += not ok_mcp

            sentinel = t / "wiki" / "concepts" / "sentinel.md"
            if sentinel.parent.is_dir():
                sentinel.write_text("# sentinel\n", encoding="utf-8")
                r8 = run([PY, os.path.join(ROOT, "scripts", "kb_init.py"),
                          "--target", v1, "--update-tools"])
                r9 = run([PY, str(t / "tools" / "kb.py"), "--doctor"], cwd=v1)
                ok_up = (r8.returncode == 0 and r9.returncode == 0 and sentinel.is_file()
                         and list((t / "_archive").glob("tools-backup-*")))
                print(f"[7] 升级幂等：{'OK' if ok_up else 'FAIL'}")
            else:
                # init 失败时 wiki/concepts 可能未建好；不裸崩，计 FAIL。
                ok_up = False
                print("[7] 升级幂等：FAIL（wiki/concepts 未建好，init 可能失败）")
            fails += not ok_up

    pkg = json.loads((pathlib.Path(ROOT) / "package.json").read_text(encoding="utf-8"))
    leaked = [e for e in pkg.get("files", [])
              if e == "build" or e.startswith("build/") or "superpowers" in e or e == "tests/"]
    print(f"[8] 白名单审计：{'OK' if not leaked else 'FAIL ' + str(leaked)}")
    fails += bool(leaked)

    import yaml
    cfg = yaml.safe_load((pathlib.Path(ROOT) / "scaffold" / "lit_config.template.yaml")
                         .read_text(encoding="utf-8"))
    ok_tpl = isinstance(cfg, dict)
    print(f"[9] onboard 模板可解析：{'OK' if ok_tpl else 'FAIL'}")
    fails += not ok_tpl

    print(f"\n=== verify_plugin：{'PASS' if fails == 0 else f'FAIL ({fails})'} ===")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
