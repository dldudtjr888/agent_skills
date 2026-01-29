#!/usr/bin/env node
/**
 * JavaScript/TypeScript Code Analysis Script for Refactoring
 * 
 * Performs comprehensive static analysis on Next.js/React projects to identify
 * refactoring opportunities, code smells, and technical debt.
 * 
 * Dependencies:
 *   npm install -g eslint @typescript-eslint/parser @typescript-eslint/eslint-plugin
 */

const fs = require('fs');
const path = require('path');
const {execSync} = require('child_process');

class AnalysisIssue {
  constructor(data) {
    this.severity = data.severity; // critical, high, medium, low
    this.category = data.category; // complexity, smell, maintainability, architecture, performance
    this.title = data.title;
    this.description = data.description;
    this.file = data.file;
    this.line = data.line;
    this.endLine = data.endLine;
    this.suggestedRefactoring = data.suggestedRefactoring;
    this.automated = data.automated;
    this.risk = data.risk; // high, medium, low
    this.impact = data.impact; // high, medium, low
    this.metrics = data.metrics || {};
  }
}

class JavaScriptAnalyzer {
  constructor(projectPath, config) {
    this.projectPath = path.resolve(projectPath);
    this.config = config;
    this.issues = [];
    this.metrics = {
      totalFiles: 0,
      totalLines: 0,
      avgComplexity: 0,
      componentCount: 0,
      hookCount: 0
    };
  }

  async analyze() {
    console.log(`🔍 Analyzing JavaScript/TypeScript project: ${this.projectPath}`);
    
    const files = this.findJavaScriptFiles();
    this.metrics.totalFiles = files.length;
    
    console.log(`📁 Found ${files.length} JavaScript/TypeScript files`);
    
    // Phase 1: ESLint Analysis
    console.log('\n🔧 Running ESLint analysis...');
    const eslintIssues = await this.analyzeWithESLint(files);
    this.issues.push(...eslintIssues);
    
    // Phase 2: React-Specific Analysis
    console.log('⚛️  Analyzing React components...');
    const reactIssues = this.analyzeReactPatterns(files);
    this.issues.push(...reactIssues);
    
    // Phase 3: Next.js-Specific Analysis
    console.log('🚀 Analyzing Next.js patterns...');
    const nextjsIssues = this.analyzeNextJsPatterns(files);
    this.issues.push(...nextjsIssues);
    
    // Phase 4: Code Complexity
    console.log('🧮 Analyzing code complexity...');
    const complexityIssues = this.analyzeComplexity(files);
    this.issues.push(...complexityIssues);
    
    // Generate report
    return this.generateReport();
  }

  findJavaScriptFiles() {
    const files = [];
    const excludeDirs = new Set(['node_modules', '.next', 'dist', 'build', '.git', 'coverage']);
    const extensions = new Set(['.js', '.jsx', '.ts', '.tsx']);
    
    const walk = (dir) => {
      const entries = fs.readdirSync(dir, {withFileTypes: true});
      
      for (const entry of entries) {
        const fullPath = path.join(dir, entry.name);
        
        if (entry.isDirectory()) {
          if (!excludeDirs.has(entry.name)) {
            walk(fullPath);
          }
        } else if (entry.isFile()) {
          const ext = path.extname(entry.name);
          if (extensions.has(ext)) {
            files.push(fullPath);
          }
        }
      }
    };
    
    walk(this.projectPath);
    return files;
  }

