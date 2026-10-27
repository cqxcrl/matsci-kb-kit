#!/usr/bin/env node

/**
 * matsci-kb-kit CLI wrapper
 * Provides npm-based access to the Python tools
 */

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const TOOLS_DIR = path.join(__dirname, '..', 'tools');
const SCRIPTS_DIR = path.join(__dirname, '..', 'scripts');

function showHelp() {
  console.log(`
matsci-kb-kit - 材料科学知识库工具箱

用法: matsci-kb <command> [args...]

核心命令:
  kb_init <target>           初始化新知识库
  kb <subcommand>            统一入口（ask/search/route/corpus/stats/doctor/index/serve/lint/toolcheck/tools/selftest）
  kb_search <query>          检索知识库（BM25 / 语义 / 混合）
  kb_rag <query>             传统 RAG：BM25 + 向量 + RRF + 本地 CrossEncoder 强制精排
  kb_agentic <query>         Agentic RAG：查询分类 → 规划 → 分层取证 → 图谱扩展
  kb_lint [--quick|--deep]   健康检查
  kb_build_index             重建索引
  kb_manifest                静态工具/CLI 清单
  kb_toolcheck               工具自检（实跑每个工具的 --selftest）

文献流水线:
  lit_discover               发现新文献（OpenAlex）
  lit_fetch                  下载 OA 全文
  lit_browser_fetch          浏览器兜底下载（自动取全文被 403/Cloudflare 挡住时）
  lit_extract                PDF → md/图 提取
  lit_ingest                 入库建卡
  lit_si                     补充材料（SI）存在性判定 / 自动获取
  lit_enrich                 证据化二次加工（带逐行 quote 校验）
  lit_finish                 收尾（index/log/索引）
  lit_daily                  每日发现全链

质检层:
  qc_proj_sources            项目卡字段门禁
  qc_proj_names              项目卡 ↔ PDF/Extract/SI 命名归属矩阵
  qc_proj_assets             项目 Extract 图片链接审计
  qc_evidence_base           证据强度判定口径
  qc_evidence_audit          「正文引用但未登记 sources」分类
  qc_si_backfill             补 si_status
  qc_sources_drift           sources: 语义漂移修复

Sci-Assistant 决策层:
  sci_landscape              C1 方向景观分析
  sci_gap_scan               C1 空白信号扫描
  sci_topic_rec              C1 切入点推荐
  sci_method_extract         C2 方法提取
  sci_protocol_gen           C2 方案生成
  sci_lab_match              C2 实验室匹配
  sci_method_chain           C2 方法链
  sci_progress               C3 课题管理
  sci_data_analysis          C3 数据分析
  sci_ecsa_qc                C3 ECSA 五道门
  sci_review                 C3 复盘建议
  sci_links                  贯穿 C1→C2→C3 的链路溯源

其他命令:
  help                       显示此帮助
  list                       列出所有可用工具
  check-deps                 检查 Python 依赖

示例:
  matsci-kb kb_init ./my-vault
  matsci-kb kb_search "固态电解质 界面"
  matsci-kb kb ask "这个方向的证据充分吗"
  matsci-kb sci_landscape --direction "<你的研究方向>"

文档: https://github.com/cqxcrl/matsci-kb-kit#readme
`);
}

function listTools() {
  const tools = fs.readdirSync(TOOLS_DIR)
    .filter(f => f.endsWith('.py'))
    .sort();
  
  console.log('可用工具:\n');
  tools.forEach(t => {
    const name = t.replace('.py', '');
    console.log(`  ${name}`);
  });
  console.log(`\n共 ${tools.length} 个工具`);
  console.log('\n使用 matsci-kb <tool-name> --help 查看工具详情');
}

function runPythonTool(toolName, args) {
  // tools/ 是主体；kb_init / verify_kit 这类安装期脚本在 scripts/。
  const candidates = [path.join(TOOLS_DIR, `${toolName}.py`),
                      path.join(SCRIPTS_DIR, `${toolName}.py`)];
  const toolPath = candidates.find(p => fs.existsSync(p));

  if (!toolPath) {
    console.error(`错误: 工具 ${toolName} 不存在`);
    console.error(`使用 'matsci-kb list' 查看所有可用工具`);
    process.exit(1);
  }

  const python = process.platform === 'win32' ? 'python' : 'python3';
  const proc = spawn(python, [toolPath, ...args], {
    stdio: 'inherit',
    cwd: process.cwd()
  });

  proc.on('error', (err) => {
    if (err.code === 'ENOENT') {
      console.error('错误: 未找到 Python');
      console.error('请安装 Python 3.10 或更高版本: https://www.python.org/downloads/');
      process.exit(1);
    } else {
      console.error('执行错误:', err);
      process.exit(1);
    }
  });

  proc.on('exit', (code) => {
    process.exit(code);
  });
}

function checkDeps() {
  const python = process.platform === 'win32' ? 'python' : 'python3';
  const checkScript = `
import sys
try:
    import yaml
    import jieba
    import numpy
    print('✓ 核心依赖已安装')
    sys.exit(0)
except ImportError as e:
    print(f'✗ 缺少依赖: {e.name}')
    print('请运行: pip install -r requirements.txt')
    sys.exit(1)
`;

  const proc = spawn(python, ['-c', checkScript], {
    stdio: 'inherit'
  });

  proc.on('error', () => {
    console.error('错误: 未找到 Python');
    process.exit(1);
  });
}

// Main
const args = process.argv.slice(2);
const command = args[0];

if (!command || command === 'help' || command === '--help' || command === '-h') {
  showHelp();
} else if (command === 'list') {
  listTools();
} else if (command === 'check-deps') {
  checkDeps();
} else if (command === 'kb_init') {
  const target = args[1];
  if (!target) {
    console.error('用法: matsci-kb kb_init <target-directory>');
    process.exit(1);
  }
  runPythonTool('kb_init', ['--target', target, ...args.slice(2)]);
} else {
  // Pass through to Python tool
  runPythonTool(command, args.slice(1));
}
