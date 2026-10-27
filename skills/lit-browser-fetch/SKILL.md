---
name: lit-browser-fetch
description: "用真实 Edge + 类人鼠标兜底下载 lit-watch 自动取全文失败的研究论文正文与 SI。无人值守时自动点 Cloudflare/hCaptcha 复选框；图片验证码切交互模式人工过一次并复用会话。触发词：浏览器兜底、自动下载失败、Cloudflare 过不去、人机验证、补下载正文、补下载 SI、lit-browser-fetch。"
whenToUse: "当 lit_fetch 退出码 4 或部分失败、fetch_result 里有 failed/si_missing、手动下载清单里出现 Cloudflare/403/人机验证，且本机有机构订阅时使用。不要用于绕过付费墙，也不要在 OA 直链还能下时抢先用。"
trigger: /lit-browser-fetch
---

# lit-browser-fetch — 浏览器兜底下载（正文 + SI）

> **定位**：lit-watch 的 **B‴ 兜底阶段**。前面的 `lit_fetch` 拿不到真 PDF 时，
> 用本机真实 Edge、持久化专用 profile、类人鼠标轨迹去走出版社页面与验证码，
> 把正文和 SI 放进 `raw/pdf/Manual Download/` 与 `raw/pdf/si/`，再交给 `lit_manual_import` 收编。
>
> **工作目录一律是库根**：`cd "<你的库根>"`。
> 引擎：`tools/lit_browser_fetch.py`。技能真源：`.dsh/skills/lit-browser-fetch/`；
> `.claude/skills/lit-browser-fetch` 是指向它的 junction。

## 一句话边界

它**不是**验证码破解器，也**不绕过付费墙**：
- 类人鼠标是**浏览器内**的 CDP 鼠标事件（贝塞尔轨迹 + 抖动 + 随机停顿），
  **不会移动你桌面的真实光标**，因此不抢占鼠标；但它也不是 OS 级硬件输入。
- Cloudflare 一旦判定浏览器为自动化，会进入 `Verifying…` 循环；
  此时**继续点只会提高风险分**。正确做法是切 `--interactive` 人工过一次，
  或换一个已有人工验证记录的 profile。
- 机构订阅/IP 授权是前提。没有权限的论文会以 `paywalled` 失败，这是正确结果。
- 图片九宫格、Radware `Press & Hold` 在无人值守下不猜；无人值守直接记为需人工。

---

## 快速开始

```bash
# 0) 自检（不启动浏览器，秒级）
python tools/lit_browser_fetch.py --selftest

# 1) 干跑：看会处理哪些 failed / si_missing
python tools/lit_browser_fetch.py --latest

# 2) 无人值守：下载 + 自动收编（推荐）
python tools/lit_browser_fetch.py --latest --apply --import

# 3) 遇到图片验证码 / 域名被风控：人工过一次，之后同域复用
python tools/lit_browser_fetch.py --latest --apply --import --interactive

# 4) 单篇补跑（默认连 SI 一起）
python tools/lit_browser_fetch.py --doi 10.1021/jacs.6c04230 --apply --import

# 5) 只补正文，不动 SI
python tools/lit_browser_fetch.py --doi 10.1021/jacs.6c04230 --apply --no-si
```

`--latest` 会从新到旧找 `raw/notes/lit-watch/fetch_result-*.json` 里**第一份仍有
failed / si_missing** 的；也可以 `--in <picks.json | fetch_result.json | 手动下载清单.md>` 指定输入。

---

## 输入与产物

| 项 | 落点 |
|---|---|
| 主文 PDF | `raw/pdf/Manual Download/`（默认收件箱；`--outdir` 可改） |
| SI | `raw/pdf/si/<主文 stem>.si.<pdf\|docx\|xlsx>` |
| 报告 | `raw/notes/lit-watch/downloads/browser-fetch-<时间戳>.md` |
| 机器可读结果 | 同目录 `browser-fetch-<时间戳>.json` |
| 残余手动清单 | 同目录 `browser-fetch-<时间戳>-residual.md` |
| 域名健康状态 | `_scratch/lit-browser-fetch/state.json` |
| 专用浏览器 profile | `_scratch/lit-browser-fetch/profile/`（`.gitignore` 已忽略） |
| 操作日志 | `wiki/log_ops.md`（`--no-log` 可关，仅测试用） |

报告里的每一条 DOI 都是可点击链接；残余清单复用 `lit_fetch.write_manifest`，
**每一条都必须带 `](http` 链接**，只有标题不算完成。