  async analyzeWithESLint(files) {
    const issues = [];
    
    // Check if ESLint is configured
    const eslintConfigPath = path.join(this.projectPath, 'eslint.config.mjs');
    const hasEslintConfig = fs.existsSync(eslintConfigPath) || 
                           fs.existsSync(path.join(this.projectPath, '.eslintrc.json'));
    
    if (!hasEslintConfig) {
      console.log('⚠️  No ESLint configuration found. Skipping ESLint analysis.');
      return issues;
    }
    
    try {
      // Run ESLint on project
      const result = execSync(
        `cd ${this.projectPath} && npx eslint . --format json`,
        {encoding: 'utf-8', stdio: ['pipe', 'pipe', 'pipe']}
      );
      
      const eslintResults = JSON.parse(result);
      
      for (const fileResult of eslintResults) {
        for (const message of fileResult.messages) {
          const severity = this.mapESLintSeverity(message.severity);
          const category = this.categorizeESLintRule(message.ruleId);
          
          issues.push(new AnalysisIssue({
            severity,
            category,
            title: message.message,
            description: `ESLint rule: ${message.ruleId || 'unknown'}`,
            file: path.relative(this.projectPath, fileResult.filePath),
            line: message.line,
            endLine: message.endLine || message.line,
            suggestedRefactoring: this.getSuggestedRefactoring(message.ruleId),
            automated: this.canAutoFix(message.ruleId),
            risk: 'low',
            impact: severity === 'critical' || severity === 'high' ? 'high' : 'medium',
            metrics: {ruleId: message.ruleId, fixable: message.fix !== undefined}
          }));
        }
      }
    } catch (error) {
      // ESLint might exit with error if there are issues
      if (error.stdout) {
        try {
          const eslintResults = JSON.parse(error.stdout);
          // Process results same as above
          for (const fileResult of eslintResults) {
            for (const message of fileResult.messages) {
              const severity = this.mapESLintSeverity(message.severity);
              const category = this.categorizeESLintRule(message.ruleId);
              
              issues.push(new AnalysisIssue({
                severity,
                category,
                title: message.message,
                description: `ESLint rule: ${message.ruleId || 'unknown'}`,
                file: path.relative(this.projectPath, fileResult.filePath),
                line: message.line,
                endLine: message.endLine || message.line,
                suggestedRefactoring: this.getSuggestedRefactoring(message.ruleId),
                automated: this.canAutoFix(message.ruleId),
                risk: 'low',
                impact: severity === 'critical' || severity === 'high' ? 'high' : 'medium',
                metrics: {ruleId: message.ruleId, fixable: message.fix !== undefined}
              }));
            }
          }
        } catch (parseError) {
          console.warn('⚠️  Could not parse ESLint output');
        }
      }
    }
    
    return issues;
  }

  mapESLintSeverity(eslintSeverity) {
    if (eslintSeverity === 2) return 'high';
    if (eslintSeverity === 1) return 'medium';
    return 'low';
  }

  categorizeESLintRule(ruleId) {
    if (!ruleId) return 'smell';
    
    if (ruleId.includes('complexity') || ruleId.includes('max-depth')) return 'complexity';
    if (ruleId.includes('react-hooks') || ruleId.includes('jsx')) return 'smell';
    if (ruleId.includes('import') || ruleId.includes('dependency')) return 'architecture';
    if (ruleId.includes('performance') || ruleId.includes('memo')) return 'performance';
    
    return 'maintainability';
  }

  getSuggestedRefactoring(ruleId) {
    const refactoringMap = {
      'complexity': 'extract_function',
      'max-lines-per-function': 'extract_function',
      'max-depth': 'decompose_conditional',
      'react-hooks/exhaustive-deps': 'fix_hook_dependencies',
      'react/jsx-no-bind': 'use_callback',
      '@next/next/no-img-element': 'use_next_image'
    };
    
    return refactoringMap[ruleId] || 'manual_review';
  }

  canAutoFix(ruleId) {
    const autoFixable = [
      'import/order',
      'react/jsx-indent',
      'prettier/prettier',
      'semi',
      'quotes'
    ];
    
    return autoFixable.some(rule => ruleId && ruleId.includes(rule));
  }

