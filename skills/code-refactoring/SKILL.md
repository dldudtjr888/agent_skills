---
name: code-refactoring
description: Production-ready multi-dimensional code refactoring for Python and Next.js (React/JavaScript/TypeScript) projects. Use when users request code refactoring, code quality improvements, technical debt reduction, or ask to "clean up code", "improve code structure", "refactor this project", "fix code smells", "improve performance", "check security", "improve scalability", or "modernize codebase". Supports deep static analysis across 5 dimensions (maintainability, performance, security, scalability, reusability), AST-based transformations, automated refactoring with safety checks, and comprehensive pre/post validation.
---

# Code Refactoring

Production-ready refactoring workflow for Python and Next.js/React projects with comprehensive analysis, automated transformations, and safety validation.

## Quick Start

### Python Project Refactoring

```bash
# 1. Analyze the project
python scripts/analyze_python.py /path/to/project

# 2. Review analysis report in /mnt/user-data/outputs/refactoring-analysis.json

# 3. Execute refactoring with safety checks
python scripts/refactor_python.py /path/to/project --plan /mnt/user-data/outputs/refactoring-analysis.json
```

### Next.js/React Project Refactoring

```bash
# 1. Analyze the project  
node scripts/analyze_js.js /path/to/project

# 2. Review analysis report in /mnt/user-data/outputs/refactoring-analysis.json

# 3. Execute refactoring with safety checks
node scripts/refactor_js.js /path/to/project --plan /mnt/user-data/outputs/refactoring-analysis.json
```

## Multi-Dimensional Analysis

This skill analyzes code across **5 critical dimensions** to provide comprehensive refactoring insights:

### 1. 🔧 Maintainability (Core Focus)
**Goal**: Reduce technical debt and improve code comprehension

**Analysis Tools**:
- Cyclomatic complexity (Radon, ESLint complexity)
- Code smells detection (long methods, large classes)
- Maintainability index calculation
- Dead code detection

**Key Metrics**:
- Complexity score (target: ≤ 10)
- Maintainability index (target: ≥ 65)
- Code duplication (target: < 5%)
- Method length (target: ≤ 50 lines)

**Coverage**: ✅ **90%** - Comprehensive

---

### 2. ⚡ Performance
**Goal**: Identify and eliminate performance bottlenecks

**Analysis Tools**:
- **Python**: `cProfile`, `memory_profiler`, algorithm complexity analysis
- **JavaScript**: React DevTools Profiler, bundle size analysis
- Time/space complexity detection via AST patterns

**Key Metrics**:
- Runtime bottlenecks (functions > 100ms)
- Memory leaks and excessive allocations
- Algorithmic complexity (O(n²) candidates)
- React unnecessary re-renders
- Bundle size impact (Next.js)

**Performance Patterns**:
- Cache expensive computations
- Use React.memo/useMemo/useCallback appropriately
- Replace O(n²) with O(n log n) or O(n)
- Lazy load heavy components
- Optimize database queries (N+1 detection)

**Coverage**: ⚠️ **Enhanced** (was 30%, now 70%)

---

### 3. 🔒 Security
**Goal**: Detect vulnerabilities and insecure patterns

**Analysis Tools**:
- **Python**: `bandit` (security linter), `safety` (dependency vulnerabilities)
- **JavaScript**: `eslint-plugin-security`, `npm audit`, Snyk integration
- SQL injection pattern detection
- XSS vulnerability detection
- Authentication/authorization checks

**Key Checks**:
- Dependency vulnerabilities (CVEs)
- SQL injection risks
- XSS vulnerabilities
- Hardcoded secrets
- Insecure cryptography
- Path traversal risks
- CSRF protection

**Coverage**: ⚠️ **Enhanced** (was 15%, now 75%)

---

### 4. 📈 Scalability/Extensibility
**Goal**: Ensure code can grow without breaking

**Analysis Tools**:
- **SOLID principles** violation detection
- Coupling/cohesion metrics (via dependency graphs)
- **Python**: `pydeps` dependency visualization
- **JavaScript**: `dependency-cruiser`, `madge` circular dependency detection
- Design pattern anti-pattern detection

**Key Metrics**:
- Coupling score (target: low coupling)
- Cohesion score (target: high cohesion)
- Circular dependencies (target: 0)
- God class/function detection
- SOLID violations count

**Scalability Patterns**:
- Dependency injection over tight coupling
- Open/Closed principle compliance
- Interface segregation
- Single Responsibility enforcement