---

## 退出码

| 码 | 含义 | 上层怎么读 |
|---|---|---|
| **0** | 全部正文成功，且没有仍缺的 SI | 可以进 C 提取 |
| **3** | 部分成功，或正文全成但有 SI 仍缺 | 继续流水线；残余清单要人看 |
| **4** | 一篇正文都没成功 | **不是“没有文献”**；看报告与 `state.json` |
| **2** | 参数/输入/浏览器启动/profile 错误 | 先修环境，不要重跑 |

> 注意：`0` 只代表“本轮输入里的条目都拿到了，且 SI 不缺”。
> 它不代表整个 lit-watch 批次完成——后面还有 C/D/E/F。

---

## 在 lit-watch 里的位置

执行顺序：

```text
B 取全文（lit_fetch，含 B″ SI）
  ↓ 有 failed 或 si_missing
B‴ 浏览器兜底（本技能）
  ↓ 产出进 Manual Download + raw/pdf/si
B′ 收编（lit_manual_import --apply；--import 会自动跑）
  ↓
C 提取 → D 建卡 → E 收尾 → F 缺口
```

推荐把 B‴ 写成 B 之后的条件分支，而不是每轮都跑。`lit_fetch` 的退出码
0 只表示“至少一篇成功”，**不表示没有失败**；所以不要只看退出码，要看
`fetch_result` 里的 `failed` / `si_missing`：

```bash
python tools/lit_fetch.py --in <picks> --outdir raw/pdf

# 干跑：--latest 会自动找最新仍有 failed/si_missing 的 fetch_result
python tools/lit_browser_fetch.py --latest
# 只有上面计划里确实有待处理项，再加 --apply
python tools/lit_browser_fetch.py --latest --apply --import
```

`--import` 会调用 `lit_manual_import.py --apply`，**只对默认收件箱安全**；
测试时改了 `--outdir` 就**不要**加 `--import`，否则会把测试 PDF 收编进库。

---

## 浏览器与 profile 生命周期

默认使用**专用 Edge profile**：`_scratch/lit-browser-fetch/profile/`。
它和你的日常 Edge 完全隔离；**不要**把 `--profile` 指向日常 profile。

同一时刻只允许一个进程驱动它（OS 级 `profile.lock`，退出自动释放）。
第二个实例会打印占用者并以 exit 2 退出——这是保护，不是故障：
两个实例会互相把对方的 Edge 当“残留”清掉，双方都表现为随机 `page_closed`。

首次使用 / 校外访问：

```bash
# 打开可见浏览器，完成 CARSI / 机构登录，回车保存会话
python tools/lit_browser_fetch.py --login
python tools/lit_browser_fetch.py --login --login-url "http<库外路径>"
```

如果另一个 profile 已经有人工验证过的 `cf_clearance`，可以一次性导入（只导出版商相关 cookie，
不导书签/历史/密码）：

```bash
python tools/lit_browser_fetch.py --seed-from "_scratch/skill-probe/profile" --apply
```

profile 被风控标记、页面持续 `Verifying…`、或 cookie 坏了：

```bash
# 先干跑看会备份到哪
python tools/lit_browser_fetch.py --reset-profile
# 真备份并清空 state（profile 目录改名为 .bak-<时间戳>）
python tools/lit_browser_fetch.py --reset-profile --apply

# 或者本次临时用一个全新 profile（排查“是 profile 还是 IP”）
python tools/lit_browser_fetch.py --latest --apply --fresh-profile --interactive
```

`state.json` 按**域名**记录连续风控失败。无人值守下某域连续 2 次挑战失败，
该域会被标记 `needs_human`，**6 小时内整组跳过**；`--interactive` 不受此限。
这不是省事，是防止把 IP 的 Cloudflare 风险分越推越高。

**启动/重启自愈**：`BrowserSession.launch()` 先做**导航探针**（`goto about:blank` 后页面必须仍活着）——
单例锁下 `launch_persistent_context` 会「成功」返回，但新 Edge 立刻把标签页交给旧实例后退出，
只 `new_page()` 探测不到。失败时只强杀命令行含**本专用 profile 路径**的 `msedge.exe`
（`taskkill /T /F` 连子进程），轮询到**连续两次**归零、移除残留 `lockfile`，
再按 2s / 8s / 15s 退避重试 **3 次**。`ensure_ready()` 在每个域名组与 SI 阶段前用同样探针探活。

两条容易漏的底层事实（2026-10-26 实测）：

