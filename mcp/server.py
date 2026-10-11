#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""server.py — matsci-kb-kit 的 MCP server。

设计（见 docs/MCP.md）：
  · 库根解析：--vault 参数 > MATSCI_KB_VAULT 环境变量 > cwd；要求 <vault>/tools/kb_lib.py 存在。
  · 每个 MCP 工具 = 以 subprocess 调 <vault>/tools/<脚本>.py ... --json。
    因为包装的是库自己的 CLI，天然继承其「常驻服务否则进程内」回退——
    localhost 的 kb_serve 只是**可选加速器**，不是硬依赖。
  · 写路径门禁：--allow-write 默认关；未开启时任何 apply=true 一律拒绝。
  · 调度（lit_daily 的 cron/Task Scheduler）**不在 MCP 范围**，见 docs/MCP.md。

依赖：pip install -r mcp/requirements.txt（官方 mcp SDK）。
不带 SDK 也可运行 --list-tools / --selftest（用于 CI）。

用法：
  python mcp/server.py --vault /path/to/vault            # 启动 stdio server
  python mcp/server.py --vault <vault> --allow-write      # 允许写工具
  python mcp/server.py --list-tools                       # 打印工具清单
  python mcp/server.py --vault <vault> --selftest         # 自检（不需 SDK）