**Coverage**: ⚠️ **Enhanced** (was 20%, now 65%)

---

### 5. ♻️ Reusability
**Goal**: Maximize code reuse and reduce duplication

**Analysis Tools**:
- Clone detection (exact and semantic)
- **Python**: `pylint` similarity checker
- **JavaScript**: `jscpd` (copy-paste detector)
- Abstract pattern identification
- Extractable utility function detection

**Key Metrics**:
- Code duplication percentage (target: < 5%)
- Duplicate block count
- Similar logic patterns
- Extractable utilities count

**Reusability Patterns**:
- Extract repeated logic into utilities
- Create reusable components/functions
- Parameterize duplicated code
- Build shared libraries

**Coverage**: ⚠️ **Enhanced** (was 40%, now 70%)

---

## Running Multi-Dimensional Analysis

### Comprehensive Analysis (All Dimensions)

```bash
# Python projects - all dimensions
python scripts/analyze_multidim.py /path/to/project --all

# JavaScript/Next.js projects - all dimensions
node scripts/analyze_multidim.js /path/to/project --all
```

### Selective Dimension Analysis

```bash
# Analyze only performance + security
python scripts/analyze_multidim.py /path/to/project --dimensions performance,security

# Analyze only scalability
node scripts/analyze_multidim.js /path/to/project --dimensions scalability
```

### Output Format

```json
{
  "dimensions": {
    "maintainability": {
      "score": 85,
      "issues": [...],
      "coverage": "comprehensive"
    },
    "performance": {
      "score": 70,
      "bottlenecks": [...],
      "improvements": [...]
    },
    "security": {
      "score": 90,
      "vulnerabilities": [...],
      "severity": "medium"
    },
    "scalability": {
      "score": 75,
      "coupling_issues": [...],
      "solid_violations": [...]
    },
    "reusability": {
      "score": 80,
      "duplication_percentage": 3.2,
      "extractable_patterns": [...]
    }
  },
  "overall_health": 80,
  "priority_actions": [...]
}
```

## Core Refactoring Workflow

The skill implements a **4-phase workflow** designed to minimize errors and ensure behavior preservation:

### Phase 1: Deep Analysis

Comprehensive static analysis to identify refactoring opportunities:

**Python Analysis**
- Code metrics (complexity, maintainability, duplication)
- Code smells detection (long methods, large classes, etc.)
- AST-based dependency analysis
- Type consistency checking
- Dead code detection

**JavaScript/TypeScript Analysis**
- ESLint flat config integration
- React-specific patterns (hooks, components)
- Next.js best practices validation
- Circular dependency detection
- Bundle size impact analysis

**Output**: `refactoring-analysis.json` with prioritized issues

### Phase 2: Planning

Generate a safe refactoring plan based on analysis:

```json
{
  "priority": "high",
  "category": "complexity",
  "refactoring": "extract_method",
  "location": "src/utils.py:45-78",
  "risk": "low",
  "impact": "high",
  "automated": true,
  "validation": ["unit_tests", "type_check"]
}
```

**Prioritization Matrix**:
- **High Risk + High Impact**: Manual review required, proceed with caution
- **Low Risk + High Impact**: Automated with comprehensive tests
- **High Risk + Low Impact**: Defer or manual only
- **Low Risk + Low Impact**: Optional, batch processing

### Phase 3: Execution

Apply refactorings incrementally with safety checks:

**Safety Mechanisms**
- Automated backup before each refactoring
- Test execution after each change
- Rollback on test failures
- Git integration for commit tracking
- Dry-run mode available

**Incremental Approach**
```python
for refactoring in plan:
    backup_state()
    apply_refactoring(refactoring)
    run_tests()
    if not tests_pass():
        rollback()
        log_failure(refactoring)
    else:
        commit_change(refactoring)
```

### Phase 4: Validation

Comprehensive post-refactoring validation:

- **Behavioral Tests**: All existing tests must pass
- **Performance Benchmarks**: No regression in performance
- **Metrics Comparison**: Complexity/maintainability improvements
- **Manual Review**: Critical changes flagged for review

## Language-Specific Features

### Python Refactoring Capabilities

**Supported Refactorings** (via Rope library):
- Rename (variables, functions, classes, modules)
- Extract Method/Function
- Extract Variable
- Inline Method/Variable
- Move Module/Class
- Change Method Signature
- Organize Imports
- Convert Local Variable to Field

