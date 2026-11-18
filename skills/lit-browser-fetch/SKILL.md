---
name: lit-browser-fetch
description: "用真实 Edge + 类人鼠标兜底下载 lit-watch 自动取全文失败的研究论文正文与 SI。无人值守时自动点 Cloudflare/hCaptcha 复选框；图片验证码切交互模式人工过一次并复用会话。内置按域配额 / 冷却 / 熔断，避免把人机验证刷到 IP 被锁。触发词：浏览器兜底、自动下载失败、Cloudflare 过不去、人机验证、IP 被锁、补下载正文、补下载 SI、lit-browser-fetch。"
whenToUse: "当 lit_fetch 退出码 4 或部分失败、fetch_result 里有 failed/si_missing、手动下载清单里出现 Cloudflare/403/人机验证，且本机有机构订阅时使用。不要用于绕过付费墙，也不要在 OA 直链还能下时抢先用。"
trigger: /lit-browser-fetch
---

# lit-browser-fetch — 浏览器兜底下载（正文 + SI）

> **定位**：lit-watch 的 **B‴ 兜底阶段**。前面的 `lit_fetch` 拿不到真 PDF 时，
> 用本机真实 Edge、持久化专用 profile、类人鼠标轨迹去走出版社页面与验证码，
> 把正文和 SI 放进 `raw/pdf/Manual Download/` 与 `raw/pdf/si/`，再交给 `lit_manual_import` 收编。
>
> **工作目录一律是库根**：`cd "<你的库根>"`。
> 引擎：`tools/lit_browser_fetch.py`。本 skill 随插件发布在 `skills/lit-browser-fetch/`（技能真源）；
> 技能在插件级注册，`kb_init` 不复制 skills 进 vault；库内无 `.claude/skills/` 属正常。

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

# 0b) 域健康探针（仅打开首页 6 秒，判断当前 IP/profile 还能不能碰）
python tools/lit_browser_fetch.py --probe

# 1) 干跑：看会处理哪些 failed / si_missing（并打印本轮节奏策略）
python tools/lit_browser_fetch.py --latest

# 2) 无人值守：下载 + 自动收编（推荐）
python tools/lit_browser_fetch.py --latest --apply --import

# 3) 遇到图片验证码 / 域名被风控：人工过一次，之后同域复用
python tools/lit_browser_fetch.py --latest --apply --import --interactive

# 4) 单篇补跑（默认连 SI 一起）
python tools/lit_browser_fetch.py --doi 10.1021/jacs.6c00004 --apply --import

# 5) 只补正文，不动 SI
python tools/lit_browser_fetch.py --doi 10.1021/jacs.6c00004 --apply --no-si

# 6) 临时放宽/收紧本轮配额（不改配置）
python tools/lit_browser_fetch.py --latest --apply --daily-total 40
python tools/lit_browser_fetch.py --latest --apply --no-rate-policy   # 仅在确认 IP 干净时
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
| **4** | 有正文**真失败**（尝试过且失败），且一篇都没成功 | **不是“没有文献”**；看报告与 `state.json` |
| **2** | 参数/输入/浏览器启动/profile 错误 | 先修环境，不要重跑 |

> 🔴 **被节奏策略推迟 ≠ 失败**：若正文条目全部因配额/冷却没被尝试，退出码是 **0**
> （报告里是「⏳ 因节奏策略推迟」小节，不是失败表）。4 只在**确实尝试过且失败**时出现。
> 但**推迟的 SI 仍会让退出码保持 3**——文件确实还没到手，不能在收尾时谎称完整；
> 它与「需手动下载」的区别是：推迟项不进残余清单，下一轮自动继续。
>
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
python tools/lit_browser_fetch.py --login --login-url "https://www.sciencedirect.com/"
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

`state.json` 按**域名**记录每日用量、连续挑战数、挑战滑窗与冷却截止时间。
无人值守下的拦截**不再**是固定的“6 小时后整组跳过”，而由 `rate_policy` 决定：
第一次挑战退避 5 分钟、第二次 1 小时、第三次 3 小时，之后当日停；10 次滑窗里
出现 2 次挑战则立即冷却 24 小时；命中 403/1020 文本则锁 24 小时。
`needs_human` 仍会写进 `state.json`（供人工排查），但**不再单独驱动跳过逻辑**。
`--interactive` 完全不受此限。这不是省事，是防止把 IP 的 Cloudflare 风险分越推越高。

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

