#!/usr/bin/env node

/**
 * matsci-kb-kit CLI wrapper
 * Provides npm-based access to the Python tools
 */

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const TOOLS_DIR = path.join(__dirname, '..', 'tools');

function showHelp() {
  console.log(`
matsci-kb-kit - 材料科学知识库工具箱

用法: matsci-kb <command> [args...]

核心命令:
  kb_init <target>           初始化新知识库
  kb_stats                   统计知识库状态
  kb_search <query>          检索知识库
  kb_lint [--quick]          健康检查
  kb_build_index             重建索引
  kb_toolcheck               工具自检

文献流水线:
  lit_discover               发现新文献
  lit_fetch                  下载文献
  lit_extract                提取元数据
  lit_ingest                 入库建卡
  lit_watch                  文献监控全链

Sci-Assistant 决策层:
  sci_landscape              方向景观分析
  sci_gap_scan               空白信号扫描
  sci_topic_rec              切入点推荐
  sci_method_extract         方法提取
  sci_protocol_gen           方案生成
  sci_lab_match              实验室匹配
  sci_progress               课题管理
  sci_data_analysis          数据分析

其他命令:
  help                       显示此帮助
  list                       列出所有可用工具
  check-deps                 检查 Python 依赖

示例:
  matsci-kb kb_init ./my-vault
  matsci-kb kb_search "电解液设计"
  matsci-kb sci_landscape --direction "电解液设计"

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
  const toolPath = path.join(TOOLS_DIR, `${toolName}.py`);
  
  if (!fs.existsSync(toolPath)) {
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
