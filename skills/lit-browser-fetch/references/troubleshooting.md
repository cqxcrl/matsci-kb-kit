# 故障排查（lit-browser-fetch）

> 先记住三条：
> 1. **失败不是“没有文献”**——看 `browser-fetch-*.json` 里的 `reason` 与 `attempts`。
> 2. **`Verifying…` 循环不要连点**——越点风险分越高。
> 3. **没有真 PDF 落盘就不算成功**——HTML/登录页不会通过 `%PDF-` 校验。

---

## 0. 先做三件事（30 秒）

```bash
# ① 干跑：确认输入和待处理项
python tools/lit_browser_fetch.py --latest

# ② 看最近一次报告与 JSON
ls -t raw/notes/lit-watch/downloads/browser-fetch-* | head
# 报告里看“正文失败”的原因列；JSON 里看 attempts

# ③ 看域名健康状态
python - <<'PY'
import json
p = "_scratch/lit-browser-fetch/state.json"
try:
    d = json.load(open(p, encoding="utf-8"))
    for k, v in d.get("domains", {}).items():
        print(k, v)
except FileNotFoundError:
    print("state.json 不存在（还没跑过浏览器阶段）")
PY
```

若 `state.json` 里某域 `needs_human: true` 且 `at` 在 6 小时内，无人值守会整组跳过。
这是设计行为，不是 bug。要立刻重试就加 `--interactive`，或删掉该域记录（谨慎）。

---

## 1. Cloudflare / Turnstile

### 症状 A：标题 `Just a moment...` / `请稍候…`，正文很短

**原因**：Cloudflare 挑战页。可能是 IP 风险高、浏览器被判定自动化、或该域要求人工。

**动作（按顺序）**：
1. 不要连续重跑。先 `--interactive`，在可见浏览器里人工点一次。
2. 人工通过后，脚本会复用同一个 profile/会话；同一域后续条目通常不再挑战。
3. 若人工也过不去，换网络（手机热点/校园网/VPN）再试；可能是 IP 被标记。
4. 仍不行 → 该域进残余清单，手动下载。**不要**为了过验证去装“破解插件”。

### 症状 B：`Verifying…` 一直转圈

**原因**：Turnstile 已把浏览器判为自动化，正在自己循环；或风险分太高。

**动作**：
1. **立即停止该域**（引擎最多点 2 次就会返回 `captcha_requires_human`）。
2. `--reset-profile --apply` 备份并清空 profile；或 `--fresh-profile` 用全新 profile。
3. 用 `--interactive` 人工过一次，建立新的 `cf_clearance`。
4. 若同一 IP 上原本能过的站点也开始挑战，说明 IP 风险分被抬高；等一段时间或换网络。
5. **不要**反复 `--apply` 刷同一域；这会让情况更糟。

### 症状 C：`challenge_timeout`

**原因**：35 秒内页面没有恢复，也没识别出具体挑战类型。

**动作**：
- 看 `state.json` 是否已把该域标 `needs_human`；
- `--interactive --human-timeout 300` 重试；
- 若页面其实已经加载完（例如 PDF 在 iframe 里），看 `attempts` 是否有
  `page_fetch_error` / `no_pdf_link_on_article`，按下面第 4 节处理。

### 症状 D：`captcha_requires_human`

**原因**：图片格、hCaptcha、或 Turnstile 自动点击失败。

**动作**：
- `--interactive`；
- 人工完成后不要关浏览器，脚本会继续；
- 若经常出现，考虑 `--seed-from` 一个已人工验证的 profile。

---

## 2. 图片验证码 / Radware

### hCaptcha 九宫格

- 引擎检测到 “select all / click each / tiles / 选择 / 点击每个” 会判 `image_grid`，
  无人值守直接返回 `captcha_requires_human`，**不会瞎点**。
- 正确做法：`--interactive`，人工选图。
- IOP 常见；一次人工后同域会话可复用，但不保证永久。

### Radware `Press & Hold`

- `press_and_hold()` 会找 `#px-captcha` / 含 “Press & Hold” 的元素，按住 6–9 秒。
- 若按住后仍要求图片格，转 `--interactive`。
- 不要用脚本模拟“按住 60 秒”；Radware 会检测轨迹/时序。

---

## 3. 付费墙 / 机构授权

### 症状：`paywalled（付费墙/无机构授权）`