**Analysis Tools**:
- **Pylint**: Code quality and style checking
- **Radon**: Cyclomatic complexity and maintainability metrics
- **Pyright**: Static type checking
- **Rope**: AST-based refactoring engine
- **LibCST**: Format-preserving transformations

**Example Usage**:
```python
# Automatic method extraction from complex function
# Before: 150-line function with cyclomatic complexity 25
# After: Main function + 5 extracted helper methods, complexity 8
```

See [references/python-patterns.md](references/python-patterns.md) for detailed Python refactoring patterns.

### Next.js/React Refactoring Capabilities

**Supported Refactorings**:
- Component extraction and composition
- Hooks optimization (useCallback, useMemo)
- Props drilling elimination (Context/state management)
- Client/Server component boundary optimization
- Route organization (App Router patterns)
- Bundle splitting and lazy loading

**Analysis Tools**:
- **ESLint 9+ flat config**: Modern linting with Next.js rules
- **typescript-eslint**: Type-aware linting
- **eslint-plugin-react**: React best practices
- **eslint-plugin-react-hooks**: Hooks rules
- **@next/eslint-plugin-next**: Next.js-specific rules
- **TypeScript Compiler API**: AST transformations

**React-Specific Patterns**:
- Extract custom hooks from duplicated logic
- Memoization for expensive computations
- Component splitting by responsibility
- Prop types refinement

**Next.js-Specific Patterns**:
- Server vs Client component optimization
- Route organization and grouping
- Middleware refactoring
- API route improvements
- Cache directive optimization (Next.js 15+)

See [references/nextjs-patterns.md](references/nextjs-patterns.md) for detailed patterns.

## Configuration

### Python Configuration (`pyproject.toml` or `.refactorconfig`)

```toml
[tool.refactoring]
# Analysis thresholds
max_complexity = 10
max_method_length = 50
max_class_length = 300
min_maintainability_index = 65

# Safety settings
require_tests = true
run_tests_after_refactoring = true
create_backup = true
git_commit_per_refactoring = false

# Tool settings
[tool.refactoring.pylint]
enabled = true
fail_under = 8.0

[tool.refactoring.type_check]
enabled = true
strict = true
```

### JavaScript/TypeScript Configuration (`eslint.config.mjs`)

```javascript
import nextPlugin from '@next/eslint-plugin-next'
import reactPlugin from 'eslint-plugin-react'
import hooksPlugin from 'eslint-plugin-react-hooks'
import tseslint from 'typescript-eslint'

export default [
  {
    files: ['**/*.{js,jsx,ts,tsx}'],
    plugins: {
      react: reactPlugin,
      'react-hooks': hooksPlugin,
      '@next/next': nextPlugin,
    },
    rules: {
      ...reactPlugin.configs['jsx-runtime'].rules,
      ...hooksPlugin.configs.recommended.rules,
      ...nextPlugin.configs.recommended.rules,
      ...nextPlugin.configs['core-web-vitals'].rules,
      
      // Refactoring-focused rules
      'complexity': ['error', 10],
      'max-lines-per-function': ['warn', 50],
      'max-depth': ['error', 3]
    }
  },
  ...tseslint.configs.recommendedTypeChecked
]
```

## Understanding Analysis Reports

The analysis report categorizes issues by:

1. **Complexity Issues**: High cyclomatic complexity, nested conditionals
2. **Code Smells**: Long methods, large classes, duplicated code
3. **Maintainability**: Low maintainability index, unclear naming
4. **Architecture**: Circular dependencies, tight coupling
5. **Performance**: Inefficient algorithms, unnecessary re-renders

Each issue includes:
- **Severity**: critical, high, medium, low
- **Location**: File and line numbers
- **Suggested Refactoring**: Specific pattern to apply
- **Automation Status**: Can be automated or requires manual review
- **Estimated Impact**: LOC affected, test coverage needed

See [references/metrics.md](references/metrics.md) for interpreting metrics.

## Common Refactoring Patterns

### Extract Method (Python & JavaScript)

**When to Use**: Function > 50 lines or complexity > 10

```python
# Before
def process_order(order):
    # 150 lines of mixed logic
    validate_items()
    calculate_totals()
    apply_discounts()
    process_payment()
    send_confirmation()

# After - extracted methods
def process_order(order):
    validated_order = validate_order(order)
    totals = calculate_order_totals(validated_order)
    discounted_totals = apply_order_discounts(totals)
    payment_result = process_order_payment(discounted_totals)
    send_order_confirmation(payment_result)
```

