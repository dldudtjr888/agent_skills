#!/usr/bin/env node
/**
 * Multi-Dimensional Code Analysis for JavaScript/TypeScript Projects
 * Supports: JS, JSX, TS, TSX, MJS, CJS, Vue, Svelte
 * Analyzes code across 5 dimensions: Maintainability, Performance, Security, Scalability, Reusability
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const { parseArgs } = require('node:util');

// Required packages for each dimension
const REQUIRED_PACKAGES = {
  maintainability: ['eslint', '@typescript-eslint/eslint-plugin'],
  performance: ['webpack-bundle-analyzer', 'lighthouse'],
  security: ['eslint-plugin-security', 'npm-audit'],
  scalability: ['dependency-cruiser', 'madge'],
  reusability: ['jscpd']
};

function checkPackageInstalled(packageName) {
  try {
    require.resolve(packageName);
    return true;
  } catch {
    return false;
  }
}

function checkDependencies(dimensions) {
  const available = {};
  
  for (const dim of dimensions) {
    if (!(dim in REQUIRED_PACKAGES)) continue;
    
    let dimAvailable = true;
    for (const pkg of REQUIRED_PACKAGES[dim]) {
      if (!checkPackageInstalled(pkg)) {
        console.log(`⚠️  ${pkg} not installed - ${dim} analysis may be limited`);
        dimAvailable = false;
      }
    }
    
    available[dim] = dimAvailable;
  }
  
  return available;
}

class MultiDimensionalAnalyzer {
  static VERSION = '1.1.0';

  constructor(projectPath, dimensions) {
    this.projectPath = path.resolve(projectPath);
    this.dimensions = dimensions;
    this.toolsUsed = [];
    this.toolsFailed = [];
    this.filesAnalyzed = 0;
    this.filesSkipped = 0;
    this.results = {
      meta: {
        analyzer_version: MultiDimensionalAnalyzer.VERSION,
        tools_used: [],
        tools_failed: [],
        coverage: { files_analyzed: 0, files_skipped: 0 },
        confidence: 1.0
      },
      project: projectPath,
      dimensions: {},
      overall_health: 0,
      priority_actions: []
    };
  }

  _trackTool(toolName, success, reason = null) {
    if (success) {
      if (!this.toolsUsed.includes(toolName)) {
        this.toolsUsed.push(toolName);
      }
    } else {
      if (!this.toolsFailed.find(t => t.tool === toolName)) {
        this.toolsFailed.push({ tool: toolName, reason: reason || 'unknown' });
      }
    }
  }

  _finalizeMeta() {
    this.results.meta.tools_used = this.toolsUsed;
    this.results.meta.tools_failed = this.toolsFailed.map(t => t.tool);
    this.results.meta.coverage = {
      files_analyzed: this.filesAnalyzed,
      files_skipped: this.filesSkipped
    };
    // Calculate confidence based on tool availability
    const expectedTools = ['eslint', 'madge', 'jscpd'];
    const availableCount = expectedTools.filter(t => this.toolsUsed.includes(t)).length;
    const failedCount = this.toolsFailed.length;
    this.results.meta.confidence = Math.max(0.5,
      parseFloat((1.0 - (failedCount * 0.1) - ((3 - availableCount) * 0.05)).toFixed(2))
    );
  }

  async analyze() {
    console.log(`\n🔍 Analyzing ${this.projectPath} across ${this.dimensions.length} dimensions...\n`);
    
    if (this.dimensions.includes('maintainability')) {
      this.results.dimensions.maintainability = await this.analyzeMaintainability();
    }
    
    if (this.dimensions.includes('performance')) {
      this.results.dimensions.performance = await this.analyzePerformance();
    }
    
    if (this.dimensions.includes('security')) {
      this.results.dimensions.security = await this.analyzeSecurity();
    }
    
    if (this.dimensions.includes('scalability')) {
      this.results.dimensions.scalability = await this.analyzeScalability();
    }
    
    if (this.dimensions.includes('reusability')) {
      this.results.dimensions.reusability = await this.analyzeReusability();
    }
    
    // Calculate overall health
    this.calculateOverallHealth();

    // Generate priority actions
    this.generatePriorityActions();

    // Finalize meta information
    this._finalizeMeta();

    return this.results;
  }

  async analyzeMaintainability() {
    console.log('🔧 Analyzing Maintainability...');
    
    const result = {
      score: 0,
      coverage: 'comprehensive',
      metrics: {},
      issues: []
    };
    
    // Run ESLint for code quality
    try {
      const eslintPath = path.join(this.projectPath, 'node_modules', '.bin', 'eslint');
      
      if (fs.existsSync(eslintPath)) {
        const output = execSync(
          `${eslintPath} "${this.projectPath}" --format json --max-warnings 0 || true`,
          { encoding: 'utf-8', maxBuffer: 10 * 1024 * 1024 }
        );

        const eslintResults = JSON.parse(output);
        this._trackTool('eslint', true);

        let errorCount = 0;
        let warningCount = 0;
        const complexityIssues = [];

        for (const file of eslintResults) {
          this.filesAnalyzed++;
          errorCount += file.errorCount || 0;
          warningCount += file.warningCount || 0;

          // Look for complexity issues
          for (const message of file.messages || []) {
            if (message.ruleId === 'complexity') {
              complexityIssues.push({
                file: file.filePath,
                line: message.line,
                message: message.message,
                severity: message.severity === 2 ? 'error' : 'warning'
              });
            }
          }
        }

        result.metrics.eslint_errors = errorCount;
        result.metrics.eslint_warnings = warningCount;
        result.metrics.complexity_issues = complexityIssues.length;
        result.issues = complexityIssues;

        // Calculate score
        if (errorCount === 0 && warningCount < 10) {
          result.score = 95;
        } else if (errorCount < 5 && warningCount < 50) {
          result.score = 80;
        } else if (errorCount < 20) {
          result.score = 60;
        } else {
          result.score = 40;
        }
      } else {
        this._trackTool('eslint', false, 'not installed');
      }
    } catch (error) {
      this._trackTool('eslint', false, error.message);
      console.log(`  Warning: ESLint analysis failed - ${error.message}`);
      result.score = 70; // Neutral score if can't analyze
    }
    
    console.log(`  ✓ Maintainability score: ${result.score}/100`);
    return result;
  }

  async analyzePerformance() {
    console.log('⚡ Analyzing Performance...');

    const result = {
      score: 100, // Start with perfect score
      bottlenecks: [],
      improvements: [],
      bundle_issues: [],
      metrics: {
        asyncPatternIssues: 0,
        memoryLeakRisks: 0,
        inefficientLoops: 0,
        largeDataStructures: 0,
        blockingOperations: 0
      }
    };

    const jsFiles = this.findFiles(this.projectPath, ['.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs', '.vue', '.svelte']);

    // Performance anti-patterns (generic - works for any JS/TS project)
    const performancePatterns = [
      // Async/Await issues
      {
        pattern: /await\s+\w+\([^)]*\);\s*await\s+\w+\([^)]*\)/g,
        type: 'sequential_await',
        severity: 'medium',
        message: 'Sequential await calls - consider Promise.all for parallel execution'
      },
      {
        pattern: /for\s*\([^)]+\)\s*\{[^}]*await/g,
        type: 'await_in_loop',
        severity: 'high',
        message: 'Await inside loop - consider batching or Promise.all'
      },

      // Memory leak risks
      {
        pattern: /addEventListener\s*\([^)]+\)(?![\s\S]*removeEventListener)/g,
        type: 'missing_cleanup',
        severity: 'medium',
        message: 'addEventListener without removeEventListener - potential memory leak'
      },
      {
        pattern: /setInterval\s*\([^)]+\)(?![\s\S]*clearInterval)/g,
        type: 'missing_cleanup',
        severity: 'high',
        message: 'setInterval without clearInterval - potential memory leak'
      },
      {
        pattern: /setTimeout\s*\([^)]+\)(?![\s\S]*clearTimeout)/g,
        type: 'missing_cleanup',
        severity: 'low',
        message: 'setTimeout without clearTimeout - consider cleanup in long-running code'
      },

      // Inefficient operations
      {
        pattern: /\.forEach\([^)]+\)\s*\.forEach/g,
        type: 'nested_iteration',
        severity: 'high',
        message: 'Nested forEach loops - O(n²) complexity, consider refactoring'
      },
      {
        pattern: /for\s*\([^)]+\)\s*\{[^}]*for\s*\([^)]+\)\s*\{/g,
        type: 'nested_iteration',
        severity: 'medium',
        message: 'Nested for loops - potential O(n²) complexity'
      },
      {
        pattern: /\.filter\([^)]+\)\[0\]/g,
        type: 'inefficient_search',
        severity: 'low',
        message: 'filter()[0] - use find() for better performance'
      },
      {
        pattern: /\.indexOf\([^)]+\)\s*[!=]=\s*-1/g,
        type: 'inefficient_search',
        severity: 'low',
        message: 'indexOf != -1 - consider includes() for readability'
      },

      // Blocking operations
      {
        pattern: /fs\.(readFileSync|writeFileSync|readdirSync|statSync|existsSync)/g,
        type: 'sync_io',
        severity: 'medium',
        message: 'Synchronous file operation - consider async alternatives'
      },
      {
        pattern: /execSync\s*\(/g,
        type: 'sync_exec',
        severity: 'medium',
        message: 'execSync - consider exec or spawn for non-blocking execution'
      },
      {
        pattern: /JSON\.parse\s*\(\s*fs\.readFileSync/g,
        type: 'sync_json_read',
        severity: 'medium',
        message: 'Synchronous JSON file read - consider async/streaming for large files'
      },

      // Large data structure issues
      {
        pattern: /new\s+Array\s*\(\s*\d{6,}\s*\)/g,
        type: 'large_array',
        severity: 'high',
        message: 'Creating very large array - consider streaming or pagination'
      },
      {
        pattern: /\.concat\([^)]+\)/g,
        type: 'array_concat',
        severity: 'low',
        message: 'Array.concat creates new array - consider spread or push for performance'
      },

      // String operations
      {
        pattern: /\+\s*['"`][^'"`]*['"`]\s*\+/g,
        type: 'string_concat',
        severity: 'low',
        message: 'String concatenation in loop - consider template literals or array join'
      },

      // RegExp in loops
      {
        pattern: /for\s*\([^)]+\)\s*\{[^}]*new\s+RegExp/g,
        type: 'regexp_in_loop',
        severity: 'medium',
        message: 'Creating RegExp in loop - move outside loop for better performance'
      },

      // Object creation in render/hot paths
      {
        pattern: /return\s*\{[^}]*\{[^}]*\}[^}]*\}/g,
        type: 'inline_object',
        severity: 'low',
        message: 'Inline object creation - may cause unnecessary re-renders in reactive frameworks'
      }
    ];

    let totalIssues = 0;

    for (const file of jsFiles) {
      try {
        const content = fs.readFileSync(file, 'utf-8');
        const relativePath = path.relative(this.projectPath, file);
        const lines = content.split('\n');

        for (const { pattern, type, severity, message } of performancePatterns) {
          pattern.lastIndex = 0;
          let match;

          while ((match = pattern.exec(content)) !== null) {
            const upToMatch = content.substring(0, match.index);
            const lineNumber = upToMatch.split('\n').length;

            result.bottlenecks.push({
              file: relativePath,
              line: lineNumber,
              type,
              severity,
              message,
              code: lines[lineNumber - 1]?.trim().substring(0, 80)
            });

            totalIssues++;

            // Update metrics
            if (type.includes('await') || type.includes('async')) {
              result.metrics.asyncPatternIssues++;
            } else if (type.includes('cleanup') || type.includes('leak')) {
              result.metrics.memoryLeakRisks++;
            } else if (type.includes('iteration') || type.includes('loop')) {
              result.metrics.inefficientLoops++;
            } else if (type.includes('large') || type.includes('array')) {
              result.metrics.largeDataStructures++;
            } else if (type.includes('sync')) {
              result.metrics.blockingOperations++;
            }
          }
        }

        // Check for large files (complexity indicator)
        if (lines.length > 500) {
          result.improvements.push({
            file: relativePath,
            type: 'large_file',
            lines: lines.length,
            message: `Large file (${lines.length} lines) - may indicate complexity issues`
          });
        }

        // Detect excessive dependencies (large import count)
        const importCount = (content.match(/^import\s+/gm) || []).length +
                          (content.match(/require\s*\(/g) || []).length;
        if (importCount > 20) {
          result.improvements.push({
            file: relativePath,
            type: 'many_imports',
            count: importCount,
            message: `High import count (${importCount}) - consider code splitting`
          });
        }
      } catch (error) {
        continue;
      }
    }

    // Group bottlenecks by severity
    const bySeverity = {
      high: result.bottlenecks.filter(b => b.severity === 'high'),
      medium: result.bottlenecks.filter(b => b.severity === 'medium'),
      low: result.bottlenecks.filter(b => b.severity === 'low')
    };

    // Calculate score based on severity
    const severityPenalty =
      (bySeverity.high.length * 5) +
      (bySeverity.medium.length * 2) +
      (bySeverity.low.length * 0.5);

    result.score = Math.max(20, Math.round(100 - severityPenalty));

    // Limit bottlenecks in output
    result.bottlenecks = result.bottlenecks.slice(0, 50);

    console.log(`  ✓ Performance score: ${result.score}/100`);
    console.log(`  Found ${totalIssues} performance issues`);
    console.log(`    - High severity: ${bySeverity.high.length}`);
    console.log(`    - Medium severity: ${bySeverity.medium.length}`);
    console.log(`    - Low severity: ${bySeverity.low.length}`);

    return result;
  }

  async analyzeSecurity() {
    console.log('🔒 Analyzing Security...');

    const result = {
      score: 100, // Start with perfect score
      vulnerabilities: [],
      severity: 'none'
    };

    // Run npm audit (if package.json exists)
    const packageJsonPath = path.join(this.projectPath, 'package.json');
    if (fs.existsSync(packageJsonPath)) {
      try {
        const auditOutput = execSync('npm audit --json 2>/dev/null || true', {
          cwd: this.projectPath,
          encoding: 'utf-8',
          maxBuffer: 10 * 1024 * 1024
        });

        if (auditOutput && auditOutput.trim()) {
          const auditData = JSON.parse(auditOutput);

          if (auditData.metadata) {
            const { vulnerabilities } = auditData.metadata;

            const criticalCount = vulnerabilities?.critical || 0;
            const highCount = vulnerabilities?.high || 0;
            const moderateCount = vulnerabilities?.moderate || 0;

            result.vulnerabilities.push({
              type: 'dependencies',
              critical: criticalCount,
              high: highCount,
              moderate: moderateCount,
              total: criticalCount + highCount + moderateCount
            });

            // Calculate score
            if (criticalCount > 0) {
              result.severity = 'critical';
              result.score = Math.max(20, 90 - (criticalCount * 20));
            } else if (highCount > 0) {
              result.severity = 'high';
              result.score = Math.max(40, 90 - (highCount * 10));
            } else if (moderateCount > 0) {
              result.severity = 'moderate';
              result.score = Math.max(70, 90 - (moderateCount * 2));
            }
          }
        }
      } catch (error) {
        // npm audit may fail, continue with static analysis
      }
    }

    // Comprehensive static analysis for security patterns
    const jsFiles = this.findFiles(this.projectPath, ['.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs', '.vue', '.svelte']);

    const securityIssues = [];
    const securityPatterns = [
      // XSS Vulnerabilities
      { pattern: /dangerouslySetInnerHTML/g, type: 'xss_risk', severity: 'high', message: 'dangerouslySetInnerHTML - potential XSS' },
      { pattern: /\.innerHTML\s*=/g, type: 'xss_risk', severity: 'high', message: 'innerHTML assignment - potential XSS' },
      { pattern: /document\.write\(/g, type: 'xss_risk', severity: 'high', message: 'document.write() - potential XSS' },

      // Code Injection
      { pattern: /eval\s*\(/g, type: 'code_injection', severity: 'critical', message: 'eval() usage - code injection risk' },
      { pattern: /new\s+Function\s*\(/g, type: 'code_injection', severity: 'critical', message: 'new Function() - code injection risk' },
      { pattern: /setTimeout\s*\(\s*['"`]/g, type: 'code_injection', severity: 'medium', message: 'setTimeout with string - potential code injection' },
      { pattern: /setInterval\s*\(\s*['"`]/g, type: 'code_injection', severity: 'medium', message: 'setInterval with string - potential code injection' },

      // SQL Injection (for Node.js backends)
      { pattern: /query\s*\(\s*['"`].*\$\{/g, type: 'sql_injection', severity: 'critical', message: 'Template literal in SQL query - SQL injection risk' },
      { pattern: /query\s*\(\s*['"`].*\+/g, type: 'sql_injection', severity: 'critical', message: 'String concatenation in SQL query - SQL injection risk' },
      { pattern: /execute\s*\(\s*['"`].*\$\{/g, type: 'sql_injection', severity: 'critical', message: 'Template literal in execute() - SQL injection risk' },

      // Path Traversal
      { pattern: /path\.join\s*\([^)]*req\.(params|query|body)/g, type: 'path_traversal', severity: 'high', message: 'User input in path.join - path traversal risk' },
      { pattern: /fs\.(read|write|unlink|rmdir).*req\.(params|query|body)/g, type: 'path_traversal', severity: 'critical', message: 'User input in fs operation - path traversal risk' },

      // Command Injection
      { pattern: /exec\s*\([^)]*\$\{/g, type: 'command_injection', severity: 'critical', message: 'Template literal in exec() - command injection risk' },
      { pattern: /execSync\s*\([^)]*\$\{/g, type: 'command_injection', severity: 'critical', message: 'Template literal in execSync() - command injection risk' },
      { pattern: /spawn\s*\([^)]*\$\{/g, type: 'command_injection', severity: 'critical', message: 'Template literal in spawn() - command injection risk' },

      // Sensitive Data Exposure
      { pattern: /(apiKey|api_key|apiSecret|api_secret|secretKey|secret_key|password|passwd|pwd)\s*[:=]\s*['"`][^'"`]{8,}['"`]/gi, type: 'hardcoded_secret', severity: 'critical', message: 'Potential hardcoded secret' },
      { pattern: /(PRIVATE_KEY|private_key|privateKey)\s*[:=]\s*['"`]/gi, type: 'hardcoded_secret', severity: 'critical', message: 'Potential hardcoded private key' },
      { pattern: /Bearer\s+[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+/g, type: 'hardcoded_token', severity: 'critical', message: 'Hardcoded JWT token' },

      // Insecure Randomness
      { pattern: /Math\.random\s*\(\)/g, type: 'weak_random', severity: 'medium', message: 'Math.random() for security purposes - use crypto' },

      // Prototype Pollution
      { pattern: /\[['"`]__proto__['"`]\]/g, type: 'prototype_pollution', severity: 'high', message: '__proto__ access - prototype pollution risk' },
      { pattern: /Object\.assign\s*\([^,]+,\s*req\.(body|query|params)/g, type: 'prototype_pollution', severity: 'high', message: 'Object.assign with user input - prototype pollution risk' },

      // Insecure Dependencies Usage
      { pattern: /require\s*\(\s*['"`]child_process['"`]\s*\)/g, type: 'dangerous_import', severity: 'low', message: 'child_process import - review for command injection' },

      // CORS Issues
      { pattern: /Access-Control-Allow-Origin['"]\s*:\s*['"`]\*['"`]/g, type: 'cors_misconfiguration', severity: 'medium', message: 'Wildcard CORS - potential security issue' },
      { pattern: /cors\s*\(\s*\{\s*origin\s*:\s*true/g, type: 'cors_misconfiguration', severity: 'medium', message: 'Permissive CORS configuration' }
    ];

    for (const file of jsFiles) {
      try {
        const content = fs.readFileSync(file, 'utf-8');
        const relativePath = path.relative(this.projectPath, file);
        const lines = content.split('\n');

        for (const { pattern, type, severity, message } of securityPatterns) {
          // Reset regex lastIndex
          pattern.lastIndex = 0;

          let match;
          while ((match = pattern.exec(content)) !== null) {
            // Find line number
            const upToMatch = content.substring(0, match.index);
            const lineNumber = upToMatch.split('\n').length;

            securityIssues.push({
              file: relativePath,
              line: lineNumber,
              type,
              severity,
              message,
              code: lines[lineNumber - 1]?.trim().substring(0, 100)
            });
          }
        }
      } catch (error) {
        continue;
      }
    }

    if (securityIssues.length > 0) {
      // Group by severity
      const bySeverity = {
        critical: securityIssues.filter(i => i.severity === 'critical'),
        high: securityIssues.filter(i => i.severity === 'high'),
        medium: securityIssues.filter(i => i.severity === 'medium'),
        low: securityIssues.filter(i => i.severity === 'low')
      };

      result.vulnerabilities.push({
        type: 'code_patterns',
        issues: securityIssues,
        count: securityIssues.length,
        by_severity: {
          critical: bySeverity.critical.length,
          high: bySeverity.high.length,
          medium: bySeverity.medium.length,
          low: bySeverity.low.length
        }
      });

      // Score calculation based on severity
      const severityPenalty =
        (bySeverity.critical.length * 15) +
        (bySeverity.high.length * 8) +
        (bySeverity.medium.length * 3) +
        (bySeverity.low.length * 1);

      result.score = Math.max(10, result.score - severityPenalty);

      // Update overall severity
      if (bySeverity.critical.length > 0) result.severity = 'critical';
      else if (bySeverity.high.length > 0) result.severity = 'high';
      else if (bySeverity.medium.length > 0) result.severity = 'medium';
      else result.severity = 'low';
    }

    console.log(`  ✓ Security score: ${result.score}/100`);
    console.log(`  Found ${securityIssues.length} security issues`);

    return result;
  }

  async analyzeScalability() {
    console.log('📈 Analyzing Scalability...');

    const result = {
      score: 75, // Default neutral score
      coupling_issues: [],
      circular_dependencies: [],
      architecture_issues: [],
      solid_violations: [],
      metrics: {
        avgImportsPerFile: 0,
        maxImportsInFile: 0,
        totalCircularDeps: 0,
        godComponents: 0
      }
    };

    const jsFiles = this.findFiles(this.projectPath, ['.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs', '.vue', '.svelte']);

    // Build import graph for circular dependency detection
    const importGraph = new Map();
    const fileToImports = new Map();

    for (const file of jsFiles) {
      try {
        const content = fs.readFileSync(file, 'utf-8');
        const relativePath = path.relative(this.projectPath, file);
        const imports = this.extractImports(content, file);

        fileToImports.set(relativePath, imports);

        // Build adjacency list
        for (const imp of imports) {
          if (!importGraph.has(relativePath)) {
            importGraph.set(relativePath, []);
          }
          importGraph.get(relativePath).push(imp);
        }
      } catch (error) {
        continue;
      }
    }

    // Detect circular dependencies using DFS
    const circularDeps = this.detectCircularDependencies(importGraph);
    result.circular_dependencies = circularDeps;
    result.metrics.totalCircularDeps = circularDeps.length;

    // Try madge if available for more accurate detection
    try {
      const madgePath = path.join(this.projectPath, 'node_modules', '.bin', 'madge');

      if (fs.existsSync(madgePath)) {
        const output = execSync(
          `${madgePath} --circular --json "${this.projectPath}" 2>/dev/null || echo "[]"`,
          { encoding: 'utf-8', maxBuffer: 10 * 1024 * 1024 }
        );
        this._trackTool('madge', true);

        if (output && output.trim() !== '[]') {
          try {
            const madgeCircular = JSON.parse(output);
            if (Array.isArray(madgeCircular) && madgeCircular.length > 0) {
              result.circular_dependencies = madgeCircular.map(cycle => ({
                cycle,
                type: 'circular_import',
                severity: 'high',
                message: `Circular dependency detected: ${cycle.join(' → ')}`
              }));
              result.metrics.totalCircularDeps = madgeCircular.length;
            }
          } catch {}
        }
      } else {
        this._trackTool('madge', false, 'not installed');
      }
    } catch (error) {
      this._trackTool('madge', false, error.message);
      // Madge not available, use our detection
    }

    // Analyze file metrics
    let totalImports = 0;
    let maxImports = 0;

    for (const [file, imports] of fileToImports) {
      totalImports += imports.length;
      maxImports = Math.max(maxImports, imports.length);

      // High coupling detection (too many imports)
      if (imports.length > 15) {
        result.coupling_issues.push({
          file,
          importCount: imports.length,
          type: 'high_coupling',
          severity: imports.length > 25 ? 'high' : 'medium',
          message: `File imports ${imports.length} modules - consider refactoring`
        });
      }
    }

    result.metrics.avgImportsPerFile = fileToImports.size > 0
      ? Math.round(totalImports / fileToImports.size * 10) / 10
      : 0;
    result.metrics.maxImportsInFile = maxImports;

    // Check for architecture issues (god files, large components)
    for (const file of jsFiles) {
      try {
        const content = fs.readFileSync(file, 'utf-8');
        const relativePath = path.relative(this.projectPath, file);
        const lines = content.split('\n').length;

        // God file/component detection
        if (lines > 300) {
          result.architecture_issues.push({
            file: relativePath,
            lines,
            type: 'god_file',
            severity: lines > 500 ? 'high' : 'medium',
            message: `File has ${lines} lines - consider splitting`
          });
          result.metrics.godComponents++;
        }

        // Detect SOLID violations

        // Single Responsibility: Multiple export types
        const exportMatches = content.match(/export\s+(default\s+)?(class|function|const|let|var)/g) || [];
        if (exportMatches.length > 5) {
          result.solid_violations.push({
            file: relativePath,
            type: 'srp_violation',
            severity: 'medium',
            message: `File has ${exportMatches.length} exports - may violate Single Responsibility Principle`
          });
        }

        // Detect deep inheritance (more than 2 levels)
        if (content.match(/extends\s+\w+\s+extends\s+\w+/)) {
          result.solid_violations.push({
            file: relativePath,
            type: 'deep_inheritance',
            severity: 'medium',
            message: 'Deep inheritance chain detected - consider composition over inheritance'
          });
        }

        // Detect large switch/if-else chains (Open/Closed violation)
        const switchMatches = content.match(/case\s+['"`\w]+\s*:/g) || [];
        if (switchMatches.length > 10) {
          result.solid_violations.push({
            file: relativePath,
            type: 'ocp_violation',
            severity: 'medium',
            message: `Large switch statement with ${switchMatches.length} cases - consider polymorphism`
          });
        }

        // Detect Dependency Inversion Principle violations (concrete dependencies)
        // Look for class-level concrete instantiations instead of dependency injection
        const classMatches = content.matchAll(/class\s+(\w+)(?:\s+extends\s+\w+)?\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}/gs);
        for (const classMatch of classMatches) {
          const className = classMatch[1];
          const classBody = classMatch[2];

          // Find property declarations with direct instantiation (not in constructor)
          // Patterns: propertyName = new ClassName() or this.prop = new ClassName()
          const concreteDepMatches = classBody.matchAll(/(?:(?:private|public|protected|readonly)\s+)?(\w+)\s*(?::\s*\w+)?\s*=\s*new\s+(\w+)\s*\(/g);
          const concreteDeps = [];

          for (const depMatch of concreteDepMatches) {
            const depClass = depMatch[2];
            // Skip common utility classes
            if (!['Array', 'Map', 'Set', 'Date', 'Error', 'Promise', 'RegExp', 'Object', 'WeakMap', 'WeakSet'].includes(depClass)) {
              concreteDeps.push(depClass);
            }
          }

          if (concreteDeps.length >= 3) {
            result.solid_violations.push({
              file: relativePath,
              type: 'dip_violation',
              class: className,
              concreteDeps,
              severity: concreteDeps.length >= 5 ? 'high' : 'medium',
              message: `Class '${className}' has ${concreteDeps.length} concrete dependencies at class level - use dependency injection`
            });
          }
        }

        // Detect long if-elif chains (additional OCP violation pattern)
        const ifElseChainMatches = content.match(/else\s+if\s*\(/g) || [];
        if (ifElseChainMatches.length > 7) {
          result.solid_violations.push({
            file: relativePath,
            type: 'ocp_violation',
            severity: 'low',
            message: `Long if-else chain (${ifElseChainMatches.length + 1} branches) - consider polymorphism or strategy pattern`
          });
        }
      } catch (error) {
        continue;
      }
    }

    // Calculate score
    const circularPenalty = result.circular_dependencies.length * 8;
    const couplingPenalty = result.coupling_issues.length * 4;
    const architecturePenalty = result.architecture_issues.length * 5;
    const solidPenalty = result.solid_violations.length * 3;

    const totalPenalty = circularPenalty + couplingPenalty + architecturePenalty + solidPenalty;
    result.score = Math.max(20, 100 - totalPenalty);

    const totalIssues = result.circular_dependencies.length +
      result.coupling_issues.length +
      result.architecture_issues.length +
      result.solid_violations.length;

    console.log(`  ✓ Scalability score: ${result.score}/100`);
    console.log(`  Found ${totalIssues} scalability issues`);
    console.log(`    - Circular dependencies: ${result.circular_dependencies.length}`);
    console.log(`    - Coupling issues: ${result.coupling_issues.length}`);
    console.log(`    - Architecture issues: ${result.architecture_issues.length}`);
    console.log(`    - SOLID violations: ${result.solid_violations.length}`);

    return result;
  }

  extractImports(content, filePath) {
    const imports = [];
    const dir = path.dirname(filePath);

    // ES6 imports
    const es6Regex = /import\s+(?:(?:\{[^}]*\}|\*\s+as\s+\w+|\w+)\s+from\s+)?['"]([^'"]+)['"]/g;
    let match;
    while ((match = es6Regex.exec(content)) !== null) {
      const importPath = match[1];
      // Only track relative imports for circular detection
      if (importPath.startsWith('.')) {
        const resolved = this.resolveImportPath(importPath, dir);
        if (resolved) imports.push(resolved);
      }
    }

    // CommonJS requires
    const cjsRegex = /require\s*\(\s*['"]([^'"]+)['"]\s*\)/g;
    while ((match = cjsRegex.exec(content)) !== null) {
      const importPath = match[1];
      if (importPath.startsWith('.')) {
        const resolved = this.resolveImportPath(importPath, dir);
        if (resolved) imports.push(resolved);
      }
    }

    return imports;
  }

  resolveImportPath(importPath, fromDir) {
    // Try to resolve the import path to a relative path from project root
    const extensions = ['', '.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs', '.vue', '.svelte', '/index.js', '/index.ts', '/index.jsx', '/index.tsx'];

    for (const ext of extensions) {
      const fullPath = path.resolve(fromDir, importPath + ext);
      if (fs.existsSync(fullPath) && fs.statSync(fullPath).isFile()) {
        return path.relative(this.projectPath, fullPath);
      }
    }

    return null;
  }

  detectCircularDependencies(graph) {
    const circular = [];
    const visited = new Set();
    const recursionStack = new Set();
    const pathStack = [];

    const dfs = (node) => {
      visited.add(node);
      recursionStack.add(node);
      pathStack.push(node);

      const neighbors = graph.get(node) || [];
      for (const neighbor of neighbors) {
        if (!visited.has(neighbor)) {
          dfs(neighbor);
        } else if (recursionStack.has(neighbor)) {
          // Found circular dependency
          const cycleStart = pathStack.indexOf(neighbor);
          const cycle = pathStack.slice(cycleStart);
          cycle.push(neighbor); // Complete the cycle
          circular.push({
            cycle,
            type: 'circular_import',
            severity: 'high',
            message: `Circular dependency: ${cycle.join(' → ')}`
          });
        }
      }

      pathStack.pop();
      recursionStack.delete(node);
    };

    for (const node of graph.keys()) {
      if (!visited.has(node)) {
        dfs(node);
      }
    }

    return circular;
  }

  async analyzeReusability() {
    console.log('♻️  Analyzing Reusability...');

    const result = {
      score: 80, // Default good score
      duplication_percentage: 0,
      duplicate_blocks: [],
      extractable_patterns: [],
      dead_code: [],
      metrics: {
        totalLines: 0,
        duplicateLines: 0,
        deadCodeLines: 0,
        extractableCount: 0
      }
    };

    const jsFiles = this.findFiles(this.projectPath, ['.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs', '.vue', '.svelte']);
    let jscpdUsed = false;

    // Try jscpd first (most accurate)
    try {
      const jscpdPath = path.join(this.projectPath, 'node_modules', '.bin', 'jscpd');

      if (fs.existsSync(jscpdPath)) {
        const output = execSync(
          `${jscpdPath} "${this.projectPath}" --format json --silent --ignore "node_modules,dist,build,.next,coverage" || true`,
          { encoding: 'utf-8', maxBuffer: 10 * 1024 * 1024 }
        );

        if (output && output.trim()) {
          const jscpdData = JSON.parse(output);

          if (jscpdData.statistics) {
            this._trackTool('jscpd', true);
            result.duplication_percentage = jscpdData.statistics.percentage || 0;
            result.duplicate_blocks = (jscpdData.duplicates || []).map(d => ({
              firstFile: d.firstFile?.name,
              secondFile: d.secondFile?.name,
              lines: d.lines,
              tokens: d.tokens
            }));
            result.metrics.duplicateLines = jscpdData.statistics.duplicatedLines || 0;
            result.metrics.totalLines = jscpdData.statistics.total?.lines || 0;
            jscpdUsed = true;
          }
        }
      } else {
        this._trackTool('jscpd', false, 'not installed');
      }
    } catch (error) {
      this._trackTool('jscpd', false, error.message);
      // jscpd failed, use fallback
    }

    // Fallback: Hash-based duplication detection
    if (!jscpdUsed) {
      const duplicates = this.detectDuplicatesWithHashing(jsFiles);
      result.duplicate_blocks = duplicates.blocks;
      result.duplication_percentage = duplicates.percentage;
      result.metrics.duplicateLines = duplicates.duplicateLines;
      result.metrics.totalLines = duplicates.totalLines;
    }

    // Detect dead code (unused exports, unreachable code)
    const deadCode = this.detectDeadCode(jsFiles);
    result.dead_code = deadCode;
    result.metrics.deadCodeLines = deadCode.reduce((sum, d) => sum + (d.lines || 1), 0);

    // Detect extractable patterns (repeated logic that could be utility functions)
    const extractable = this.detectExtractablePatterns(jsFiles);
    result.extractable_patterns = extractable;
    result.metrics.extractableCount = extractable.length;

    // Calculate score
    let score = 100;

    // Duplication penalty
    if (result.duplication_percentage >= 10) {
      score -= 30;
    } else if (result.duplication_percentage >= 5) {
      score -= 15;
    } else if (result.duplication_percentage >= 3) {
      score -= 5;
    }

    // Dead code penalty
    score -= Math.min(20, result.dead_code.length * 2);

    // Extractable patterns (minor penalty - opportunity for improvement)
    score -= Math.min(10, result.extractable_patterns.length);

    result.score = Math.max(20, score);

    console.log(`  ✓ Reusability score: ${result.score}/100`);
    console.log(`  Code duplication: ${result.duplication_percentage.toFixed(2)}%`);
    console.log(`  Dead code items: ${result.dead_code.length}`);
    console.log(`  Extractable patterns: ${result.extractable_patterns.length}`);

    return result;
  }

  detectDuplicatesWithHashing(files) {
    const BLOCK_SIZE = 5; // Lines per block
    const MIN_DUPLICATE_LINES = 6; // Minimum lines to consider as duplicate

    const blockHashes = new Map(); // hash -> [{file, startLine}]
    let totalLines = 0;
    let duplicateLines = 0;
    const duplicateBlocks = [];

    for (const file of files) {
      try {
        const content = fs.readFileSync(file, 'utf-8');
        const lines = content.split('\n');
        totalLines += lines.length;
        const relativePath = path.relative(this.projectPath, file);

        // Create normalized blocks
        for (let i = 0; i <= lines.length - BLOCK_SIZE; i++) {
          const block = lines.slice(i, i + BLOCK_SIZE)
            .map(l => l.trim())
            .filter(l => l && !l.startsWith('//') && !l.startsWith('*'))
            .join('\n');

          if (block.length < 50) continue; // Skip trivial blocks

          const hash = this.simpleHash(block);

          if (!blockHashes.has(hash)) {
            blockHashes.set(hash, []);
          }

          const existing = blockHashes.get(hash);

          // Check if this is a new duplicate (not from same file, same position)
          const isDuplicate = existing.some(e =>
            e.file !== relativePath || Math.abs(e.startLine - i) > BLOCK_SIZE
          );

          if (isDuplicate && existing.length === 1) {
            // First time we found a duplicate for this hash
            duplicateBlocks.push({
              firstFile: existing[0].file,
              secondFile: relativePath,
              firstLine: existing[0].startLine + 1,
              secondLine: i + 1,
              lines: BLOCK_SIZE,
              type: 'duplicate_block'
            });
            duplicateLines += BLOCK_SIZE * 2; // Both occurrences
          } else if (isDuplicate) {
            duplicateLines += BLOCK_SIZE;
          }

          existing.push({ file: relativePath, startLine: i });
        }
      } catch (error) {
        continue;
      }
    }

    return {
      blocks: duplicateBlocks.slice(0, 50), // Limit to top 50
      percentage: totalLines > 0 ? (duplicateLines / totalLines) * 100 : 0,
      duplicateLines,
      totalLines
    };
  }

  simpleHash(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32bit integer
    }
    return hash.toString(16);
  }

  detectDeadCode(files) {
    const deadCode = [];
    const allExports = new Map(); // export name -> file
    const allImports = new Set(); // imported names

    // First pass: collect all exports and imports
    for (const file of files) {
      try {
        const content = fs.readFileSync(file, 'utf-8');
        const relativePath = path.relative(this.projectPath, file);

        // Collect exports
        const exportMatches = [
          ...content.matchAll(/export\s+(?:const|let|var|function|class)\s+(\w+)/g),
          ...content.matchAll(/export\s+\{\s*([^}]+)\s*\}/g),
          ...content.matchAll(/export\s+default\s+(?:function|class)?\s*(\w+)/g)
        ];

        for (const match of exportMatches) {
          const names = match[1].split(',').map(n => n.trim().split(/\s+as\s+/)[0]);
          for (const name of names) {
            if (name && name !== 'default') {
              allExports.set(name, relativePath);
            }
          }
        }

        // Collect imports and detect unused imports within this file
        const importMatches = [
          ...content.matchAll(/import\s+\{([^}]+)\}\s+from\s+['"]([^'"]+)['"]/g),
          ...content.matchAll(/import\s+(\w+)\s+from\s+['"]([^'"]+)['"]/g),
          ...content.matchAll(/import\s+\*\s+as\s+(\w+)\s+from\s+['"]([^'"]+)['"]/g)
        ];

        // Get the code body without import statements for usage checking
        const codeWithoutImports = content.replace(/^import\s+.*$/gm, '');

        for (const match of importMatches) {
          const namesStr = match[1];
          const importSource = match[2] || '';
          const names = namesStr.split(',').map(n => {
            const trimmed = n.trim();
            // Handle "name as alias" - use the alias for usage check
            const parts = trimmed.split(/\s+as\s+/);
            return {
              original: parts[0].trim(),
              local: parts.length > 1 ? parts[1].trim() : parts[0].trim()
            };
          });

          for (const { original, local } of names) {
            if (local) {
              allImports.add(original);

              // Check if this import is used in the file (excluding import statements)
              // Create a regex that matches the import name as a whole word
              const usageRegex = new RegExp(`\\b${local}\\b`);

              // Skip type-only imports and common side-effect imports
              const isTypeImport = match[0].includes('import type');
              const isSideEffectImport = !namesStr || namesStr.trim() === '';
              const isStyleImport = /\.(css|scss|sass|less|styl)['"]/.test(importSource);

              if (!isTypeImport && !isSideEffectImport && !isStyleImport) {
                if (!usageRegex.test(codeWithoutImports)) {
                  // Skip common React/framework imports that might be used implicitly
                  const implicitlyUsed = ['React', 'Fragment', 'jsx', 'jsxs', 'createElement'];
                  if (!implicitlyUsed.includes(local)) {
                    deadCode.push({
                      file: relativePath,
                      type: 'unused_import',
                      name: original,
                      localName: local !== original ? local : undefined,
                      source: importSource,
                      message: `Unused import: '${local}'${importSource ? ` from '${importSource}'` : ''}`,
                      severity: 'low'
                    });
                  }
                }
              }
            }
          }
        }

        // Detect unreachable code patterns
        const lines = content.split('\n');
        for (let i = 0; i < lines.length; i++) {
          const line = lines[i].trim();

          // Code after return/throw/break/continue (simple heuristic)
          if (/^(return|throw)\s/.test(line) && !line.endsWith('{')) {
            // Check if next non-empty line is code (not closing brace)
            for (let j = i + 1; j < Math.min(i + 5, lines.length); j++) {
              const nextLine = lines[j].trim();
              if (nextLine && !nextLine.startsWith('}') && !nextLine.startsWith('//') &&
                  !nextLine.startsWith('/*') && !nextLine.startsWith('*') &&
                  !nextLine.startsWith('case') && !nextLine.startsWith('default')) {
                deadCode.push({
                  file: relativePath,
                  line: j + 1,
                  type: 'unreachable_code',
                  message: 'Code after return/throw statement',
                  code: nextLine.substring(0, 80)
                });
                break;
              }
              if (nextLine.startsWith('}') || nextLine.startsWith('case') || nextLine.startsWith('default')) break;
            }
          }

          // Commented out code blocks (multi-line)
          if (line.startsWith('/*') && !line.includes('*/')) {
            let commentedCodeLines = 0;
            for (let j = i; j < Math.min(i + 50, lines.length); j++) {
              if (lines[j].includes('*/')) break;
              if (/[{};=()]/.test(lines[j])) commentedCodeLines++;
            }
            if (commentedCodeLines > 3) {
              deadCode.push({
                file: relativePath,
                line: i + 1,
                type: 'commented_code',
                message: 'Large block of commented-out code',
                lines: commentedCodeLines
              });
            }
          }
        }
      } catch (error) {
        continue;
      }
    }

    // Check for unused exports (not imported anywhere)
    for (const [exportName, file] of allExports) {
      // Skip common entry points and lifecycle names
      const skipNames = ['default', 'App', 'main', 'index', 'handler', 'middleware',
        'getServerSideProps', 'getStaticProps', 'getStaticPaths', 'loader', 'action',
        'GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'];

      if (!allImports.has(exportName) && !skipNames.includes(exportName)) {
        deadCode.push({
          file,
          type: 'unused_export',
          name: exportName,
          message: `Export '${exportName}' is not imported anywhere`
        });
      }
    }

    return deadCode.slice(0, 100); // Limit results
  }

  detectExtractablePatterns(files) {
    const patterns = [];
    const codePatterns = new Map(); // normalized pattern -> occurrences

    const extractableRegexes = [
      // Repeated try-catch with same structure
      { regex: /try\s*\{[^}]{20,100}\}\s*catch/g, type: 'error_handling' },
      // Repeated validation patterns
      { regex: /if\s*\(\s*!\w+\s*\)\s*\{?\s*(throw|return)/g, type: 'validation' },
      // Repeated async/await patterns
      { regex: /const\s+\w+\s*=\s*await\s+fetch\([^)]+\)/g, type: 'fetch_pattern' },
      // Repeated array operations
      { regex: /\.filter\([^)]+\)\.map\([^)]+\)/g, type: 'array_chain' },
      // Repeated object spreading
      { regex: /\{\s*\.\.\.\w+,\s*\w+:\s*[^}]+\}/g, type: 'object_spread' }
    ];

    for (const file of files) {
      try {
        const content = fs.readFileSync(file, 'utf-8');
        const relativePath = path.relative(this.projectPath, file);

        for (const { regex, type } of extractableRegexes) {
          regex.lastIndex = 0;
          let match;

          while ((match = regex.exec(content)) !== null) {
            const pattern = match[0].substring(0, 100);
            const key = `${type}:${this.simpleHash(pattern)}`;

            if (!codePatterns.has(key)) {
              codePatterns.set(key, { type, pattern, occurrences: [] });
            }

            codePatterns.get(key).occurrences.push({
              file: relativePath,
              position: match.index
            });
          }
        }
      } catch (error) {
        continue;
      }
    }

    // Find patterns with multiple occurrences
    for (const [key, data] of codePatterns) {
      if (data.occurrences.length >= 3) {
        patterns.push({
          type: data.type,
          count: data.occurrences.length,
          pattern: data.pattern.substring(0, 60) + '...',
          files: [...new Set(data.occurrences.map(o => o.file))].slice(0, 5),
          suggestion: this.getSuggestionForPattern(data.type)
        });
      }
    }

    return patterns.slice(0, 20); // Limit results
  }

  getSuggestionForPattern(type) {
    const suggestions = {
      error_handling: 'Consider creating a wrapper function for consistent error handling',
      validation: 'Consider creating validation utility functions',
      fetch_pattern: 'Consider creating an API client or custom hook',
      array_chain: 'Consider creating utility functions for common data transformations',
      object_spread: 'Consider using a merge utility or factory function'
    };
    return suggestions[type] || 'Consider extracting into a reusable utility';
  }

  findFiles(dir, extensions) {
    const files = [];
    
    const walk = (currentDir) => {
      try {
        const entries = fs.readdirSync(currentDir, { withFileTypes: true });
        
        for (const entry of entries) {
          // Skip node_modules and hidden directories
          if (entry.name === 'node_modules' || entry.name.startsWith('.')) {
            continue;
          }
          
          const fullPath = path.join(currentDir, entry.name);
          
          if (entry.isDirectory()) {
            walk(fullPath);
          } else if (extensions.some(ext => entry.name.endsWith(ext))) {
            files.push(fullPath);
          }
        }
      } catch (error) {
        // Permission denied or other errors
      }
    };
    
    walk(dir);
    return files;
  }

  calculateOverallHealth() {
    const scores = [];
    const weights = {
      maintainability: 0.35,
      performance: 0.20,
      security: 0.25,
      scalability: 0.10,
      reusability: 0.10
    };
    
    for (const [dim, weight] of Object.entries(weights)) {
      if (this.results.dimensions[dim]) {
        const dimScore = this.results.dimensions[dim].score || 70;
        scores.push(dimScore * weight);
      }
    }
    
    this.results.overall_health = Math.round(scores.reduce((a, b) => a + b, 0));
  }

  generatePriorityActions() {
    const actions = [];
    
    for (const [dim, data] of Object.entries(this.results.dimensions)) {
      const score = data.score || 0;
      
      if (score < 60) {
        actions.push({
          dimension: dim,
          priority: 'high',
          score,
          action: `Address critical ${dim} issues immediately`
        });
      } else if (score < 75) {
        actions.push({
          dimension: dim,
          priority: 'medium',
          score,
          action: `Improve ${dim} in next iteration`
        });
      }
    }
    
    // Sort by score (lowest first)
    actions.sort((a, b) => a.score - b.score);
    
    this.results.priority_actions = actions.slice(0, 5);
  }
}