**原因**：
- 当前 IP 不在机构授权范围；
- 未登录/CARSI 会话过期；
- 该刊不在订阅包内；
- 出版社把 PDF 链接对非订阅者隐藏。

**动作**：
1. `python tools/lit_browser_fetch.py --login`，完成 CARSI/机构登录；
2. 确认浏览器里能手动打开该文 PDF；
3. 若手动也打不开，就是没有权限——走馆际互借/作者索取，不要继续试脚本；
4. 校外访问请先连学校 VPN，再 `--login`。

### 症状：文章页能开，但 `no_pdf_link_on_article`

**原因**：PDF 链接被订阅墙隐藏、在 JS 里、或在折叠菜单里。

**动作**：
- `--interactive` 打开文章页，人工找 PDF 按钮；
- 若人工能看到，记下链接形态，补 `find_pdf_link()` 选择器；
- APS 已加 `/abstract/` → `/pdf/` 兜底；其他站点可类似加 recipe；
- 若人工也看不到，就是无权限。

---

## 4. 找不到 PDF / 下载到的不是 PDF

### 症状：`未能定位真 PDF`，`attempts` 里有 `no_pdf_link_on_article`

按顺序检查：

1. 文章页 URL 是否正确？`--doi` 是否带前缀（`10.xxxx/...`）？
2. 页面是否需要先点 “View PDF”/“PDF” 按钮才出现链接？
3. 链接是否在 iframe/shadow DOM 里？`query_selector_all` 看不到 shadow DOM；
   需要 `page.locator(...).evaluate` 或先点开。
4. 是否是 APS 这类 `/abstract/` → `/pdf/` 规律？引擎已兜底。
5. 是否被重定向到登录页？看 `page.url` 与 `detect_state().paywall`。

### 症状：下载到 HTML，`looks_pdf()` 失败

**原因**：链接返回的是登录页、挑战页、或 “PDF not available” 页面。

**动作**：
- 看 `attempts` 里的 `content-type`/`page_fetch_error`；
- 不要绕过校验把 HTML 改名成 `.pdf`；
- 用 `--interactive` 手动点一次，确认真实下载 URL；
- 若真实 URL 是签名 S3/临时链接，让引擎走“点击 → 新页 → fetch”，不要硬编码。

### 症状：点击后没有 `download` 事件，也没有 popup

**原因**：
- 链接是 `javascript:` 打开新窗口，被浏览器拦截；
- 下载被 Edge 的“每次询问保存位置”拦住；
- 链接其实是在新标签打开 PDF 阅读器。

**动作**：
- 引擎监听 `popup` + `download` 23 秒；超时后会对 href 做 fetch/curl 兜底；
- `--interactive` 看实际行为；
- 若是 Edge 下载设置问题，在专用 profile 里允许自动下载（不要改日常 profile）。

---

## 5. SI 相关

### 症状：正文成功，SI 一直 `missing`

按顺序：

1. `python tools/lit_si.py scan "<PDF>"` —— 确认原文到底有没有 SI；
   `unknown` 不等于“没有”，要看扫描页数/文字层。
2. `python tools/lit_si.py fetch "<PDF>" --apply --year <年份>` —— 试自动直链；
3. 浏览器阶段会先试 SI 专题页，再回文章页；
4. Science 的 SI 必须真点击；Wiley 的链接可能不可见；
5. 仍失败 → 残余清单的 **📎 SI 待手动下载** 小节，手动下到
   `raw/pdf/si/<主文 stem>.si.<pdf|docx|xlsx>`。

### 症状：SI 下载成了正文 / 撞名

- `lit_manual_import.looks_like_si()` 会按文件名和内容判 SI；
- SI 落点必须是 `<主文 stem>.si.<ext>`，不要用与主文相同的名字；
- 手动收编时若撞名，`lit_manual_import` 会跳过并报告，不会覆盖主文。

### 症状：`got_si_instead_of_main`

**先看括号里的 `file=` / `href=`**：

- `file='..._si.pdf'` 或 `href` 含 `suppl` / `article-supplement` / `_si_`：确实是 SI，
  正文链接没找到；看同目录报告的 `attempts`，用 `--interactive` 打开文章页确认正文入口。