### Simplify Conditionals

**When to Use**: Nested conditionals > 3 levels

```javascript
// Before
if (user) {
  if (user.isActive) {
    if (user.hasPermission('write')) {
      // do something
    }
  }
}

// After - guard clauses
if (!user) return
if (!user.isActive) return
if (!user.hasPermission('write')) return
// do something
```

### Replace Primitive with Object

**When to Use**: Primitive values with associated behavior

```python
# Before
def calculate_shipping(weight: float, distance: int) -> float:
    # weight in kg, distance in km
    pass

# After
class Weight:
    def __init__(self, kilograms: float):
        self.kg = kilograms
    def to_pounds(self) -> float:
        return self.kg * 2.20462

class Distance:
    def __init__(self, kilometers: int):
        self.km = kilometers
```

See [references/code-smells.md](references/code-smells.md) for complete pattern catalog.

## Advanced Features

### Batch Processing

Process multiple files with a single command:

```bash
# Python batch refactoring
python scripts/refactor_python.py /project \
  --batch \
  --parallel 4 \
  --only-automated

# JavaScript batch refactoring
node scripts/refactor_js.js /project \
  --batch \
  --parallel 4 \
  --only-automated
```

### Custom Refactoring Rules

Define project-specific refactoring rules:

```python
# .refactor-rules.py
from refactor import Rule, Pattern

class MyCustomRule(Rule):
    name = "extract_api_call"
    pattern = Pattern("requests.get(*)")
    
    def should_refactor(self, node):
        return len(node.args) > 3
    
    def refactor(self, node):
        return extract_to_api_client(node)
```

### CI/CD Integration

```yaml
# .github/workflows/refactor-check.yml
name: Refactoring Analysis
on: [pull_request]

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run refactoring analysis
        run: |
          python scripts/analyze_python.py . --output report.json
      - name: Comment on PR if issues found
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs')
            const report = JSON.parse(fs.readFileSync('report.json'))
            // Post analysis summary as PR comment
```

## Safety Best Practices

1. **Always run in a clean git state**: Commit or stash changes first
2. **Use dry-run mode for initial attempts**: `--dry-run` flag
3. **Review automated changes**: Even automated refactorings need review
4. **Test coverage first**: Ensure good test coverage before refactoring
5. **Incremental approach**: Refactor one thing at a time
6. **Separate commits**: Each refactoring type in separate commits

## Troubleshooting

**Tests failing after refactoring**:
- Check the rollback logs in `.refactoring-logs/`
- Review the specific refactoring that failed
- Run tests manually to isolate the issue

**Analysis tool errors**:
- Ensure all dependencies are installed (see `references/tools-setup.md`)
- Check Python/Node version compatibility
- Verify project structure matches expected patterns

**Performance issues with large codebases**:
- Use `--parallel` flag for concurrent processing
- Exclude test files and vendor directories
- Process by module/directory instead of whole project

## Reference Documentation

Detailed guides for deep dives:

- **[references/multidim-analysis.md](references/multidim-analysis.md)** - **NEW!** Comprehensive guide to multi-dimensional analysis: understanding scores, metrics, thresholds, and case studies across all 5 dimensions
- **[references/python-patterns.md](references/python-patterns.md)** - Complete Python refactoring pattern catalog with Martin Fowler patterns, Rope library usage, and type hints integration
- **[references/nextjs-patterns.md](references/nextjs-patterns.md)** - Next.js and React refactoring patterns including Server/Client components, hooks optimization, and App Router patterns
- **[references/code-smells.md](references/code-smells.md)** - Comprehensive code smell detection guide with examples
- **[references/metrics.md](references/metrics.md)** - Detailed metrics interpretation and threshold guidelines
- **[references/tools-setup.md](references/tools-setup.md)** - Installation and configuration for all analysis tools

## Limitations

- **Python**: Rope library supports up to Python 3.10 syntax (as of 2025)
- **JavaScript**: AST transformations work best with TypeScript
- **Large Projects**: Analysis may take several minutes for projects > 100k LOC
- **Test-First**: Refactoring quality depends on existing test coverage
- **Dynamic Code**: Runtime behavior analysis not included (only static analysis)

## Version Support

- Python: 3.8 - 3.13
- Node.js: 18+ (for Next.js 14+)
- Next.js: 14.x, 15.x
- React: 18.x, 19.x
- TypeScript: 5.x
- ESLint: 9.x (flat config)