> 🔴 **先认清一件事**：2026-10-26 那轮 277 篇里出现 **64 次挑战**，而且分布极偏——
> 挑战/成功比 acs 0.11、wiley 0.17、science 0.29，而 Elsevier 8.0、IOP 10.0、AIP 从未成功；
> **约一半挑战集中在少数几个域上，换来的论文却是个位数**。
> 验证码不是“顺手点一下”，它是**刷高本机 IP 风险分的主要来源**；IP 被锁之后，
> 连原本能过的 Wiley/ACS 也会一起进 `Verifying…`。所以现在的默认策略是
> **“少而准”**：先走零验证通道，浏览器只用于确定有戏的域，且每域有硬配额。

### 两层节奏

**浏览器之前的零验证通道**（`lit_fetch`，不是本引擎，但决定本引擎要处理多少篇）：

1. **Europe PMC → PMC OA**：`isOpenAccess=Y && inEPMC=Y` 时直接取 PDF；
   正常时 PMC 的「Preparing to download」是 **SHA-256 前缀零工作量证明**，脚本 0.2 秒解完，
   **不是人机验证**。实测覆盖 70 篇失败 DOI 中的 10 篇（14%）。
   🔴 **但 IP 被标记后 PMC 会改发 reCAPTCHA 页**（2026-10-28 实测）。引擎识别到
   `recaptcha` 即**本轮停用该通道**——不要逐篇重试，那只会继续给 IP 加分。
   此外 Europe PMC 的检索是模糊的，返回记录的 DOI 必须与请求 DOI 相同，否则跳过
   （防止把别的论文存成本篇的名字）。
2. **OpenAlex `locations[]` 的仓库副本**：只取非出版社 host（arXiv / OSTI / HAL / 机构库）。
   🔴 不能只看 `best_oa_location`：抽查 12 篇的 best 直链 **12/12 都是出版社 `/pdf` 端点，
   纯 HTTP 一律 403**；而 `locations[]` 里另有可直接取的仓库副本。
3. Unpaywall（需要 `datasource.mailto` 填真实邮箱，否则跳过）→ 最后才是出版社直链。

**浏览器兜底内的速率治理**（`tools/lit_config.yaml` → `rate_policy:`）：

| 键 | 默认 | 语义 |
|---|---|---|
| `daily_total` | 25 | 全局每日**尝试**上限（主文 + SI 各计 1 次） |
| `per_domain_daily` | 每域不同 | 按 recipe 域名的每日尝试上限；**`0` = 无人值守永不碰** |
| `per_domain_unknown` | 3 | 配置里没列的域名的默认上限 |
| `min_interval_seconds` | 30 | 同域两次尝试的最小间隔 |
| `challenge_window` / `challenge_threshold` | 10 / 2 | 滑动窗口内挑战数达阈值 → 该域冷却 `cooldown_hours` |
| `cooldown_hours` | 24 | 挑战熔断后的冷却时长 |
| `backoff_seconds` | `[300, 3600, 10800]` | 连续失败退避阶梯（秒） |
| `resume_wait_seconds` | 600 | 若冷却剩余时间 ≤ 此值，**原地等完继续本域**，不整批推迟 |
| `hard_block_seconds` | 86400 | 命中 403 / `Error 1020` / `Access Denied` 文本 → 该域锁 24 小时 |

默认域分级（由 2026-10-26 实测挑战/成功率反推）：

| 级别 | 域 | 配额 | 理由 |
|---|---|---|---|
| 🟢 绿 | `acs` 15、`wiley` 8、`nature`/`springer`/`science` 各 6、`rsc`/`pnas`/`aps` 各 3、`generic` 4 | 正常尝试 | 实测成功率可接受 |
| 🔴 红 | `elsevier` / `iop` / `aip` **全部 0** | **无人值守永不碰** | 8–10 次挑战/成功或不成功；改走 `--interactive` 或手动清单 |
| ❓ 未知 | 任意新域 | 3 | 先观察，不默认信任 |

- 到配额 / 冷却中的条目不进失败，而是**标 `skipped` + `rate_policy:` 原因，写进报告的
  「⏳ 因节奏策略推迟（未尝试）」小节**。它们仍在原输入里，下次运行会继续处理。
- `--interactive` **完全绕过** `rate_policy`（人工在场时由人判断）；`--no-rate-policy`
  显式关闭（仅在你确认 IP 干净、想一次跑完时用）；`--daily-total N` 临时改全局上限。
- 启动时会打印 `[rate] …` 策略摘要，便于确认“这次到底按什么节奏跑”。

### 其余参数