1. **`ctx.close()` 不会关掉 Edge**——关完后仍有约 10 个 `msedge.exe` 占着 profile。
   无人值守时 `close()` 会自动收干净；否则**下一轮开局必撞单例锁**。
2. **Edge 关掉最后一个窗口就整个退出**。组循环/探针每次 `page.close()` 都可能恰好
   关掉最后一页，上下文随后无声死掉。引擎因此常驻一个 `about:blank` 的 keepalive 页，
   任何时刻都不会出现「零窗口」。

`--interactive` 不自动杀进程（用户可能正在同一 profile 登录）。
`page_closed` 只算浏览器生命周期问题，**不会**把域名标 `needs_human`。

🔴 **同一 profile 同时只能有一个进程**。两个实例各自「清理残留 Edge」时会杀掉对方的浏览器，
表现为交替的 `TargetClosedError` / `page_closed`，看起来像 Edge 不稳定、实际是互相踩。
引擎用 OS 级 `profile.lock` 互斥（进程退出自动释放）；确需并行请给不同 `--profile` 并加 `--no-lock`。

---

## 节奏与风控（默认“稳妥”）

| 参数 | 默认 | 说明 |
|---|---|---|
| `--limit` | 20 | 单轮最多处理篇数；`0` = 不限，只在域名稳定时用 |
| `--delay-min` / `--delay-max` | 4 / 9 秒 | 每篇之间的随机间隔 |
| 同域连续挑战失败 | 2 次 | 停止该域并写 `needs_human` |
| `needs_human` TTL | 6 小时 | 无人值守跳过；交互模式可立即重试 |
| `--human-timeout` | 300 秒 | 交互模式单次人工等待 |

🔴 **不要在 `Verifying…` 循环里反复点同一个位置。** Cloudflare 的 Turnstile 在判定自动化后
会自己循环；反复点击会提高风险分，甚至让同一 IP 上原本有效的 `cf_clearance` 失效。
本引擎最多点 2 次、间隔 4 秒，不通过就交回人工。

`--headless` 会显著降低过验证率，只建议在已确认无挑战的域名上调试用。

---

## 各出版商现状（2026-10-26 实测基线）

| 出版商 | 正文方式 | SI 方式 | 状态 |
|---|---|---|---|
| Wiley (`10.1002`) | 文章页内 `fetch(pdfdirect)` | 隐藏的 `downloadSupplement` 链接 | ✅ 正文 2.4 MB / SI 1.36 MB |
| ACS (`10.1021`) | 文章页 + 浏览器 cookie + `curl_cffi`，或点 PDF 后 `href_fetch` | SI 专题页的文件链接 | ✅ 正文 8.7 MB / SI 950 KB |
| Elsevier (`10.1016`) | 点 “View PDF” → 新签名的 S3 页 → 页内 fetch | `lit_si` 直链（不过 Cloudflare） | ✅ 需有效 `cf_clearance`；9.4 MB |
| Science / AAAS (`10.1126`) | 文章页内 fetch | 必须**真点击**下载链接（直接 fetch 403） | ✅ 正文 0.9 MB / SI 6.08 MB |
| Nature / Springer (`10.1038` / `10.1007`) | 文章页 / PDF 直链 | `lit_si` 自动通道 | ✅ 走 `lit_si` 为主 |
| RSC (`10.1039`) | 点 `articlepdf` 链接 | 同左 | ⚠️ 测试时 IP/profile 已被 Cloudflare 标记，未取得干净复现 |
| PNAS (`10.1073`) | 点 PDF 链接 | 同左 | ⚠️ 同上 |
| AIP (`10.1063`) | 点 PDF 链接 | 同左 | ⚠️ 同上 |
| APS (`10.1103`) | `/abstract/` → `/pdf/` 直链兜底 | 同左 | ⚠️ 已加直链兜底与 `/pdf/` 选择器，未复测 |
| IOP / ECS (`10.1149` / `10.1088`) | Radware / hCaptcha 图片格 | 同左 | ⚠️ 无人值守不猜；必须 `--interactive` |
| 其他 | 通用：找 PDF 链接 → 点击/抓取 | 同左 | 兜底 |

> “⚠️ 未复测”不是“不支持”。测试当天专用 profile/IP 已被前序 Cloudflare 尝试标记，
> 任何出版商都可能被挑战；干净 profile + `--interactive` 人工过一次后可再验证。
> 逐出版商的 URL、捕获顺序与坑见 [`references/publishers.md`](references/publishers.md)。

---

## SI 流程（默认开启）

