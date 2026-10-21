/**
 * matsci-kb-kit - 材料科学知识库工具箱
 * 
 * Toolbox + methodology for building an Obsidian knowledge base:
 * retrieval, literature pipeline, QC, MCP server, and Sci-Assistant decision layer.
 */

const path = require('path');

module.exports = {
  toolsDir: path.join(__dirname, 'tools'),
  scriptsDir: path.join(__dirname, 'scripts'),
  scaffoldDir: path.join(__dirname, 'scaffold'),
  skillsDir: path.join(__dirname, 'skills'),
  docsDir: path.join(__dirname, 'docs'),
  
  version: require('./package.json').version,
  
  /**
   * Get path to a specific tool
   * @param {string} toolName - Tool name without .py extension
   * @returns {string} Full path to the tool
   */
  getToolPath: function(toolName) {
    return path.join(this.toolsDir, `${toolName}.py`);
  },
  
  /**
   * List all available tools
   * @returns {string[]} Array of tool names
   */
  listTools: function() {
    const fs = require('fs');
    return fs.readdirSync(this.toolsDir)
      .filter(f => f.endsWith('.py'))
      .map(f => f.replace('.py', ''))
      .sort();
  }
};