  analyzeReactPatterns(files) {
    const issues = [];
    
    for (const file of files) {
      try {
        const content = fs.readFileSync(file, 'utf-8');
        const relativePath = path.relative(this.projectPath, file);
        
        // Detect large components
        const componentMatch = content.match(/(?:function|const)\s+\w+.*?(?:export\s+)?(?:default\s+)?[{(]/g);
        if (componentMatch) {
          const lines = content.split('\n').length;
          
          if (lines > this.config.maxComponentLength) {
            issues.push(new AnalysisIssue({
              severity: 'high',
              category: 'smell',
              title: `Large component: ${lines} lines`,
              description: `Component is ${lines} lines, should be < ${this.config.maxComponentLength}`,
              file: relativePath,
              line: 1,
              endLine: lines,
              suggestedRefactoring: 'extract_component',
              automated: false,
              risk: 'medium',
              impact: 'high',
              metrics: {length: lines}
            }));
          }
        }
        
        // Detect missing React.memo on expensive components
        if (content.includes('useState') || content.includes('useEffect')) {
          if (!content.includes('React.memo') && !content.includes('memo(')) {
            const lines = content.split('\n').length;
            if (lines > 50) {
              issues.push(new AnalysisIssue({
                severity: 'medium',
                category: 'performance',
                title: 'Consider memoization',
                description: 'Large component with hooks should consider React.memo',
                file: relativePath,
                line: 1,
                endLine: lines,
                suggestedRefactoring: 'add_memo',
                automated: true,
                risk: 'low',
                impact: 'medium',
                metrics: {length: lines}
              }));
            }
          }
        }
        
        // Detect props drilling (many props passed through)
        const propsMatch = content.match(/\{([^}]+)\}/g);
        if (propsMatch) {
          const propsCount = propsMatch.filter(m => m.includes(',')).length;
          if (propsCount > 5) {
            issues.push(new AnalysisIssue({
              severity: 'medium',
              category: 'smell',
              title: `Props drilling detected: ${propsCount} props`,
              description: 'Consider using Context or state management',
              file: relativePath,
              line: 1,
              endLine: 1,
              suggestedRefactoring: 'introduce_context',
              automated: false,
              risk: 'medium',
              impact: 'high',
              metrics: {propsCount}
            }));
          }
        }
        
      } catch (error) {
        console.warn(`⚠️  Error analyzing React patterns in ${file}: ${error.message}`);
      }
    }
    
    return issues;
  }

  analyzeNextJsPatterns(files) {
    const issues = [];
    
    // Check for Next.js specific patterns
    const appDirExists = fs.existsSync(path.join(this.projectPath, 'app'));
    const pagesDirExists = fs.existsSync(path.join(this.projectPath, 'pages'));
    
    for (const file of files) {
      try {
        const content = fs.readFileSync(file, 'utf-8');
        const relativePath = path.relative(this.projectPath, file);
        
        // Check for missing 'use client' directive when needed
        if (appDirExists && relativePath.startsWith('app/')) {
          const hasClientCode = content.includes('useState') || 
                               content.includes('useEffect') ||
                               content.includes('onClick') ||
                               content.includes('onSubmit');
          
          if (hasClientCode && !content.includes("'use client'") && !content.includes('"use client"')) {
            issues.push(new AnalysisIssue({
              severity: 'high',
              category: 'architecture',
              title: "Missing 'use client' directive",
              description: 'Component uses client-side features but lacks use client directive',
              file: relativePath,
              line: 1,
              endLine: 1,
              suggestedRefactoring: 'add_use_client',
              automated: true,
              risk: 'low',
              impact: 'high',
              metrics: {}
            }));
          }
        }
        
        // Check for inefficient image usage
        if (content.includes('<img') && !content.includes('next/image')) {
          issues.push(new AnalysisIssue({
            severity: 'medium',
            category: 'performance',
            title: 'Using <img> instead of next/image',
            description: 'Consider using Next.js Image component for optimization',
            file: relativePath,
            line: 1,
            endLine: 1,
            suggestedRefactoring: 'use_next_image',
            automated: true,
            risk: 'low',
            impact: 'medium',
            metrics: {}
          }));
        }
        
        // Check for client components in Server Component tree
        if (appDirExists && content.includes("'use client'")) {
          // This is a simplified check - in production, you'd analyze the component tree
          issues.push(new AnalysisIssue({
            severity: 'low',
            category: 'architecture',
            title: 'Review client/server boundary',
            description: 'Ensure client component is necessary at this boundary',
            file: relativePath,
            line: 1,
            endLine: 1,
            suggestedRefactoring: 'optimize_server_client_boundary',
            automated: false,
            risk: 'low',
            impact: 'medium',
            metrics: {}
          }));
        }

        // Check for Pages Router migration opportunity
        if (pagesDirExists && !appDirExists && relativePath.startsWith('pages/')) {
          issues.push(new AnalysisIssue({
            severity: 'low',
            category: 'architecture',
            title: 'Consider App Router migration',
            description: 'Project uses Pages Router. Consider migrating to App Router for improved performance and features.',
            file: relativePath,
            line: 1,
            endLine: 1,
            suggestedRefactoring: 'migrate_to_app_router',
            automated: false,
            risk: 'high',
            impact: 'high',
            metrics: { routerType: 'pages' }
          }));
        }

      } catch (error) {
        console.warn(`⚠️  Error analyzing Next.js patterns in ${file}: ${error.message}`);
      }
    }
    
    return issues;
  }

  analyzeComplexity(files) {
    const issues = [];
    
    for (const file of files) {
      try {
        const content = fs.readFileSync(file, 'utf-8');
        const relativePath = path.relative(this.projectPath, file);
        
        // Simple complexity check based on control flow keywords
        const lines = content.split('\n');
        let currentFunction = null;
        let functionStartLine = 0;
        let complexity = 0;
        
        for (let i = 0; i < lines.length; i++) {
          const line = lines[i];
          
          // Detect function start
          if (/(?:function|const|let|var)\s+\w+.*?[{(]/.test(line) || /=>\s*{/.test(line)) {
            if (currentFunction && complexity > this.config.maxComplexity) {
              issues.push(new AnalysisIssue({
                severity: complexity > 20 ? 'critical' : 'high',
                category: 'complexity',
                title: `High complexity: ${complexity}`,
                description: `Function has complexity ${complexity}, threshold is ${this.config.maxComplexity}`,
                file: relativePath,
                line: functionStartLine,
                endLine: i,
                suggestedRefactoring: 'extract_function',
                automated: true,
                risk: 'low',
                impact: 'high',
                metrics: {complexity}
              }));
            }
            
            currentFunction = line;
            functionStartLine = i + 1;
            complexity = 1; // Base complexity
          }
          
          // Count complexity-increasing keywords
          if (/\b(if|for|while|case|catch|\&\&|\|\||\?)\b/.test(line)) {
            complexity++;
          }
        }
        
      } catch (error) {
        console.warn(`⚠️  Error analyzing complexity of ${file}: ${error.message}`);
      }
    }
    
    return issues;
  }

  generateReport() {
    // Sort issues by priority
    const priorityOrder = {critical: 0, high: 1, medium: 2, low: 3};
    this.issues.sort((a, b) => {
      if (priorityOrder[a.severity] !== priorityOrder[b.severity]) {
        return priorityOrder[a.severity] - priorityOrder[b.severity];
      }
      return a.file.localeCompare(b.file);
    });
    
    // Calculate summary statistics
    const severityCounts = {critical: 0, high: 0, medium: 0, low: 0};
    const categoryCounts = {};
    let automatedCount = 0;
    
    for (const issue of this.issues) {
      severityCounts[issue.severity]++;
      categoryCounts[issue.category] = (categoryCounts[issue.category] || 0) + 1;
      if (issue.automated) automatedCount++;
    }
    
    const report = {
      projectPath: this.projectPath,
      analysisVersion: '1.0.0',
      summary: {
        totalIssues: this.issues.length,
        bySeverity: severityCounts,
        byCategory: categoryCounts,
        automatedCount,
        manualCount: this.issues.length - automatedCount
      },
      metrics: this.metrics,
      issues: this.issues,
      recommendations: this.generateRecommendations()
    };
    
    return report;
  }

  generateRecommendations() {
    const recommendations = [];
    
    const criticalCount = this.issues.filter(i => i.severity === 'critical').length;
    if (criticalCount > 0) {
      recommendations.push(`Address ${criticalCount} critical issues immediately - these represent major technical debt`);
    }
    
    const performanceIssues = this.issues.filter(i => i.category === 'performance');
    if (performanceIssues.length > 5) {
      recommendations.push(`Optimize performance - ${performanceIssues.length} issues affecting user experience`);
    }
    
    const automatedIssues = this.issues.filter(i => i.automated);
    if (automatedIssues.length > 0) {
      recommendations.push(`Run automated refactoring on ${automatedIssues.length} issues that can be safely automated`);
    }
    
    return recommendations;
  }
}

async function main() {
  const args = process.argv.slice(2);
  
  if (args.length === 0) {
    console.error('Usage: node analyze_js.js <project-path> [options]');
    console.error('Options:');
    console.error('  --output, -o <path>        Output file for analysis report (default: ./refactoring-analysis.json)');
    console.error('  --max-complexity <n>       Maximum allowed complexity (default: 10)');
    console.error('  --max-component-length <n> Maximum component length (default: 200)');
    process.exit(1);
  }
  
  const projectPath = args[0];
  let outputPath = './refactoring-analysis.json';
  let maxComplexity = 10;
  let maxComponentLength = 200;
  
  // Parse options
  for (let i = 1; i < args.length; i++) {
    if ((args[i] === '--output' || args[i] === '-o') && i + 1 < args.length) {
      outputPath = args[++i];
    } else if (args[i] === '--max-complexity' && i + 1 < args.length) {
      maxComplexity = parseInt(args[++i]);
    } else if (args[i] === '--max-component-length' && i + 1 < args.length) {
      maxComponentLength = parseInt(args[++i]);
    }
  }
  
  const config = {maxComplexity, maxComponentLength};
  
  const analyzer = new JavaScriptAnalyzer(projectPath, config);
  const report = await analyzer.analyze();
  
  // Write report
  const outputDir = path.dirname(outputPath);
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, {recursive: true});
  }
  
  fs.writeFileSync(outputPath, JSON.stringify(report, null, 2));
  
  console.log('\n✅ Analysis complete!');
  console.log(`📊 Found ${report.summary.totalIssues} issues`);
  console.log(`   - Critical: ${report.summary.bySeverity.critical}`);
  console.log(`   - High: ${report.summary.bySeverity.high}`);
  console.log(`   - Medium: ${report.summary.bySeverity.medium}`);
  console.log(`   - Low: ${report.summary.bySeverity.low}`);
  console.log(`\n🤖 ${report.summary.automatedCount} issues can be automatically refactored`);
  console.log(`📝 Report saved to: ${outputPath}`);
  
  if (report.recommendations.length > 0) {
    console.log('\n💡 Recommendations:');
    for (const rec of report.recommendations) {
      console.log(`   - ${rec}`);
    }
  }
}

main().catch(error => {
  console.error('Error:', error);
  process.exit(1);
});