| 参数 | 默认 | 说明 |
|---|---|---|
| `--limit` | 20 | 单轮最多处理篇数；`0` = 不限，只在域名稳定时用 |
| `--delay-min` / `--delay-max` | 4 / 9 秒 | 每篇之间的随机间隔（与 `min_interval_seconds` 叠加取大者） |
| `--human-timeout` | 300 秒 | 交互模式单次人工等待 |

🔴 **不要在 `Verifying…` 循环里反复点同一个位置。** Cloudflare 的 Turnstile 在判定自动化后
会自己循环；反复点击会提高风险分，甚至让同一 IP 上原本有效的 `cf_clearance` 失效。
本引擎最多点 2 次、间隔 4 秒，不通过就交回人工。

`--headless` 会显著降低过验证率，只建议在已确认无挑战的域名上调试用。

### 域健康探针 `--probe`

```bash
python tools/lit_browser_fetch.py --probe
```

只打开每个 recipe 的首页、等 6 秒、`detect_state()` 判一次，域间停 8–15 秒。
**不消耗配额、不下载、不改 `state.json`**。输出 `✓` / `✗` 与判定原因；
全绿 exit 0，任一挑战/被封 exit 3。**在跑大批次前先跑它**——如果连首页都挑战，
问题在 IP/profile，不在配方，这时跑多少篇都是白刷。

### IP 已被锁时的恢复顺序（L4）

已经出现「验证码越来越频繁 / 原本能过的域也开始挑战 / PMC 弹 reCAPTCHA」时：

1. **立即停手 24–72 小时**。继续跑任何域都只是在同一风险分上继续加分；
   停手期间改用 `lit_fetch` 的零验证通道（仓库副本）与手动下载清单。
2. 恢复前先 `--probe`：**全绿**才开跑；有 `✗` 就继续等，不要用真实批次去试。
3. 恢复后的第一批用**最小暴露**：`--limit 5 --only acs,wiley`（绿域、5 篇），
   观察报告里有没有挑战；无挑战再逐步加量，单日不超过 `daily_total`。
4. 红域（`elsevier`/`iop`/`aip`）只在 `--interactive` 下碰；不要为提高配额改配置。
5. 同域反复挑战且 `--probe` 也红：先 `--reset-profile --apply`（排除 profile 被标记），
   仍不行就是 IP 层面——换网络/等更久，**不要**用代理池轮换来绕。校园网是共享 IP，
   把出口打进黑名单会影响整栋楼，这属于越界操作。

---

## 各出版商现状（2026-10-26 实测基线）

| 出版商 | 正文方式 | SI 方式 | 状态 |
|---|---|---|---|
| Wiley (`10.1002`) | 文章页内 `fetch(pdfdirect)` | 隐藏的 `downloadSupplement` 链接 | ✅ 正文 2.4 MB / SI 1.36 MB |
| ACS (`10.1021`) | 文章页 + 浏览器 cookie + `curl_cffi`，或点 PDF 后 `href_fetch` | SI 专题页的文件链接 | ✅ 正文 8.7 MB / SI 950 KB |
| Elsevier (`10.1016`) | 点 “View PDF” → 新签名的 S3 页 → 页内 fetch | `lit_si` 直链（不过 Cloudflare） | ✅ 需有效 `cf_clearance`；9.4 MB｜🔴 默认配额 0 |
| Science / AAAS (`10.1126`) | 文章页内 fetch | 必须**真点击**下载链接（直接 fetch 403） | ✅ 正文 0.9 MB / SI 6.08 MB |
| Nature / Springer (`10.1038` / `10.1007`) | 文章页 / PDF 直链 | `lit_si` 自动通道 | ✅ 走 `lit_si` 为主 |
| RSC (`10.1039`) | 点 `articlepdf` 链接 | 同左 | ⚠️ 测试时 IP/profile 已被 Cloudflare 标记，未取得干净复现 |
| PNAS (`10.1073`) | 点 PDF 链接 | 同左 | ⚠️ 同上 |
| AIP (`10.1063`) | 点 PDF 链接 | 同左 | ⚠️ 同上｜🔴 默认配额 0（从未成功） |
| APS (`10.1103`) | `/abstract/` → `/pdf/` 直链兜底 | 同左 | ⚠️ 已加直链兜底与 `/pdf/` 选择器，未复测 |
| IOP / ECS (`10.1149` / `10.1088`) | Radware / hCaptcha 图片格 | 同左 | ⚠️ 无人值守不猜；必须 `--interactive`｜🔴 默认配额 0 |
| 其他 | 通用：找 PDF 链接 → 点击/抓取 | 同左 | 兜底 |