async function main() {
  const { values, positionals } = parseArgs({
    options: {
      dimensions: {
        type: 'string',
        default: 'all'
      },
      output: {
        type: 'string',
        default: './multidim-analysis.json'
      },
      all: {
        type: 'boolean',
        default: false
      }
    },
    allowPositionals: true
  });
  
  if (positionals.length === 0) {
    console.error('Usage: node analyze_multidim.js <project-path> [options]');
    process.exit(1);
  }
  
  const projectPath = positionals[0];
  
  // Parse dimensions
  let dimensions;
  if (values.all || values.dimensions === 'all') {
    dimensions = ['maintainability', 'performance', 'security', 'scalability', 'reusability'];
  } else {
    dimensions = values.dimensions.split(',').map(d => d.trim());
  }
  
  // Check dependencies
  console.log('\n🔍 Checking analysis tools...');
  checkDependencies(dimensions);
  
  // Run analysis
  const analyzer = new MultiDimensionalAnalyzer(projectPath, dimensions);
  const results = await analyzer.analyze();
  
  // Save results
  const outputDir = path.dirname(values.output);
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }
  
  fs.writeFileSync(values.output, JSON.stringify(results, null, 2));
  
  console.log('\n✅ Analysis complete!');
  console.log(`📊 Overall Health Score: ${results.overall_health}/100`);
  console.log(`📄 Full report: ${values.output}`);
  
  // Print priority actions
  if (results.priority_actions.length > 0) {
    console.log('\n🎯 Priority Actions:');
    for (const action of results.priority_actions) {
      console.log(`  [${action.priority.toUpperCase()}] ${action.action} (score: ${action.score})`);
    }
  }
  
  process.exit(0);
}

main().catch(error => {
  console.error('Error:', error);
  process.exit(1);
});
