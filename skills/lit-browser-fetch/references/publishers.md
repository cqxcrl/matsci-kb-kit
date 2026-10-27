# 出版商配方与实测记录（lit-browser-fetch）

> 引擎里的 `RECIPES` 在 `tools/lit_browser_fetch.py` 顶部。本文件解释**为什么这样写**、
> 实测到哪一步、以及下次复测该看什么。所有 URL 模板里的 `{doi}` / `{suffix}` 由
> `Recipe.article_url()` / `pdf_url()` 填充；`{suffix}` 是 DOI 斜杠后的部分。
>
> **实测基线：2026-10-26。** 当天测试 profile/IP 已被前序 Cloudflare 尝试标记，
> 所以“未复测”不等于“不支持”；干净 profile + 人工过一次后可重跑本表。

## 一张总表

| DOI 前缀 | key | 文章页 | PDF 直链 / 捕获 | 验证体系 | SI 专题页 | 实测 |
|---|---|---|---|---|---|---|
| `10.1002` | `wiley` | `http<库外路径> | `http<库外路径> `fetch` | Cloudflare | `http<库外路径> | ✅ 正文 + SI |
| `10.1021` | `acs` | `http<库外路径> | `http<库外路径> 或点 PDF 后 `href_fetch` | Cloudflare | `http<库外路径> | ✅ 正文 + SI |
| `10.1016` | `elsevier` | `http<库外路径> | 点 “View PDF” → 新签名 S3 页 → 页内 `fetch(location.href)` | Cloudflare | 无独立 SI 页；走 `lit_si` 直链 | ✅ 需有效 `cf_clearance` |
| `10.1038` | `nature` | `http<库外路径> | `http<库外路径> `fetch` | Cloudflare | 文章页 Supporting information | ✅ 主要走 `lit_si` |
| `10.1007` | `springer` | `http<库外路径> | `http<库外路径> | Cloudflare | 文章页 Supplementary information | ✅ 主要走 `lit_si` |
| `10.1126` | `science` | `http<库外路径> | `http<库外路径> `fetch` | Cloudflare | `http<库外路径> | ✅ 正文 + SI |
| `10.1039` | `rsc` | `http<库外路径> | 点 `articlepdf` / `a[href*='/pdf/']` | Cloudflare | 文章页 Supplementary files | ⚠️ 未干净复测 |
| `10.1149` / `10.1088` | `iop` | `http<库外路径> | 点 PDF 链接 | Radware / hCaptcha 图片格 | `http<库外路径> | ⚠️ 必须 `--interactive` |
| `10.1073` | `pnas` | `http<库外路径> | 点 PDF 链接 | Cloudflare | 文章页 Supporting Information | ⚠️ 未干净复测 |
| `10.1063` | `aip` | `http<库外路径> | 点 PDF 链接 | Cloudflare | 文章页 Supplementary Material | ⚠️ 未干净复测 |
| `10.1103` | `aps` | `http<库外路径> | 点 `/pdf/` 链接；`/abstract/` → `/pdf/` 直链兜底 | Cloudflare | 文章页 Supplemental Material | ⚠️ 已加兜底，未复测 |
| 其他 | `generic` | `http<库外路径> | 找 PDF 链接 → 点击/抓取；最后试 `oa_url` | 视出版商 | 找 `suppl`/`suppdata` 链接 | 兜底 |

> 若 DOI 前缀不在表里，`classify_recipe()` 返回 `generic`。这时不要硬编码新配方，
> 先交互模式打开文章页，确认 PDF 链接形态，再加 recipe + selftest 夹具。

---

## 捕获顺序（引擎实际执行）

`download_main()` 的顺序对所有出版商一致，recipe 只决定“优先用哪种”：

1. 打开文章页 → `dismiss_cookies()` → `pass_challenge()`。
2. 若当前就是 PDF → 页内 `fetch(location.href)`。
3. recipe 指定的首选取法：
   - `page_fetch`：页内 `fetch(pdf_url)`（Wiley/Nature/Springer/Science）。
   - `curl`：`curl_cffi` + 浏览器 cookie + UA/referer（ACS）。
   - `click`：跳过，直接进第 4 步（Elsevier/RSC/PNAS/AIP/APS/IOP/generic）。
4. `find_pdf_link()` 找可见 PDF 链接 → `click_link_capture()`：
   - 监听 `popup` 与 `download` 事件，最多等 23 秒；
   - 新页若是 PDF → 页内 fetch；新页若只是文章页 → 在新页再找链接；
   - 下载事件 → `download.save_as(dest)`，校验 `%PDF-`；
   - 同页导航成 PDF → fetch；
   - 最后对链接 href 做 `fetch` / `curl` 兜底。
5. 直链兜底：`pdf_url`、输入里的 `pdf_url`/`oa_url`、以及 `/abstract/` → `/pdf/` 猜测。
6. 新开页直接访问 PDF URL → 过验证 → fetch。

**任何一步拿到的字节都必须过 `looks_pdf()`**：`%PDF-` 开头且不是 HTML。
校验失败不会落盘，原因写进 `Item.attempts`。

---

## 逐出版商笔记

### Wiley（`10.1002`）✅

- 文章页 `onlinelibrary.wiley.com/doi/<doi>` 通常能过 Cloudflare；`pdfdirect` 在页内 `fetch`
  可拿到真 PDF。
- **SI 链接在折叠的 Supporting Information 区，常不可见**。`find_si_links()` 对
  `downloadSupplement` / `suppdata` / `.docx` 这类 **SI 专属**链接放行“不可见”，
  对泛化的 `.pdf` 仍要求可见。
- SI 端点对脚本 403，但文件名可从 PDF 文末 `SupportingFile: ...` 读到；
  `lit_si.fetch` 会拼 `action/downloadSupplement?doi=…&file=…`。
- 实测：正文 2.4 MB，SI 1.36 MB。

### ACS（`10.1021`）✅

- 文章页可能先过 Cloudflare；过完后 `curl_cffi(impersonate="chrome")` 带浏览器 cookie
  请求 `pubs.acs.org/doi/pdf/...`，常能直接拿 PDF。
- 若 `curl` 拿到 HTML，点页面上的 PDF 链接，走 `href_fetch`。
- **正文链接形态（2026-10-26 实测）**：文章页已改版为
  `pubs.acs.org/<journal>/article-pdf/<vol>/<issue>/<page>/<id>/<doi-suffix>.pdf`，
  anchor 文本是 `PDF Link / Open PDF`；`find_pdf_link()` 的 `a[href*='article-pdf']` 先命中。
- **SI 链接形态**：`.../article-supplement/<id>/pdf/<suffix>_si_001/`（不带 `.pdf` 后缀），
  同时含 `supplement` 与 `_si_`，`is_si_href()` 两道都能拦。旧版 `/doi/suppl/<doi>` 仍可用。
- 🔴 **SI 链接是"导航即下载"，且文件可达 145 MB**（2026-10-26 实测 `jacs.6c10800`）：
  - `page.goto(si_url)` 抛 `Download is starting`（浏览器自己开下载）；
  - 页内 `fetch` 拿到的 Content-Length 是 **145 657 612 B** ⇒ 撞 `fetch_bytes_in_page`
    的 **100 MB 上限**，只报 `page_fetch_too_big`；
  - `ctx.request.get()` 对该端点返回 **403**；点击链接待 32 秒也可能等不到 `popup`/`download`。
  ⇒ 正确做法是 `nav_download_bytes()`：新页 `expect_download()` + `goto()`，让浏览器落盘。
  这就是 ACS 一批 SI 长期 `missing` 的直接原因，**不是反爬**。
- 🆕 **尾斜杠曾让点击路径全灭**：`os.path.basename(".../ja6c10800_si_001/")` 是空串，
  旧 `click_si_download` 的 `target in h` 永远不成立 ⇒ 整批 `no_element_for_href`。
  现由 `si_href_key()` / `si_href_matches()` 归一处理（rstrip `/` + 相对转绝对）。
- 🔴 **不要用“页数少 + 首页有 Supporting Information”直接判 SI**：ACS 主文首页常写
  `* Supporting Information` 作为 section 指针。`looks_like_si()` 必须同时要求**首页无 Abstract**；
  2026-10-26 修掉了“Abstract 落在 600 字外”的假阳性（jacs.9b00911，9 页 12 MB 主文被误杀）。
  看到 `got_si_instead_of_main（...; file='ja9b00911.pdf'）` 先怀疑闸门，不要急着当 SI。
- 实测：正文 8.7 MB / 5.6 MB / 10.1 MB 等，SI 950 KB–3.2 MB。

### Elsevier / ScienceDirect（`10.1016`）✅（需有效 clearance）

- 不要直接 fetch `pdf` URL；ScienceDirect 的 PDF 是**点击后新开的签名 S3 页**。
- 流程：文章页 → 关 cookie 弹窗 → 点 “View PDF” → 新页 URL 是 `pdf.sciencedirectassets.com/...`
  → `page.evaluate(fetch(location.href))`。
- 没有有效 `cf_clearance` 时，文章页会卡在 `Verifying…`。可：
  - `--interactive` 人工过一次；
  - `--seed-from` 一个已有人工验证的 profile；
  - 确认机构 IP 授权（实测 USTC IP 210.45.118.3 有权限）。
- 实测：正文 9.4 MB（seeded profile）。

### Science / AAAS（`10.1126`）✅

- 正文：文章页内 `fetch(http<库外路径> 可拿。
- **SI 必须真点击**：直接 fetch/curl SI 端点返回 403 HTML；点 `suppl_file` 链接会触发下载事件。
  `download_si()` 因此先试 SI 页，再回文章页，最后 `click_si_download()`。
- 实测：正文 0.9 MB，SI 6.08 MB。

### Nature / Springer（`10.1038` / `10.1007`）✅

- 正文可用 `page_fetch` 直链；SI 优先走 `lit_si.fetch`（`static-content.springer.com` 直链）。
- Nature 的 SI 真实链接常是 `media.springernature.com/.../MediaObjects/<MOESM>`；
  拿到 href 后直接 HTTP 下即可，不必让浏览器落盘。
- `lit_si.fetch` 的 `--year` 只影响 Nature 系：DOI 里的年份可能被截成 3 位，必须给真年份。

### RSC（`10.1039`）⚠️

- 文章页通常由 `doi.org` 跳到 `pubs.rsc.org/en/content/articlelanding/...`。
- PDF 链接形态：`.../articlepdf/...`，`find_pdf_link()` 的 `article-pdf` / `/pdf/` 选择器应能命中。
- 2026-10-26 测试时页面直接进 Cloudflare 挑战，未取得干净正文；**不是配方已证明失败**。
- 复测建议：`--interactive` 过一次，确认文章页 DOM 里 PDF 链接的 href 与文本；
  若链接在 shadow DOM/JS 按钮里，补选择器或改成点按钮后等 `download` 事件。

### PNAS（`10.1073`）⚠️

- `doi.org` → `pnas.org/doi/<doi>`；PDF 链接通常是 `/doi/pdf/<doi>`。
- 2026-10-26 测试返回 `captcha_requires_human`（Cloudflare），未取得干净正文。
- 复测建议同 RSC；PNAS 的 Cloudflare 对自动化较敏感，优先 `--interactive`。

### AIP（`10.1063`）⚠️

- `doi.org` → `pubs.aip.org/.../article/<doi>`；PDF 链接常含 `article-pdf`。
- 2026-10-26 测试 `challenge_timeout`（Cloudflare），未取得干净正文。
- 复测建议：确认文章页是否先跳 `pubs.aip.org` 的 cookie/挑战页；交互模式过一次。

### APS（`10.1103`）⚠️

- `doi.org` → `journals.aps.org/<刊>/abstract/<doi>`。
- PDF 直链规律：`http<库外路径>
  引擎已做 `/abstract/` → `/pdf/` 猜测，并在 `find_pdf_link()` 增加 `a[href*='/pdf/']`。
- 2026-10-26 测试失败原因是 `no_pdf_link_on_article`，当时还没有上述兜底；**未复测**。
- 若仍失败：交互模式打开文章页，看 PDF 链接是否被订阅墙隐藏；APS 的 PDF 可能只对订阅者显示。

### IOP / ECS（`10.1149` / `10.1088`）⚠️

- `iopscience.iop.org/article/<doi>` 使用 Radware bot manager，常见 hCaptcha 图片格或
  `Press & Hold`。
- 无人值守**不猜图片**：`detect_state()` 会把含 “select all / click each / tiles” 的挑战
  判为 `image_grid`，直接返回 `captcha_requires_human`。
- `Press & Hold` 有 `press_and_hold()`（按住 6–9 秒），但 Radware 仍可能要求图片格。
- 正确用法：`--interactive`，人工过一次；之后同域会话可复用。
- SI 专题页：`/article/<doi>/suppdata`。

### Generic（其他 DOI）

- 打开 `doi.org`，过验证，找 PDF 链接；找不到就试输入里的 `pdf_url` / `oa_url`。
- 如果文章页是 JS 渲染的阅读器（如某些平台），`find_pdf_link()` 可能看不到链接；
  交互模式人工点一次，确认下载 URL 后可作为 `--doi` 单篇的输入补充。
- 不要为单个出版商写“死循环重试”；失败就进残余清单。

---

## 选择器与 DOM 经验

`find_pdf_link()` 的当前顺序：

```text
a[href*='pdfdirect']
a[href*='/doi/pdf/']
a[href*='/pdf/']
a[href*='article-pdf']
a[href*='pdfft']
a[href*='articlepdf']
a[href*='.pdf']
a:has-text('View PDF')
a:has-text('Download PDF')
a:has-text('PDF')
button:has-text('View PDF')
button:has-text('PDF')
```

注意：

- 所有候选都要求 **可见**（`is_visible()`）。如果出版商的 PDF 链接在折叠菜单里，
  先点开对应 tab/按钮，或把该链接加入 SI 专属放行名单（只对 SI，不对正文）。
- 过滤掉 `suppl` / `supplement` / `mmc` / `supporting` 且 URL 不含 `pdf`/`pdfft` 的链接，
  防止把 SI 当正文。
- `a:has-text('PDF')` 可能命中 “PDF” 导航或 “PDF 下载说明”；引擎取第一个命中的，
  所以更具体的 href 选择器必须排在前面。
- **不要用 `page.content()` 正则找 PDF URL**：很多链接是相对路径/JS 拼接，
  正则会抓到大量假阳性。优先 `query_selector_all` + `bounding_box`。

---

## SI 链接经验

`find_si_links()` 的放行规则：

- **SI 专属**（可不可见）：`downloadSupplement`、`/article-supplement/`、`suppdata`、
  `/suppl/`、`supplementary`、`supporting`、`.docx`、`.xlsx`、`.zip`。
- **泛化 `.pdf`**：必须可见，且链接文本/URL 不像正文 PDF。
- Wiley 的 `downloadSupplement` 常藏在折叠区，所以不能要求可见。
- ACS 的 SI 专题页 `/doi/suppl/<doi>` 上文件链接通常可见。
- Science 的 SI 链接点击才会触发下载；直接 fetch 403。

---

## 复测清单（下次有干净 IP/profile 时）

1. `python tools/lit_browser_fetch.py --selftest` 必须 **56/56 PASS**（2026-10-26 起）。
2. 每个出版商选 1 篇**有机构权限、有 SI** 的论文，单篇跑：
   ```bash
   python tools/lit_browser_fetch.py --doi <DOI> --apply --no-dedup \
          --outdir _scratch/lit-browser-fetch-test/retest --no-log --no-residual
   ```
   （`--no-dedup` 防止本地目录里已有 DOI 被跳过；测试输出不要 `--import`。）
3. 记录：正文大小、方法（`page_fetch` / `curl_cffi` / `click` / `href_fetch`）、
   SI 状态、是否遇到挑战。
4. 只有**真 PDF 落盘且 `%PDF-` 校验通过**才算成功；HTML/登录页不算。
5. 把结果更新到本文件“实测”列，并在 `wiki/log_ops.md` 记一条。
