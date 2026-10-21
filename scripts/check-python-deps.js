#!/usr/bin/env node

/**
 * Check Python dependencies after npm install
 */

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const ROOT = path.join(__dirname, '..');
const REQUIREMENTS = path.join(ROOT, 'requirements.txt');

console.log('🔍 检查 Python 依赖...\n');

const python = process.platform === 'win32' ? 'python' : 'python3';

// Check if Python is installed
const pythonCheck = spawn(python, ['--version'], { stdio: 'pipe' });

pythonCheck.on('error', (err) => {
  if (err.code === 'ENOENT') {
    console.log('⚠️  未检测到 Python');
    console.log('');
    console.log('matsci-kb-kit 需要 Python 3.10 或更高版本。');
    console.log('请从 https://www.python.org/downloads/ 下载安装。');
    console.log('');
    console.log('安装 Python 后，运行以下命令安装依赖:');
    console.log('  pip install -r requirements.txt');
    process.exit(0); // Don't fail npm install
  }
});

pythonCheck.stdout.on('data', (data) => {
  const version = data.toString().trim();
  console.log(`✓ Python: ${version}\n`);
  
  // Check if requirements.txt exists
  if (!fs.existsSync(REQUIREMENTS)) {
    console.log('⚠️  requirements.txt 不存在');
    return;
  }

  // Check Python dependencies
  const checkScript = `
import sys
import re

requirements = []
with open('${REQUIREMENTS.replace(/\\/g, '\\\\')}', 'r') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#'):
            pkg = re.split(r'[>=<]', line)[0].strip()
            if pkg:
                requirements.append(pkg)

missing = []
for pkg in requirements:
    try:
        __import__(pkg.replace('-', '_'))
    except ImportError:
        missing.append(pkg)

if missing:
    print(f'⚠️  缺少 {len(missing)} 个依赖:')
    for m in missing:
        print(f'  - {m}')
    print('')
    print('请运行以下命令安装:')
    print('  pip install -r requirements.txt')
    sys.exit(0)
else:
    print(f'✓ 所有 {len(requirements)} 个核心依赖已安装')
    sys.exit(0)
`;

  const depCheck = spawn(python, ['-c', checkScript], { stdio: 'inherit' });
  
  depCheck.on('error', () => {
    console.log('⚠️  依赖检查失败');
  });
});