- `file='ja9b00911.pdf'`（没有 `_si`）且 PDF 是 9 页左右、十几 MB：**可能是主文被内容闸门误杀**。
  2026-10-26 实测 jacs.9b00911：ACS 主文首页作者/单位栏很长，`ABSTRACT:` 落在旧版
  `page1[:600]` 窗口之外，`looks_like_si()` 把它误判成 SI。修复后「SI 抬头」只看页首 600 字，
  **`ABSTRACT` 扫整页**；同一 PDF 复判为正文。
- 复跑前先确认 `lit_manual_import.py --selftest` 通过；不要为了过闸门把 SI 硬改名为正文。

### 症状：SI 明明在 `raw/pdf/si/`，每轮还被重新处理 / 报 `missing`

2026-10-26 起 `download_si()` 会先查 `existing_si_files(si_dir, stem)`：
`<stem>.si.pdf` / `.si2.pdf` / `.si.docx` 任一非空文件即返回 `present`（原因“已存在”），
**不启动浏览器**。若仍被重试，检查主文 stem 是否与 SI 文件名一致（收编改名会换 stem）。

### 症状：SI-only 输入（`kind: si`）报“未找到主文 PDF”

`--in` 的 SI 项可以只给 DOI；引擎会先 `find_existing_pdf()`（按规范文件名），
再查 `state/local_lit_catalogue.json` 的 DOI→`local_files`。若主文在库外（例如
`<你的 .claude>\tasks\...`），在输入 JSON 里显式写 `pdf_path`，或先把主文收编进 `raw/pdf/`。
本地目录重建后不应含 SI 条目（`lit_catalogue.py` 已排除 `.si.` 与 `si/` 目录）。

### 症状：`si_status: present` 但 `raw/pdf/si/` 没有文件

这是**假 present**，必须修：
- `present` 的定义是“库内确有实体 SI 文件”；
- 没有文件就改回 `missing` 或 `partial`，并进清单；
- 不要用 `si_note` 里的文件名冒充文件存在。

---

## 6. Profile / 浏览器

### 症状：`源 profile 正被 Edge 占用（有 SingletonLock）`

**原因**：上次 Edge 没退干净，或日常 Edge 正在用同一个 profile。

**动作**：
1. 关闭所有使用该 profile 的 Edge 窗口；
2. 检查残留进程（PowerShell）：
   ```powershell
   Get-CimInstance Win32_Process -Filter "Name='msedge.exe'" |
     Select-Object ProcessId, CommandLine
   ```
   只杀带 `--user-data-dir=...lit-browser-fetch...` 的进程，**不要**杀日常 Edge。
3. 仍不行：`--reset-profile --apply`（会备份旧 profile）。

### 症状：`TargetClosedError` / 浏览器在批次中途死亡

**现象**：报告里出现 `page_closed`、`浏览器不可用（上下文已关闭且重启失败）`，后续整组失败，
日志里新 Edge 打印“在现有浏览器会话中打开”后立刻退出。

**原因**：上一段 `ctx.close()` 没把 Edge 进程收干净，profile 仍被单例锁占用；
Playwright 新实例连到一个已死的 context。以前这会连报告都不写。

**现在的自动恢复**（无人值守）：
1. `BrowserSession.launch()` 先用**导航探针**判断实例是否真活着（`new_page` 成功不等于活着：
   单例锁下新 Edge 会「在现有浏览器会话中打开」后立刻退出）。启动失败时只强杀
   **命令行含本专用 profile 路径**的 `msedge.exe`（`taskkill /T /F`，连 GPU/utility/crashpad
   子进程一起收），轮询到**连续两次**为 0、移除残留 `lockfile`，再按 2s / 8s / 15s 退避
   重试 **3 次**（窗口太短会被残留的“会话”再挡一次）；
2. `ensure_ready()` 在每个域名组和 SI 阶段前用同样的导航探针探活，上下文死了就走同一套恢复；
   `close()` 在无人值守时自动清理关闭后仍活着的 Edge（实测 `ctx.close()` 后残留 ~10 个进程，
   留给下一轮就是开局撞锁）；
   `start()` 常驻一个 `about:blank` keepalive 页——**Edge 关掉最后一个窗口会整个退出**，
   组循环关页面时很容易把它带走；
3. 报告与残余清单在 `finally` 里写，浏览器死了也保留证据。

