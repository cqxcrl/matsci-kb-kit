#!/usr/bin/env node

/**
 * Check Python dependencies after npm install.
 * Never fails the install: every path exits 0, problems are printed as warnings.
 */

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const ROOT = path.join(__dirname, '..');
const CORE = path.join(ROOT, 'requirements.txt');
const OPTIONAL = path.join(ROOT, 'requirements-optional.txt');

const python = process.platform === 'win32' ? 'python' : 'python3';

// Passed as argv so we never interpolate a Windows path into Python source.
const CHECK_SCRIPT = `
import importlib.util
import sys

# Windows consoles default to the OEM code page (GBK on zh-CN), which cannot
# print the ✓/✗/🔴 below. Without this the whole check dies on a codec error.
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# distribution name -> import name, for the packages where they differ.
IMPORT_NAME = {
    "pyyaml": "yaml",
    "pymupdf": "fitz",
    "scikit-learn": "sklearn",
    "sentence-transformers": "sentence_transformers",
    "ruamel.yaml": "ruamel",
    "curl-cffi": "curl_cffi",
    "curl_cffi": "curl_cffi",
}

# what you lose when an optional package is absent (kept short; details in
# requirements-optional.txt).
LOSS = {
    "sentence-transformers": "kb.py search 的默认 --mode hybrid 与 kb.py ask 会退出码 3",
    "scikit-learn": "语义检索无 TF-IDF 降级路径；sci_landscape 子方向聚类不可用",
    "playwright": "lit_browser_fetch 无法启动（反爬站点兜底下载）",
    "curl_cffi": "lit_browser_fetch 的 ACS/Cloudflare 路径不可用",
    "matplotlib": "sci_data_analysis / sci_progress 跳过绘图（统计与导出照常）",
    "openpyxl": ".xlsx 降级为 zip+XML 解析（旧版 .xls 仍不支持）",
    "ruamel.yaml": "qc_base_check 回退 PyYAML（不保序）",
    "pyperclip": "kb_cite --copy 只打印到 stdout",
}


def parse(req_path):
    out = []
    with open(req_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            name = line.split("[")[0]
            for sep in (">=", "<=", "==", ">", "<", "~=", ";"):
                name = name.split(sep)[0]
            name = name.strip()
            if name:
                out.append(name)
    return out


def installed(dist):
    mod = IMPORT_NAME.get(dist.lower(), dist.replace("-", "_"))
    try:
        return importlib.util.find_spec(mod) is not None
    except (ImportError, ValueError, ModuleNotFoundError):
        return False


core_path, opt_path = sys.argv[1], sys.argv[2]

core = parse(core_path)
missing_core = [p for p in core if not installed(p)]
if missing_core:
    print("✗ 缺少 %d 个核心依赖：" % len(missing_core))
    for m in missing_core:
        print("    - " + m)
    print("  请运行： pip install -r requirements.txt")
else:
    print("✓ 全部 %d 个核心依赖已安装" % len(core))

try:
    opt = parse(opt_path)
except OSError:
    opt = []

if opt:
    have = [p for p in opt if installed(p)]
    want = [p for p in opt if not installed(p)]
    print("")
    print("可选依赖：%d/%d 已安装" % (len(have), len(opt)))
    for p in want:
        loss = LOSS.get(p.replace("-", "_"), LOSS.get(p, "部分功能不可用"))
        print("    - %-22s 缺 → %s" % (p, loss))
    if want:
        print("  想要全部： pip install -r requirements-optional.txt")
        print("  🔴 不装 sentence-transformers 时，检索请显式用 --mode bm25。")

sys.exit(0)
`;

function run(args, onDone) {
  const proc = spawn(python, args, { stdio: ['ignore', 'inherit', 'inherit'] });
  proc.on('error', onDone);
  proc.on('exit', onDone);
}

console.log('🔍 检查 Python 依赖...\n');

const probe = spawn(python, ['--version'], { stdio: ['ignore', 'pipe', 'pipe'] });
let probeFailed = false;

probe.on('error', (err) => {
  if (err.code !== 'ENOENT') return;
  probeFailed = true;
  console.log('⚠️  未检测到 Python');
  console.log('');
  console.log('matsci-kb-kit 需要 Python 3.10 或更高版本。');
  console.log('请从 https://www.python.org/downloads/ 下载安装。');
  console.log('');
  console.log('安装 Python 后，运行以下命令安装依赖:');
  console.log('  pip install -r requirements.txt');
  console.log('  pip install -r requirements-optional.txt   # 可选，语义检索/浏览器兜底');
  process.exit(0);
});

probe.stdout.on('data', (data) => {
  console.log(`✓ Python: ${data.toString().trim()}\n`);
});

probe.on('exit', () => {
  if (probeFailed) return;
  if (!fs.existsSync(CORE)) {
    console.log('⚠️  requirements.txt 不存在');
    process.exit(0);
  }
  run(['-c', CHECK_SCRIPT, CORE, OPTIONAL], () => process.exit(0));
});
