#!/usr/bin/env node
/*
 * clean-pycache.js — npm prepack 钩子：删掉 __pycache__ / *.pyc / *.pyo。
 *
 * 🔴 为什么必须做这一步，而不能靠 ignore 文件：
 *   npm 明确规定「被 package.json 的 files 字段收进来的文件，无法再用
 *   .npmignore / .gitignore 排除」。files 里有 "tools/"，于是 tools/__pycache__/*.pyc
 *   会整包发出去（实测 62 个）。.npmignore 里写 __pycache__/ 一点作用都没有——
 *   所以那个文件被删掉了，免得它给人虚假的安全感。
 *
 * 🔴 为什么这算隐私问题而不只是垃圾文件：
 *   .pyc 里序列化了 code object 的 co_filename，也就是**构建机的绝对路径**。
 *   而 build_kit.scan_leaks() 用文本方式读文件，遇到二进制会 except 掉、静默跳过——
 *   泄漏扫描根本看不见 .pyc 里的内容。唯一可靠的办法是打包前物理删除。
 *
 * 只在 prepack 跑，不影响本地开发（__pycache__ 本来就在 .gitignore 里）。
 */
'use strict';

const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const SKIP_DIRS = new Set(['.git', 'node_modules']);
let removed = [];

function isJunk(name) {
  return name.endsWith('.pyc') || name.endsWith('.pyo');
}

function walk(dir) {
  let entries;
  try {
    entries = fs.readdirSync(dir, { withFileTypes: true });
  } catch (e) {
    return;
  }
  for (const ent of entries) {
    const full = path.join(dir, ent.name);
    if (ent.isDirectory()) {
      if (ent.name === '__pycache__') {
        fs.rmSync(full, { recursive: true, force: true });
        removed.push(path.relative(ROOT, full) + path.sep);
      } else if (!SKIP_DIRS.has(ent.name)) {
        walk(full);
      }
    } else if (isJunk(ent.name)) {
      fs.rmSync(full, { force: true });
      removed.push(path.relative(ROOT, full));
    }
  }
}

walk(ROOT);
if (removed.length) {
  console.log(`[prepack] 已清理 ${removed.length} 个 Python 构建产物：`);
  for (const r of removed.slice(0, 10)) console.log(`          ${r}`);
  if (removed.length > 10) console.log(`          …（其余 ${removed.length - 10} 个略）`);
} else {
  console.log('[prepack] 无 __pycache__ / *.pyc 需清理');
}
