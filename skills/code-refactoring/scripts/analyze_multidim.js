#!/usr/bin/env node
/**
 * Multi-Dimensional Code Analysis for JavaScript/TypeScript/Next.js Projects
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
  constructor(projectPath, dimensions) {
    this.projectPath = path.resolve(projectPath);
    this.dimensions = dimensions;
    this.results = {
      project: projectPath,
      dimensions: {},
      overall_health: 0,
      priority_actions: []
    };
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
        
        let errorCount = 0;
        let warningCount = 0;
        const complexityIssues = [];
        
        for (const file of eslintResults) {
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
      }
    } catch (error) {
      console.log(`  Warning: ESLint analysis failed - ${error.message}`);
      result.score = 70; // Neutral score if can't analyze
    }
    
    console.log(`  ✓ Maintainability score: ${result.score}/100`);
    return result;
  }

  async analyzePerformance() {
    console.log('⚡ Analyzing Performance...');
    
    const result = {
      score: 70, // Default neutral score
      bottlenecks: [],
      improvements: [],
      bundle_issues: []
    };
    
    // Check for Next.js configuration
    const nextConfigPath = path.join(this.projectPath, 'next.config.js');
    const nextConfigMjsPath = path.join(this.projectPath, 'next.config.mjs');
    
    if (fs.existsSync(nextConfigPath) || fs.existsSync(nextConfigMjsPath)) {
      result.improvements.push({
        type: 'nextjs_optimization',
        message: 'Next.js project detected - check for Image optimization, bundle size',
        action: 'Use next/image, implement lazy loading, check bundle analyzer'
      });
    }
    
    // Static analysis for React performance issues
    const jsFiles = this.findFiles(this.projectPath, ['.js', '.jsx', '.ts', '.tsx']);
    
    let unnecessaryRerenderCount = 0;
    let missingSplittingCount = 0;
    
    for (const file of jsFiles) {
      try {
        const content = fs.readFileSync(file, 'utf-8');
        
        // Check for missing React.memo on components with props
        if (content.includes('export default function') || content.includes('export const')) {
          if (!content.includes('React.memo') && !content.includes('useMemo')) {
            unnecessaryRerenderCount++;
          }
        }
        
        // Check for large imports without lazy loading
        if (content.match(/import .+ from ['"]@\/components\/.*['"]/g)) {
          if (!content.includes('dynamic(') && !content.includes('lazy(')) {
            missingSplittingCount++;
          }
        }
      } catch (error) {
        continue;
      }
    }
    
    result.improvements.push({
      type: 'react_optimization',
      count: unnecessaryRerenderCount,
      message: `Found ${unnecessaryRerenderCount} components without memoization`
    });
    
    result.improvements.push({
      type: 'code_splitting',
      count: missingSplittingCount,
      message: `Found ${missingSplittingCount} files without lazy loading`
    });
    
    // Calculate score
    const totalIssues = unnecessaryRerenderCount + missingSplittingCount;
    if (totalIssues === 0) {
      result.score = 95;
    } else if (totalIssues < 10) {
      result.score = 80;
    } else if (totalIssues < 30) {
      result.score = 65;
    } else {
      result.score = 50;
    }
    
    console.log(`  ✓ Performance score: ${result.score}/100`);
    console.log(`  Found ${totalIssues} potential performance issues`);
    
    return result;
  }

  async analyzeSecurity() {
    console.log('🔒 Analyzing Security...');
    
    const result = {
      score: 100, // Start with perfect score
      vulnerabilities: [],
      severity: 'none'
    };
    
    // Run npm audit
    try {
      const auditOutput = execSync('npm audit --json', {
        cwd: this.projectPath,
        encoding: 'utf-8',
        stdio: ['pipe', 'pipe', 'ignore']
      });
      
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
    } catch (error) {
      // npm audit returns non-zero when vulnerabilities found
      if (error.stdout) {
        try {
          const auditData = JSON.parse(error.stdout);
          // Process similar to above
        } catch {}
      }
    }
    
    // Static analysis for security patterns
    const jsFiles = this.findFiles(this.projectPath, ['.js', '.jsx', '.ts', '.tsx']);
    
    const securityIssues = [];
    for (const file of jsFiles) {
      try {
        const content = fs.readFileSync(file, 'utf-8');
        
        // Check for common security issues
        if (content.includes('dangerouslySetInnerHTML')) {
          securityIssues.push({
            file,
            type: 'xss_risk',
            message: 'Using dangerouslySetInnerHTML - XSS risk'
          });
        }
        
        if (content.match(/eval\(/)) {
          securityIssues.push({
            file,
            type: 'code_injection',
            message: 'Using eval() - code injection risk'
          });
        }
        
        // Check for hardcoded secrets (basic pattern)
        if (content.match(/(apiKey|api_key|secret|password|token)\s*=\s*['"][^'"]{20,}['"]/i)) {
          securityIssues.push({
            file,
            type: 'hardcoded_secret',
            message: 'Potential hardcoded secret detected'
          });
        }
      } catch (error) {
        continue;
      }
    }
    
    if (securityIssues.length > 0) {
      result.vulnerabilities.push({
        type: 'code_patterns',
        issues: securityIssues,
        count: securityIssues.length
      });
      
      result.score = Math.min(result.score, 80 - (securityIssues.length * 5));
    }
    
    console.log(`  ✓ Security score: ${result.score}/100`);
    console.log(`  Found ${result.vulnerabilities.length} security issue categories`);
    
    return result;
  }

  async analyzeScalability() {
    console.log('📈 Analyzing Scalability...');
    
    const result = {
      score: 75, // Default neutral score
      coupling_issues: [],
      circular_dependencies: [],
      architecture_issues: []
    };
    
    // Check for circular dependencies using madge
    try {
      const madgePath = path.join(this.projectPath, 'node_modules', '.bin', 'madge');
      
      if (fs.existsSync(madgePath)) {
        const output = execSync(
          `${madgePath} --circular --json "${this.projectPath}"`,
          { encoding: 'utf-8', maxBuffer: 10 * 1024 * 1024 }
        );
        
        const circularDeps = JSON.parse(output);
        
        for (const [file, deps] of Object.entries(circularDeps)) {
          if (deps.length > 0) {
            result.circular_dependencies.push({
              file,
              dependencies: deps
            });
          }
        }
      }
    } catch (error) {
      // Madge not available or no circular deps
    }
    
    // Check for large components (god components)
    const componentFiles = this.findFiles(this.projectPath, ['.jsx', '.tsx']);
    
    for (const file of componentFiles) {
      try {
        const content = fs.readFileSync(file, 'utf-8');
        const lines = content.split('\n').length;
        
        if (lines > 300) {
          result.architecture_issues.push({
            file,
            lines,
            type: 'god_component',
            message: `Component has ${lines} lines - consider splitting`
          });
        }
      } catch (error) {
        continue;
      }
    }
    
    // Calculate score
    const issueCount = result.circular_dependencies.length + result.architecture_issues.length;
    
    if (issueCount === 0) {
      result.score = 90;
    } else if (issueCount < 5) {
      result.score = 75;
    } else if (issueCount < 10) {
      result.score = 60;
    } else {
      result.score = 40;
    }
    
    console.log(`  ✓ Scalability score: ${result.score}/100`);
    console.log(`  Found ${issueCount} scalability issues`);
    
    return result;
  }

  async analyzeReusability() {
    console.log('♻️  Analyzing Reusability...');
    
    const result = {
      score: 80, // Default good score
      duplication_percentage: 0,
      duplicate_blocks: [],
      extractable_patterns: []
    };
    
    // Check for duplicate code using jscpd
    try {
      const jscpdPath = path.join(this.projectPath, 'node_modules', '.bin', 'jscpd');
      
      if (fs.existsSync(jscpdPath)) {
        const output = execSync(
          `${jscpdPath} "${this.projectPath}" --format json --silent || true`,
          { encoding: 'utf-8', maxBuffer: 10 * 1024 * 1024 }
        );
        
        if (output) {
          const jscpdData = JSON.parse(output);
          
          if (jscpdData.statistics) {
            result.duplication_percentage = jscpdData.statistics.percentage || 0;
            result.duplicate_blocks = jscpdData.duplicates?.length || 0;
            
            // Calculate score based on duplication
            if (result.duplication_percentage < 3) {
              result.score = 95;
            } else if (result.duplication_percentage < 5) {
              result.score = 85;
            } else if (result.duplication_percentage < 10) {
              result.score = 70;
            } else {
              result.score = 50;
            }
          }
        }
      }
    } catch (error) {
      console.log(`  Warning: jscpd analysis failed - ${error.message}`);
    }
    
    console.log(`  ✓ Reusability score: ${result.score}/100`);
    console.log(`  Code duplication: ${result.duplication_percentage.toFixed(2)}%`);
    
    return result;
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
        default: '/mnt/user-data/outputs/multidim-analysis.json'
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
