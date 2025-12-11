# Tools Setup (Quick Reference)

## Python Installation

```bash
# Core analysis tools (required)
pip install radon bandit --break-system-packages

# Optional tools
pip install pylint pydeps safety line-profiler memory-profiler rope
```

### Verify Installation
```bash
python -c "import radon; print('✓ radon')"
bandit --version
```

## JavaScript/TypeScript Installation

```bash
# Per-project installation (recommended)
npm install --save-dev eslint madge jscpd \
  @typescript-eslint/eslint-plugin \
  eslint-plugin-security
```

### Verify Installation
```bash
npx eslint --version
npx madge --version
```

## Common Issues

### Python

| Issue | Solution |
|-------|----------|
| `radon: command not found` | `pip install radon --break-system-packages` |
| `bandit: command not found` | `pip install bandit --break-system-packages` |
| Import errors in bandit | `export PYTHONPATH="${PYTHONPATH}:$(pwd)"` |
| pydeps graphviz error | `brew install graphviz` (macOS) / `apt install graphviz` |

### JavaScript

| Issue | Solution |
|-------|----------|
| eslint not found | `npm install --save-dev eslint` |
| madge TypeScript error | `npx madge --ts-config ./tsconfig.json src/` |
| jscpd too slow | Add to `.jscpd.json`: `"minLines": 10` |

## Quick Commands

### Python Analysis
```bash
radon cc . -a --json          # Complexity (JSON)
radon mi . --json             # Maintainability index
bandit -r src/ -f json        # Security scan
```

### JavaScript Analysis
```bash
npx eslint . --format json    # Lint + complexity
npx madge --circular src/     # Circular deps
npx jscpd src/ --format json  # Code duplication
```

## CI/CD One-Liner

```bash
# Python
pip install radon bandit && python scripts/analyze_multidim.py . --all

# JavaScript
npm ci && node scripts/analyze_multidim.js . --all
```

## When Tools Fail

The analyzers handle missing tools gracefully:
- Missing tool → Dimension marked as `skipped`
- Partial failure → Continue with available tools
- Confidence adjusted based on tool coverage

See `meta.tools_failed` in output for details.