> “⚠️ 未复测”不是“不支持”。测试当天专用 profile/IP 已被前序 Cloudflare 尝试标记，
> 任何出版商都可能被挑战；干净 profile + `--interactive` 人工过一次后可再验证。
>
> 🔴 **本表只说明“配方能不能用”，不决定“默认要不要碰”**：能否无人值守由
> `rate_policy.per_domain_daily` 决定（`elsevier`/`iop`/`aip` 现为 **0**）。
> 配方可用 ≠ 值得为它刷验证码——Elsevier 实测 8 次挑战/成功，IOP 10 次，AIP 从未成功。
> 这三家应走 `--interactive` 或手动清单，不要靠调大配额“再试一次”。
>
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
7. 🆕 **会话复用（L2，2026-10-28）**：① SI 阶段用主文阶段记录的 `article_url_used`
   （DOI 重定向后的真实文章页）作为候选，少一次 `doi.org` 跳转与潜在挑战；
   ② SI 批次按域名**稳定分组**后再跑，同域 cookie 保持热、避免 A→B→A 来回切域。
   这两条不改变结果判定，只减少导航次数；不要为了“再快一点”把 SI 与正文合并到
   同一次导航里去猜链接（会引入正文/SI 混淆，见 ACS 的 `got_si_instead_of_main`）。
8. **下载成功后卡片不会自己变**：已建卡的论文新拿到 SI，卡上仍写着 `si_status: missing`，
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

- `--selftest` 覆盖（2026-10-28：**88 项**）：12 个 DOI 分流（含 AIP/APS）、
  APS `/abstract/`→`/pdf/` 直链猜测、SI 链接识别（ACS/Wiley）与正文链接反例、
  **SI 链接与页面上 `<a>` 的对照**（ACS 尾斜杠端点 → `si_href_key`/`si_href_matches`）、
  **"导航即下载"形态判定**（`nav_download_first`，ACS 目录型端点）、
  被 cancel 的 future 不抛未取回异常、PDF 魔数正/反例、文件名合法性、
  `fetch_result`/`picks`/手动清单解析、`kind: si` 与 `pdf_path`、
  已有 SI 文件识别（空文件不算）、本地目录 DOI→主文 PDF（SI 不冒充主文）、
  DOI 去重、报告 DOI 可点击、残余清单可点击、退出码（SI-only 仍缺=3 而非 4）、
  **节奏策略**（默认加载 / 配置覆盖 / 坏配置不污染 / 阈值钳制 / 配额 0 / 交互与
  `--no-rate-policy` 绕过 / 配额耗尽 / 跨日重置 / 全局上限 / 退避阶梯 / 成功后清零 /
  窗口熔断 24h / 硬封锁 24h / 同域最小间隔 / 报告推迟小节 正反例 / 全推迟=0 而非 4 /
  **SI 推迟不进残余清单但退出码仍为 3** 的正反例）。
- `python tools/lit_fetch.py --selftest` 覆盖零验证通道：`_solve_pow` 已知答案
  （SHA-256 d2 → 188）与 **SHA-1 解不满足 SHA-256 前缀**（真事故回归）、`max_nonce` 用尽 → None、
  `_parse_pow` 正/反例与 difficulty 缺省、**PMC 相对 href `pdf/x.pdf` 解析**（旧正则 `/pdf/`
  一条都匹配不到的真事故）、`is_repository_url` 仓库正例与出版社/图片反例、
  `candidate_urls` 仓库副本先于出版社直链 + 去重（打桩，不联网）、空 DOI 不触发查询。
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
5. **出版商的条款与频率限制仍然适用。** 默认 25 次尝试/日、4–9 秒间隔、同域 30 秒最小间隔、
   挑战熔断与硬封锁，都是为了不把机构 IP 打进黑名单。不要为了“一次下完”同时设
   `--limit 0 --no-rate-policy`——2026-10-26 的 64 次挑战就是这么来的。
   被锁定后**恢复期以天计**，而多下 10 篇的收益以分钟计，这笔账不划算。
6. **报告里的“成功”只代表真 PDF 已落盘**（`%PDF-` + 非 HTML）。它不代表论文已提取、
   已建卡、已入库——那是 C/D/E 阶段的事。

---

## 参考文件

- [`references/publishers.md`](references/publishers.md) —— 逐出版商 URL、捕获顺序、选择器、实测状态。
- [`references/troubleshooting.md`](references/troubleshooting.md) —— 症状 → 原因 → 动作排查树。
- 上游技能：[`../lit-watch/SKILL.md`](../lit-watch/SKILL.md)（B/B″/B‴/B′ 阶段与收编口径）。
- SI 判定：[`../../../tools/lit_si.py`](../../../tools/lit_si.py)、`python tools/lit_si.py --help`。