**仍然失败时**：
- `--interactive` 模式**不会**自动杀进程（用户可能正在同一 profile 登录）；
- 手动清理：`powershell -NoProfile -ExecutionPolicy Bypass -File _scratch/litbf-edge-procs.ps1 kill`
  （只杀带 `lit-browser-fetch` 的 Edge），再删 `_scratch/lit-browser-fetch/profile/lockfile`；
- 若频繁死亡，检查磁盘/内存与 Edge 版本；必要时 `--reset-profile --apply`。

> `page_closed` 是浏览器生命周期问题，**不再**计入域名风控失败数（不会把域名误标 `needs_human` 6 小时）。

### 症状：SI 阶段第一篇成功，后面全报 `page_closed`

**现象**（2026-10-26 实测）：9 篇 SI，只有第 1 篇 `present`，其余 8 篇
`si_entry <SI 页>` 与 `si_entry <文章页>` 两条都记 `page_closed`，最终都被写成
`missing（文章页/SI 页未找到 SI 链接）`。

**原因**：SI 阶段复用同一个 page；某个站点脚本把承载页关掉后，page 变成死对象，
后续每次 `goto` 都立刻抛 `page_closed`。上下文其实还活着，但循环从不重建页面。

**现行恢复**：SI 循环每篇最多试 2 次；每篇开始前与每次重试前检查 `page.is_closed()`，
死了就重建（上下文也死了由 `ensure_ready()` 重启浏览器）。重建仍失败才记
`missing（浏览器不可用，SI 未处理）`。


### 症状：两个后台任务同时跑，浏览器反复“无故”死亡

**现象**：两个 `lit_browser_fetch.py` 进程（例如一个补 SI 分块、一个补正文）交替报
`TargetClosedError` / `page_closed` / `浏览器不可用`，单看日志像是 Edge 不稳定。

**原因**：两者用同一个专用 profile，各自在启动/收尾时「清理占用 profile 的残留 Edge」，
**把对方的浏览器当孤儿杀掉**。实测 2026-10-26：一个分块任务与一次手动补 SI 并行，
双方成功率同时崩到接近 0，`state.json` 里却看不到风控失败。

**处理**：
1. 只保留一个进程；或给不同 `--profile` 并加 `--no-lock`；
2. 引擎默认持 `profile.lock`（OS 级，进程退出自动释放），第二个实例会直接
   打印占用信息并以 exit 2 退出；
3. 排查时先看进程列表，不要先怀疑站点：
   ```bash
   powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | ? { \$_.CommandLine -like '*lit_browser_fetch*' } | select ProcessId,CommandLine"
   ```

### 症状：浏览器启动失败 / 找不到 Edge

- 引擎默认 `channel` 自动探测 `msedge`，再退 `chrome`；
- 显式指定：`--channel msedge` 或 `--channel chrome`；
- 确认 Edge 已安装；Playwright 的 `channel="msedge"` 使用系统 Edge，不需要 `playwright install`；
- 若公司策略禁用远程调试，换 Chrome 或更新 Edge。

### 症状：profile 越来越大 / 越来越慢

- profile 会积累缓存；可在确认没有登录态需要保留时 `--reset-profile --apply`；
- 重置后需要重新 `--login` 或 `--seed-from`；
- 不要把 profile 提交 git（`_scratch/` 已忽略）。

### 症状：想比较“是 profile 还是 IP 的问题”

```bash
# A：全新 profile + 交互
python tools/lit_browser_fetch.py --doi <DOI> --apply --fresh-profile --interactive --no-si

# B：旧 profile + 交互
python tools/lit_browser_fetch.py --doi <DOI> --apply --interactive --no-si
```

- A 能过、B 不能 → 旧 profile 被标记/损坏，重置或换 profile；
- A/B 都不能过 → 大概率 IP 风险或该域要求人工，换网络。

---

## 7. 输入 / 收编 / 去重

### 症状：`--latest` 说“没有待处理项”，但明明有失败

- `--latest` 从新到旧找**第一份仍有 failed/si_missing 的 `fetch_result-*.json`**；
  若所有 fetch_result 都全成功，才回退到最新手动下载清单；
- 想指定某一份：`--in raw/notes/lit-watch/fetch_result-XXXX.json`；
- 或 `--in raw/notes/lit-watch/downloads/手动下载清单-XXXX.md`。

### 症状：DOI 被跳过（“已在库/范围外”）