1. **先查已有文件**：`existing_si_files(si_dir, stem)` 命中 `<stem>.si.pdf` / `.si2.pdf` /
   `.si.docx` 即返回 `present`（原因“已存在”），**不启动浏览器**。这条同时防止
   “浏览器死了 → 已在库的 SI 被误报 missing”。
2. 主文成功后，先用 `lit_si.scan_pdf` 判**有没有 SI**（判据只认原文，不认 Crossref `relation`
   或 Europe PMC `hasSuppl`）。
3. 有 SI → 先试 `lit_si.fetch(si_dir=..., apply=True)`（Nature/Springer/Elsevier 直链）。
4. 直链失败 → 浏览器：先试 SI 专题页，再回文章页；找到 SI 链接后，
   **能 fetch 就 fetch，403 就真点击**（Science 的 SI 端点只认点击）。
5. 写入 `raw/pdf/si/<主文 stem>.si.<ext>`；多份用 `.si2.<ext>`。
6. 仍取不到 → `si_status: missing`，写进残余清单的 **📎 SI 待手动下载** 小节，带 DOI、
   SI 专题页、Wiley 文件级直链。**没有实体文件就不准把卡改成 `present`。**
7. 🆕 **下载成功后卡片不会自己变**：已建卡的论文新拿到 SI，卡上仍写着 `si_status: missing`，
   与实际文件矛盾（2026-10-26 实测一批 18 张）。收尾跑一次：
   ```bash
   python tools/qc_si_backfill.py --recheck          # 干跑，只看不动
   python tools/qc_si_backfill.py --recheck --apply  # 只允许升级到 present
   ```
   复判的判据与建卡同源（独立 SI 文件优先），且**只准升级**——复判成 `not_applicable`/`missing`
   一律不写，避免用“这一遍没看见”覆盖上一遍的判断。

**SI-only 输入**：`--in <picks.json>` 里的条目写 `"kind": "si"` 即可。`pdf_path` 可省略——
引擎先按规范文件名找主文，再查本地目录 `local_lit_catalogue.json` 的 DOI→PDF；
库外主文（如任务目录）请显式给 `pdf_path`。本地目录已排除 `.si.` 与 `si/`，
SI 不会被当成“这篇论文我已有了”。

`--no-si` 只用于调试或“本轮只补正文”；正常批次不要关。

---

## 报告、残余清单与日志

- `browser-fetch-<ts>.md`：成功表（标题/DOI/出版商/文件名/方式）、失败表（原因 + 最近 6 条尝试）、
  SI 仍缺列表。
- `browser-fetch-<ts>.json`：每条 `Item` 的完整字段，便于后续脚本读取。
- `browser-fetch-<ts>-residual.md`：**只列真正需要人手的条目**。人只需要打开这个文件；
  里面每一条都应带可点击链接。
- `wiki/log_ops.md`：追加一行 `## [日期] lit-browser-fetch | 输入 …：正文成功 N/M，SI 仍缺 K，残余清单 …`。
  测试时用 `--no-log`，不要污染日志。

---

## 故障排查（先看这张表）

| 症状 | 最可能原因 | 动作 |
|---|---|---|
| 页面标题 `Just a moment...` / `请稍候…` | Cloudflare 挑战 | 先 `--interactive` 人工过一次；不要连点 |
| `Verifying…` 一直循环 | 浏览器已被判定自动化 / IP 风险高 | 停止该域；`--reset-profile --apply` 或换 profile；必要时换网络 |
| `captcha_requires_human` | 图片格 / hCaptcha / Turnstile 不自动过 | `--interactive`，人工完成后脚本继续 |
| `challenge_timeout` | 35 秒内没等到页面恢复 | 看是否 `needs_human`；交互模式重试 |
| `paywalled` | 无机构订阅 / 未登录 | `--login` 做 CARSI；确认 IP 授权 |
| `未能定位真 PDF` + `no_pdf_link_on_article` | 页面没有可见 PDF 链接，或链接在 JS 里 | 交互模式打开文章页看；APS 已加 `/pdf/` 兜底 |
| 下载到的是 HTML | 被重定向到登录/挑战页 | 看 `attempts`；不是 PDF 就不会落盘 |
| `profile 正被 Edge 占用` | 上次浏览器没退干净 | 无人值守会自动清理本专用 profile 的残留 Edge；交互模式需手动关 |
| `TargetClosedError` / 中途“浏览器不可用” | 旧 Edge 未退净，profile 单例锁 | 已自动强杀本 profile 进程并重试；仍失败看 troubleshooting §6 |
| `got_si_instead_of_main` | 链接是 SI，或主文被 `looks_like_si` 误杀 | 看 `file=`/`href=`；主文误杀已于 2026-10-26 修复，复跑即可 |
| `--import` 后文件不见了 | 被 `lit_manual_import` 移进 `raw/pdf/` | 这是正常收编；台账 `state/manual_import_log.json` |
| SI 一直 `missing` | SI 端点 403 / 只认点击 / 需订阅 | 看残余清单；必要时手动下到 `raw/pdf/si/<stem>.si.<ext>` |
| SI 已在库却仍被处理 | 旧版本不查已有文件 | 现在先查 `<stem>.si.*` 并直接记 `present`（“已存在”） |

