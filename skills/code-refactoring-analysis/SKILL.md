---
name: code-refactoring-analysis
version: "1.1.0"
description: Multi-dimensional static code analysis for Python and JavaScript/TypeScript projects (React, Next.js, Vue, Svelte). Use when users request "analyze code", "code quality", "technical debt", "code smells", "security scan", or "performance analysis".

triggers:
  keywords: ["analyze code", "code quality", "technical debt", "code smells", "security scan", "performance analysis", "refactoring opportunities", "check code health"]
  file_patterns: ["*.py", "*.js", "*.jsx", "*.ts", "*.tsx", "*.mjs", "*.cjs", "*.vue", "*.svelte"]

not_for:
  - "Runtime/dynamic analysis (static only)"
  - "Planning refactoring work (use project-planner)"
  - "Breaking down tasks (use task-decomposer)"
  - "Executing refactoring (use code-refactoring skill)"

dependencies:
  python:
    required: ["radon"]
    recommended: ["bandit", "safety", "pylint", "pydeps"]
  javascript:
    required: []
    recommended: ["eslint", "madge", "jscpd"]

outputs_to:
  - skill: "project-planner"
    file: "multidim-analysis.json"

references:
  always_load: []
  on_score_interpretation: ["quick-ref.md"]
  on_deep_analysis: ["multidim-analysis.md", "metrics.md"]
  on_troubleshooting: ["tools-setup.md"]
---

# Code Refactoring Analysis

5-dimensional static analysis identifying refactoring opportunities.

**Dimensions**: Maintainability(35%) | Security(25%) | Performance(20%) | Scalability(10%) | Reusability(10%)

## Quick Start

```bash
# Python
python scripts/analyze_multidim.py /path/to/project --all

# JavaScript/TypeScript
node scripts/analyze_multidim.js /path/to/project --all

# Output: ./multidim-analysis.json
```

## Output Structure

```json
{
  "meta": {
    "analyzer_version": "1.1.0",
    "tools_used": ["radon", "bandit"],
    "confidence": 0.92
  },
  "overall_health": 82,
  "priority_actions": [
    {"priority": "high", "action": "Fix SQL injection in db.py:45", "dimension": "security"}
  ],
  "dimensions": {
    "maintainability": {"score": 85, "weight": 0.35, "issues": [...]},
    "security": {"score": 90, "weight": 0.25, "issues": [...]},
    "performance": {"score": 70, "weight": 0.20, "issues": [...]},
    "scalability": {"score": 75, "weight": 0.10, "issues": [...]},
    "reusability": {"score": 80, "weight": 0.10, "issues": [...]}
  }
}
```

## Issue Format

```json
{
  "severity": "high",
  "category": "complexity",
  "file": "src/utils.py",
  "line": 45,
  "message": "Cyclomatic complexity 25 exceeds threshold 10",
  "suggested_refactoring": "extract_method",
  "automated": true,
  "risk": "low",
  "impact": "high"
}
```

## CLI Options

| Option | Description | Default |
|--------|-------------|---------|
| `--all` | Analyze all 5 dimensions | - |
| `--dimensions <list>` | Specific dimensions (comma-separated) | all |
| `--output <path>` | Output file path | ./multidim-analysis.json |
| `--max-complexity <n>` | Complexity threshold | 10 |

## Skill Workflow

```
code-refactoring-analysis  →  project-planner  →  task-decomposer
(What needs fixing?)          (How to fix?)        (Task sequence)
         ↓
  multidim-analysis.json
```

## Fallback Strategies

### External Tool Unavailable
When analysis tools are not installed:
1. Run available tools only
2. Mark missing dimensions: `"status": "skipped", "reason": "bandit not installed"`
3. Add to warnings array: `"warnings": ["security analysis partial - bandit unavailable"]`
4. Adjust confidence score proportionally

### Large Codebase (>100k LOC)
1. Use `--dimensions` for specific analysis
2. Analyze by directory: `--path src/module1`
3. Increase timeout if needed

### Partial Failure
If some tools fail mid-analysis:
1. Continue with remaining tools
2. Include partial results with `"tools_failed": ["safety"]`
3. Note in meta: `"coverage": {"complete": false, "reason": "tool failure"}`

## Score Interpretation

| Score | Status | Recommendation |
|-------|--------|----------------|
| 90-100 | Excellent | Maintain practices |
| 75-89 | Good | Minor improvements |
| 60-74 | Fair | Plan refactoring sprint |
| 45-59 | Poor | Prioritize critical fixes |
| <45 | Critical | Immediate intervention |

## References

- **[quick-ref.md](references/quick-ref.md)** - Score tables and severity mapping
- **[metrics.md](references/metrics.md)** - Detailed metric interpretation
- **[multidim-analysis.md](references/multidim-analysis.md)** - Deep analysis guide
- **[code-smells.md](references/code-smells.md)** - Code smell catalog
- **[tools-setup.md](references/tools-setup.md)** - Tool installation (troubleshooting)

## Limitations

- Static analysis only (no runtime behavior)
- Python and JavaScript/TypeScript only
- Large projects (>100k LOC) may need chunked analysis