- 默认按本机文献目录去重；测试时用 `--no-dedup`；
- `--no-dedup` 仍会跳过 `raw/pdf` 里已有的同名真 PDF；
- 若确实要重下，先确认目标文件不是坏文件，再手动移走/改名。

### 症状：`--import` 后 `Manual Download/` 空了

- 这是正常收编：`lit_manual_import --apply` 把 PDF 改名移入 `raw/pdf/<分类>/`；
- 看 `raw/notes/lit-watch/state/manual_import_log.json` 和
  `raw/notes/lit-watch/downloads/手动导入报告.md`；
- 未匹配的会进 `raw/pdf/_unmatched/`，不会删除。

### 症状：收编报 `ambiguous(1.00 vs 0.90)`，但那篇明明是对的

- **原因**：PDF 首页**没有 DOI**（Science 老排版常见，DOI 只在页脚/元数据里，提取不到），
  只能靠标题匹配；池里另一篇同主题论文（重叠词更多、分母更大）覆盖到 0.90，
  旧 margin 规则（差 <0.15 判 ambiguous）把真论文推去 `_unmatched/`。
  真实事故：`10.1126/science.aas9100`（2026-10-26）。
- **2026-10-26 起**：`NEAR_PERFECT_SCORE = 0.95` —— 标题 **1.00 精确命中**
  （候选标题的词全部出现在前两页）不再受 margin 约束；两条都不到 0.95 时**仍判 ambiguous**
  （不得为了过闸门放宽）。
- 若仍报 ambiguous：先看抢分的是谁（`match_one` 打印分值），
  再决定是补 DOI 还是人工收编；**不要**把阈值调到 1.0 硬过。

### 症状：测试时 `--import` 把测试 PDF 收进库了

- 测试必须用 `--outdir _scratch/...` 且**不要**加 `--import`；
- 已经收进去的，按 `manual_import_log.json` 找到目标，人工确认后移回测试目录；
- 以后把“测试不 import”写进命令模板。

---

## 8. 退出码与日志

| 码 | 含义 | 处理 |
|---|---|---|
| 0 | 全成功且 SI 不缺 | 进 C |
| 3 | 部分成功 / SI 仍缺 | 看残余清单，继续流水线 |
| 4 | 正文全失败 | 看报告/JSON/state；不要读成“没有文献” |
| 2 | 参数/输入/浏览器/profile 错误 | 先修环境 |

> **SI-only 输入（`"kind": "si"`）不参与正文成败**：全取到 → 0，仍缺 → 3，**不会**是 4
> （它们没有正文 status，2026-10-26 前会被误算成“正文全失败”）。

- 引擎默认追加 `wiki/log_ops.md`；测试用 `--no-log`；
- 报告与 JSON 在 `raw/notes/lit-watch/downloads/`；
- 残余清单是**给人看的唯一入口**，每条必须可点击。

---

## 9. 不要做的事

- ❌ 在 `Verifying…` 里连续点同一个位置；
- ❌ 把 `--limit` 设 0、把间隔设 0，一次下几百篇；
- ❌ 把 HTML 改名成 `.pdf` 冒充成功；
- ❌ 没有 SI 文件却把卡改成 `present`；
- ❌ 把 `--profile` 指向日常 Edge profile；
- ❌ 把测试 `--outdir` 加 `--import` 收进库；
- ❌ 为了过验证安装来源不明的“破解/绕过”扩展；
- ❌ 在没有机构权限时反复试付费墙论文。

---

## 10. 收集诊断信息（报 bug 时附上）

```bash
python tools/lit_browser_fetch.py --selftest
python tools/lit_browser_fetch.py --latest
# 最近一份 JSON 的失败项摘要
python - <<'PY'
import glob, json, os
p = sorted(glob.glob("raw/notes/lit-watch/downloads/browser-fetch-*.json"))[-1]
print("JSON:", p)
for x in json.load(open(p, encoding="utf-8")):
    if x.get("status") not in ("ok", "skipped"):
        print(x.get("doi"), x.get("publisher"), x.get("reason"))
        for a in (x.get("attempts") or [])[-6:]:
            print("   ", a)
PY
```

附上：DOI、出版商、`reason`、`attempts`、`state.json` 对应域、是否 `--interactive`、
是否刚 reset/seed 过 profile、网络环境（校园网/家庭/热点/VPN）。