更细的排查树见 [`references/troubleshooting.md`](references/troubleshooting.md)。

---

## 自检与维护

改了这个引擎或任何 recipe 之后，**至少跑**：

```bash
python -m py_compile tools/lit_browser_fetch.py
python tools/lit_browser_fetch.py --selftest
python tools/kb_toolcheck.py
```

- `--selftest` 覆盖（2026-10-26：**56 项**）：12 个 DOI 分流（含 AIP/APS）、
  APS `/abstract/`→`/pdf/` 直链猜测、SI 链接识别（ACS/Wiley）与正文链接反例、
  **SI 链接与页面上 `<a>` 的对照**（ACS 尾斜杠端点 → `si_href_key`/`si_href_matches`）、
  **"导航即下载"形态判定**（`nav_download_first`，ACS 目录型端点）、
  被 cancel 的 future 不抛未取回异常、PDF 魔数正/反例、文件名合法性、
  `fetch_result`/`picks`/手动清单解析、`kind: si` 与 `pdf_path`、
  已有 SI 文件识别（空文件不算）、本地目录 DOI→主文 PDF（SI 不冒充主文）、
  DOI 去重、报告 DOI 可点击、残余清单可点击、退出码（SI-only 仍缺=3 而非 4）。
- 改 `lit_manual_import.looks_like_si` 后必跑 `python tools/lit_manual_import.py --selftest`
  （含 2026-10-26 回归夹具：Abstract 在首页 600 字外的主文不得判 SI）。
- 新增/修改出版商 recipe 时，**同时加分流夹具**；只测“该过的过了”会漏“该报的没报”。
- 任何写盘路径都必须走原子写；写后复算。不要绕开 `save_pdf` 的 `%PDF-` 校验。
- 引擎会自动追加 `wiki/log_ops.md`；手工补跑后不要重复写同一条。

---

## 诚实边界（必须让用户知道）

1. **不是所有验证码都能无人值守过。** 图片九宫格、Radware `Press & Hold`、
   被标记 IP 的 Turnstile，都需要人工或换网络。无人值守失败会如实进残余清单，不假装成功。
2. **不是所有出版商都已复测。** 2026-10-26 的干净成功链是 Wiley / ACS / Elsevier（需有效
   `cf_clearance`）/ Science；RSC / PNAS / AIP / APS 因测试 profile 被 Cloudflare 标记而未取得
   干净复现；IOP 必须交互。不要把“未复测”写成“已支持”。
3. **不绕过付费墙。** 没有机构订阅就是 `paywalled`；这时应走馆际互借/作者索取，而不是换脚本。
4. **profile 含登录 cookie。** `_scratch/` 不提交 git；不要把 profile 目录发给别人。
5. **出版商的条款与频率限制仍然适用。** 默认 20 篇/轮、4–9 秒间隔、同域 2 次失败即停，
   是为了不把机构 IP 打进黑名单。不要为了“一次下完”把 `--limit` 设 0 并关掉间隔。
6. **报告里的“成功”只代表真 PDF 已落盘**（`%PDF-` + 非 HTML）。它不代表论文已提取、
   已建卡、已入库——那是 C/D/E 阶段的事。

---

## 参考文件

- [`references/publishers.md`](references/publishers.md) —— 逐出版商 URL、捕获顺序、选择器、实测状态。
- [`references/troubleshooting.md`](references/troubleshooting.md) —— 症状 → 原因 → 动作排查树。
- 上游技能：[`../lit-watch/SKILL.md`](../lit-watch/SKILL.md)（B/B″/B‴/B′ 阶段与收编口径）。
- SI 判定：[`../../../tools/lit_si.py`](../../../tools/lit_si.py)、`python tools/lit_si.py --help`。