"""
import argparse
import inspect
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
_EMPTY = inspect.Parameter.empty

# ── 工具注册表 ────────────────────────────────────────────────────────────
# 每项：
#   script   : 相对 <vault>/tools/ 的脚本名
#   desc     : 给 LLM 看的说明（每条都吃客户端上下文，务必精简）
#   params   : {名: {flag|pos, type, desc, default?}}
#   write    : True 表示会落盘（需 --allow-write 才可 apply=true）
#   jsonarg  : 是否追加 --json（若脚本支持）
TOOLS = [
    # —— 只读：检索 ——
    {"name": "kb_route", "script": "kb_route.py", "jsonarg": True, "write": False,
     "desc": "分层检索引擎（首选）：一次返回 L1 综合 / L2 文献卡 / L3 原文块，带引用与 low_confidence。",
     "params": {"query": {"pos": True, "type": "string", "desc": "查询"},
                "budget": {"flag": "--budget", "type": "string", "desc": "各层条目数, 如 5,5,8", "default": ""},
                "layer": {"flag": "--layer", "type": "string", "desc": "只取某层 1/2/3", "default": ""}}},
    {"name": "kb_search", "script": "kb_search.py", "jsonarg": True, "write": False,
     "desc": "BM25/语义/混合检索知识库页面。",
     "params": {"query": {"pos": True, "type": "string", "desc": "查询"},
                "k": {"flag": "-k", "type": "string", "desc": "返回条数", "default": "8"},
                "type": {"flag": "--type", "type": "string", "desc": "限定页面类型 concept,entity,source", "default": ""},
                "semantic": {"flag": "--semantic", "type": "boolean", "desc": "用语义检索"},
                "hybrid": {"flag": "--hybrid", "type": "boolean", "desc": "用混合检索"}}},
    {"name": "kb_resolve", "script": "kb_search.py", "jsonarg": True, "write": False,
     "desc": "把口语/缩写解析到知识库的规范页面名（别名表）。",
     "params": {"query": {"flag": "--resolve", "type": "string", "desc": "待解析词"}}},
    {"name": "kb_where", "script": "kb_where.py", "jsonarg": False, "write": False,
     "desc": "「库内有没有 X」完备检索：跨四目录并逐目录报命中数（断言缺失前必用）。",
     "params": {"term": {"pos": True, "type": "string", "desc": "要找的串"}}},
    {"name": "kb_corpus_search", "script": "kb_corpus.py", "jsonarg": True, "write": False,
     "desc": "在 raw 全文块里检索，可回指文件:行号。",
     "params": {"query": {"flag": "--query", "type": "string", "desc": "查询"},
                "k": {"flag": "-k", "type": "string", "desc": "返回条数", "default": "8"}}},
    {"name": "kb_graph", "script": "kb_graph.py", "jsonarg": True, "write": False,
     "desc": "知识图谱：枢纽页、桥接页、两页间路径。",
     "params": {"path": {"flag": "--path", "type": "string", "desc": "两个页面名，空格分隔", "default": ""}}},
    {"name": "kb_backlinks", "script": "kb_backlinks.py", "jsonarg": False, "write": False,
     "desc": "孤立页/弱连接页分析 + 补链建议。",
     "params": {"suggest": {"flag": "--suggest", "type": "boolean", "desc": "给出补链建议"},
                "page": {"flag": "--page", "type": "string", "desc": "查某页的出入站", "default": ""}}},
    # —— 只读：元信息 ——
    {"name": "kb_stats", "script": "kb_stats.py", "jsonarg": True, "write": False,
     "desc": "知识库统计仪表板（页数/类型/标签/孤立页）。",
     "params": {}},
    {"name": "kb_tags", "script": "kb_tags.py", "jsonarg": True, "write": False,
     "desc": "标签词表审计（一次性标签占比等）。", "params": {}},
    {"name": "kb_dois", "script": "kb_dois.py", "jsonarg": True, "write": False,
     "desc": "库内已建卡 DOI 清单（去重键之一）。", "params": {}},
    {"name": "kb_cite", "script": "kb_cite.py", "jsonarg": False, "write": False,
     "desc": "从 source 页生成 GB/T 7714 引用串。",
     "params": {"page": {"flag": "--page", "type": "string", "desc": "如 sources/xxx.md"}}},
    {"name": "lit_batch", "script": "lit_batch.py", "jsonarg": True, "write": False,
     "desc": "文献提取/建卡的欠账台账状态。",
     "params": {"status": {"flag": "--status", "type": "boolean", "desc": "只看状态"}}},
    {"name": "lit_gapscan", "script": "lit_gapscan.py", "jsonarg": True, "write": False,
     "desc": "缺口扫描 → 下一轮检索式（带出处与信号）。",
     "params": {"queries": {"flag": "--queries", "type": "boolean", "desc": "输出检索式"}}},
    # —— 诊断 ——
    {"name": "kb_doctor", "script": "kb.py", "jsonarg": False, "write": False, "base": ["--doctor"],
     "desc": "环境与索引自检（索引是否可加载、是否新鲜）。", "params": {}},
    {"name": "kb_lint", "script": "kb_lint.py", "jsonarg": True, "write": False,
     "desc": "健康检查：--quick（最近 ingest）或 --deep（全库）。",
     "params": {"quick": {"flag": "--quick", "type": "boolean", "desc": "快速档"},
                "deep": {"flag": "--deep", "type": "boolean", "desc": "全库档"}}},
    {"name": "kb_selftest", "script": "kb_selftest.py", "jsonarg": False, "write": False,
     "desc": "底座不变量自检（frontmatter/换行/出链）。", "params": {}},
    {"name": "kb_toolcheck", "script": "kb_toolcheck.py", "jsonarg": False, "write": False,
     "desc": "实跑全部工具的 --selftest/--help，报编译/自检/写盘问题。", "params": {}},
    {"name": "lit_doctor", "script": "lit_doctor.py", "jsonarg": True, "write": False,
     "desc": "文献流水线体检（配置/去重对账/索引/任务）。", "params": {}},
    # —— 写（需 --allow-write）——
    {"name": "kb_build_index", "script": "kb_build_index.py", "jsonarg": False, "write": True,
     "desc": "重建/增量更新检索索引（幂等；写 wiki/.index/）。",
     "params": {"apply": {"meta": True, "type": "boolean", "desc": "确认执行（否则仅预览）"}}},
]
TOOL_BY_NAME = {t["name"]: t for t in TOOLS}


def resolve_vault(cli_vault=None):
    v = cli_vault or os.environ.get("MATSCI_KB_VAULT") or os.getcwd()
    v = os.path.abspath(v)
    if not os.path.isfile(os.path.join(v, "tools", "kb_lib.py")):
        raise SystemExit(f"[ABORT] 不是知识库（缺 tools/kb_lib.py）：{v}\n"
                         f"        用 --vault 指定库根，或设 MATSCI_KB_VAULT。")
    return v


def build_argv(vault, tool, args):
    """把 MCP 工具参数映射成 CLI argv。"""
    py = sys.executable
    script = os.path.join(vault, "tools", tool["script"])
    argv = [py, script] + tool.get("base", [])
    params = tool["params"]
    write_mode = bool(args.get("apply")) if tool.get("write") else False
    if tool.get("write") and "apply" not in args:
        write_mode = False
    for name, spec in params.items():
        if spec.get("meta"):                       # apply 等元参数，不进 CLI
            continue
        val = args.get(name, spec.get("default"))
        if spec.get("pos"):
            if val:
                argv.append(str(val))
            continue
        if spec.get("type") == "boolean":
            if val:
                argv.append(spec["flag"])
        else:
            if val not in (None, ""):
                argv.extend([spec["flag"], str(val)])
    if tool.get("jsonarg") and not write_mode:
        argv.append("--json")
    return argv, write_mode


def run_tool(vault, name, args, allow_write):
    tool = TOOL_BY_NAME.get(name)
    if not tool:
        return {"ok": False, "error": f"未知工具 {name}"}
    args = args or {}
    # 双钥门禁：写工具必须同时满足 ①server --allow-write ②调用方 apply=true。
    # 不能只靠 apply 参数——像 kb_build_index 默认就写盘，没有 apply 也会落盘。
    if tool.get("write"):
        if not allow_write:
            return {"ok": False, "error": "写操作被拒：server 未以 --allow-write 启动（双钥之一未满足）"}
        if not args.get("apply"):
            return {"ok": False, "error": "写操作被拒：需 apply=true 显式确认（双钥之二未满足）"}
    argv, _ = build_argv(vault, tool, args)
    r = subprocess.run(argv, cwd=vault, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=900,
                       env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    return {"ok": r.returncode == 0, "exit": r.returncode,
            "stdout": r.stdout, "stderr": r.stderr}


def input_schema(tool):
    props, required = {}, []
    for name, spec in tool["params"].items():
        if spec.get("meta"):
            props[name] = {"type": "boolean", "description": spec.get("desc", "")}
            continue
        t = spec.get("type", "string")
        props[name] = {"type": t, "description": spec.get("desc", "")}
        if spec.get("pos") and not spec.get("default"):
            required.append(name)
    return {"type": "object", "properties": props, "required": required}


def cmd_list_tools():
    for t in TOOLS:
        tag = "写" if t.get("write") else "读"
        print(f"  [{tag}] {t['name']:<18} {t['desc'][:60]}")
    print(f"\n共 {len(TOOLS)} 个工具")
    return 0


def cmd_selftest(vault, allow_write):
    ok = True
    print(f"库根: {vault}")
    for t in TOOLS:
        sp = os.path.join(vault, "tools", t["script"])
        ex = os.path.isfile(sp)
        print(f"  [{'ok' if ex else 'FAIL'}] {t['name']:<18} -> tools/{t['script']}")
        ok = ok and ex
    # 抽查一个只读工具真能跑
    r = run_tool(vault, "kb_stats", {}, allow_write=False)
    good = r["ok"]
    print(f"  [{'ok' if good else 'FAIL'}] kb_stats 实跑 exit={r['exit']}")
    ok = ok and good
    print(f"=== mcp server selftest {'PASS' if ok else 'FAIL'} ===")
    return 0 if ok else 1


def _make_tool_fn(vault, tool, allow_write):
    """为 v2 的 MCPServer.add_tool 造一个带**显式签名**的包装函数，
    使工具的参数与说明能正确暴露给客户端（schema 由签名推导）。"""
    from typing import Annotated

    def fn(**kwargs):
        res = run_tool(vault, tool["name"], kwargs or {}, allow_write)
        return json.dumps(res, ensure_ascii=False)

    ps = []
    for pname, spec in tool["params"].items():
        base = bool if spec.get("type") == "boolean" else str
        ann = Annotated[base, spec.get("desc", "")]
        # meta 参数（如 apply）也要可见，否则客户端传不进来、门禁形同虚设；
        # 但它不进 CLI（build_argv 会跳过 meta）。
        has_default = bool(spec.get("default")) or not spec.get("pos") or spec.get("meta")
        default = (spec.get("default") or "") if base is str else bool(spec.get("default"))
        default = default if has_default else _EMPTY
        ps.append(inspect.Parameter(pname, inspect.Parameter.KEYWORD_ONLY,
                                    default=default, annotation=ann))
    fn.__signature__ = inspect.Signature(ps)
    fn.__doc__ = tool["desc"]
    return fn


def serve(vault, allow_write):
    """以官方 MCP SDK（v2：MCPServer）启动 stdio server。"""
    try:
        from mcp.server import MCPServer
    except ImportError as e:
        print(f"[ABORT] 未安装官方 MCP SDK：{e}\n        运行： pip install -r {HERE}/requirements.txt")
        return 2

    app = MCPServer("matsci-kb")
    for t in TOOLS:
        fn = _make_tool_fn(vault, t, allow_write)
        kw = {"name": t["name"], "description": t["desc"]}
        try:
            app.add_tool(fn, **kw)
        except TypeError:                       # 老版本无 description 形参
            app.add_tool(fn, name=t["name"])
    app.run(transport="stdio")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", default=None)
    ap.add_argument("--allow-write", action="store_true", help="允许写工具（默认关）")
    ap.add_argument("--list-tools", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.list_tools:
        return cmd_list_tools()
    vault = resolve_vault(args.vault)
    if args.selftest:
        return cmd_selftest(vault, args.allow_write)
    return serve(vault, args.allow_write)


if __name__ == "__main__":
    sys.exit(main())
