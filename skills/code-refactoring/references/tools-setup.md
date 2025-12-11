# Tools Installation and Setup Guide

Complete guide for installing and configuring all refactoring and analysis tools.

## Python Tools

### System Requirements
- Python 3.8 - 3.13
- pip (latest version)

### Core Refactoring Tools

#### Rope (Refactoring Library)
```bash
# Install
pip install rope --break-system-packages

# Or in virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install rope
```

**Configuration** (`.ropeproject/config.py`):
```python
# Set Python path
prefs['python_path'] = '/path/to/your/venv/bin/python'

# Ignore patterns
prefs['ignore_syntax_errors'] = False
prefs['ignore_bad_imports'] = False

# Auto-save
prefs['automatic_soa'] = True
prefs['soa_followed_calls'] = 2
```

#### Pylint (Static Analysis)
```bash
pip install pylint --break-system-packages
```

**Configuration** (`.pylintrc`):
```ini
[MASTER]
max-line-length=100
disable=C0111,  # missing-docstring
        C0103   # invalid-name

[MESSAGES CONTROL]
confidence=HIGH

[REFACTORING]
max-nested-blocks=3
max-returns=5
max-branches=12
max-statements=50
```

#### Radon (Complexity Metrics)
```bash
pip install radon --break-system-packages
```

**Usage**:
```bash
# Cyclomatic complexity
radon cc . -a -s

# Maintainability index
radon mi . -s

# Raw metrics
radon raw . -s

# JSON output for automation
radon cc . -j > complexity.json
```

#### Pyright (Type Checking)
```bash
pip install pyright --break-system-packages
```

**Configuration** (`pyrightconfig.json`):
```json
{
  "include": ["src"],
  "exclude": ["**/node_modules", "**/__pycache__"],
  "pythonVersion": "3.11",
  "typeCheckingMode": "basic",
  "reportMissingImports": true,
  "reportMissingTypeStubs": false
}
```

#### LibCST (Format-Preserving Transformations)
```bash
pip install libcst --break-system-packages
```

**Example Usage**:
```python
import libcst as cst

# Parse code
tree = cst.parse_module("def foo(): pass")

# Transform
class RenameTransformer(cst.CSTTransformer):
    def leave_Name(self, original_node, updated_node):
        if original_node.value == "foo":
            return updated_node.with_changes(value="bar")
        return updated_node

# Apply
new_tree = tree.visit(RenameTransformer())
print(new_tree.code)
```

### Additional Tools

#### Black (Code Formatter)
```bash
pip install black --break-system-packages
```

**Configuration** (`pyproject.toml`):
```toml
[tool.black]
line-length = 100
target-version = ['py311']
include = '\.pyi?$'
```

#### isort (Import Sorter)
```bash
pip install isort --break-system-packages
```

**Configuration** (`pyproject.toml`):
```toml
[tool.isort]
profile = "black"
line_length = 100
multi_line_output = 3
```

#### Vulture (Dead Code Detector)
```bash
pip install vulture --break-system-packages
```

**Usage**:
```bash
vulture . --min-confidence 80
```

## JavaScript/TypeScript Tools

### System Requirements
- Node.js 18+ (for Next.js 14+)
- npm or pnpm

### Core Tools

#### ESLint (Linter)
```bash
npm install -g eslint

# Or per-project
npm install --save-dev eslint
```

**Next.js Configuration** (`eslint.config.mjs`):
```javascript
import { defineConfig } from 'eslint/config'
import nextVitals from 'eslint-config-next/core-web-vitals'
import typescript from 'typescript-eslint'
import react from 'eslint-plugin-react'
import reactHooks from 'eslint-plugin-react-hooks'

export default defineConfig([
  ...nextVitals,
  ...typescript.configs.recommendedTypeChecked,
  {
    files: ['**/*.{js,jsx,ts,tsx}'],
    plugins: {
      react,
      'react-hooks': reactHooks
    },
    languageOptions: {
      parserOptions: {
        project: './tsconfig.json'
      }
    },
    rules: {
      'complexity': ['error', 10],
      'max-lines-per-function': ['warn', 50],
      'max-depth': ['error', 3],
      'max-params': ['warn', 5],
      'react-hooks/exhaustive-deps': 'error',
      'react/jsx-no-bind': 'warn',
      '@next/next/no-img-element': 'error'
    }
  }
])
```

#### TypeScript ESLint
```bash
npm install --save-dev @typescript-eslint/parser @typescript-eslint/eslint-plugin typescript-eslint
```

#### React Plugins
```bash
npm install --save-dev \
  eslint-plugin-react \
  eslint-plugin-react-hooks \
  eslint-plugin-jsx-a11y
```

#### Next.js Plugin
```bash
npm install --save-dev @next/eslint-plugin-next eslint-config-next
```

#### React Compiler Plugin (React 19+)
```bash
npm install --save-dev eslint-plugin-react-compiler
```

**Add to config**:
```javascript
import reactCompiler from 'eslint-plugin-react-compiler'

export default [
  // ...other config
  reactCompiler.configs.recommended
]
```

### TypeScript Configuration

**`tsconfig.json`**:
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "jsx": "preserve",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "forceConsistentCasingInFileNames": true,
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx"],
  "exclude": ["node_modules", ".next"]
}
```

### Prettier (Code Formatter)
```bash
npm install --save-dev prettier eslint-config-prettier eslint-plugin-prettier
```

**Configuration** (`.prettierrc`):
```json
{
  "semi": false,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 100,
  "arrowParens": "avoid"
}
```

## Multi-Language Tools

### SonarQube
```bash
# Using Docker
docker run -d --name sonarqube -p 9000:9000 sonarqube:latest

# Or download from https://www.sonarqube.org/downloads/
```

**Scanner Setup**:
```bash
# Install scanner
npm install -g sonarqube-scanner

# Or download from https://docs.sonarqube.org/latest/analysis/scan/sonarscanner/
```

**Configuration** (`sonar-project.properties`):
```properties
sonar.projectKey=my-project
sonar.projectName=My Project
sonar.projectVersion=1.0
sonar.sources=src
sonar.tests=tests

# Python specific
sonar.python.version=3.11
sonar.python.coverage.reportPaths=coverage.xml

# JavaScript/TypeScript specific
sonar.javascript.lcov.reportPaths=coverage/lcov.info
sonar.typescript.tsconfigPath=tsconfig.json

# Exclusions
sonar.exclusions=**/*.test.ts,**/*.spec.ts,**/node_modules/**,**/__pycache__/**
```

**Run Analysis**:
```bash
sonar-scanner \
  -Dsonar.host.url=http://localhost:9000 \
  -Dsonar.login=your_token
```

### CodeScene
Commercial tool with free tier for open source.

**Setup**:
1. Sign up at https://codescene.com
2. Connect Git repository
3. Configure analysis schedules

### Git Integration

#### Pre-commit Hooks
```bash
# Install pre-commit
pip install pre-commit --break-system-packages

# Or for Node projects
npm install --save-dev husky lint-staged
```

**Configuration** (`.pre-commit-config.yaml`):
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
  
  - repo: https://github.com/PyCQA/isort
    rev: 5.13.2
    hooks:
      - id: isort
  
  - repo: https://github.com/PyCQA/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
  
  - repo: local
    hooks:
      - id: eslint
        name: ESLint
        entry: npx eslint --fix
        language: node
        types: [javascript, typescript]
```

**Install hooks**:
```bash
pre-commit install
```

#### Lint-staged (Node)
**Configuration** (`.lintstagedrc.js`):
```javascript
module.exports = {
  '*.{js,jsx,ts,tsx}': ['eslint --fix', 'prettier --write'],
  '*.{json,md}': ['prettier --write']
}
```

**`package.json`**:
```json
{
  "scripts": {
    "prepare": "husky install"
  }
}
```

## CI/CD Integration

### GitHub Actions

**`.github/workflows/code-quality.yml`**:
```yaml
name: Code Quality

on: [push, pull_request]

jobs:
  python-quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install pylint radon --break-system-packages
      
      - name: Run Pylint
        run: pylint src/
      
      - name: Check Complexity
        run: |
          radon cc src/ -a -nb
          radon mi src/ -nb
  
  js-quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Node
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Run ESLint
        run: npm run lint
      
      - name: Type Check
        run: npm run type-check
```

### VS Code Integration

**`.vscode/settings.json`**:
```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true,
    "source.fixAll.eslint": true
  },
  "eslint.validate": [
    "javascript",
    "javascriptreact",
    "typescript",
    "typescriptreact"
  ],
  "typescript.tsdk": "node_modules/typescript/lib"
}
```

**`.vscode/extensions.json`**:
```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "bradlc.vscode-tailwindcss"
  ]
}
```

## Docker Setup

**`Dockerfile`** for analysis environment:
```dockerfile
FROM python:3.11-slim

# Install Python tools
RUN pip install --no-cache-dir \
    pylint \
    radon \
    pyright \
    rope \
    black \
    isort

# Install Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
RUN apt-get install -y nodejs

# Install Node tools
RUN npm install -g \
    eslint \
    typescript \
    prettier

WORKDIR /app

CMD ["/bin/bash"]
```

**Usage**:
```bash
docker build -t refactoring-tools .
docker run -v $(pwd):/app refactoring-tools pylint src/
```

## Troubleshooting

### Python Issues

**ModuleNotFoundError with Rope**:
```bash
# Ensure rope can find your modules
export PYTHONPATH="${PYTHONPATH}:/path/to/project"
```

**Pylint import errors**:
```bash
# Install project in editable mode
pip install -e .
```

### JavaScript Issues

**ESLint parsing errors**:
```bash
# Clear cache
rm -rf node_modules/.cache
npm cache clean --force
npm install
```

**TypeScript version conflicts**:
```bash
# Use workspace version
npm install typescript@latest --save-dev
```

## Performance Optimization

### Large Projects

**Parallel Analysis**:
```bash
# Python
pylint src/ --jobs=4

# JavaScript
eslint . --cache --max-warnings=0
```

**Incremental Analysis**:
```bash
# Only analyze changed files
git diff --name-only --diff-filter=ACMR | grep '\.py$' | xargs pylint
```

### Memory Management

**Python**:
```bash
# Limit Radon to one file at a time
find . -name '*.py' -exec radon cc {} \;
```

**Node**:
```bash
# Increase Node memory
NODE_OPTIONS="--max-old-space-size=4096" npm run lint
```

## Maintenance

**Update Tools Regularly**:
```bash
# Python
pip install --upgrade pylint radon rope

# Node
npm update -g eslint typescript
npm update --save-dev @typescript-eslint/parser
```

**Check for Security Updates**:
```bash
npm audit
pip-audit  # Install with: pip install pip-audit
```

---

## Multi-Dimensional Analysis Tools

Additional tools for comprehensive multi-dimensional code analysis.

### Python: Performance Analysis

#### cProfile (Built-in Profiler)
```bash
# Built-in, no installation needed
python -m cProfile -o profile.stats your_script.py

# Analyze results
python -m pstats profile.stats
# Inside pstats:
> sort cumulative
> stats 20
```

#### line_profiler (Line-by-Line Profiling)
```bash
pip install line-profiler --break-system-packages
```

**Usage**:
```python
# Add @profile decorator to functions
@profile
def slow_function():
    # ... your code

# Run
kernprof -l -v your_script.py
```

#### memory_profiler (Memory Usage)
```bash
pip install memory-profiler --break-system-packages
```

**Usage**:
```python
from memory_profiler import profile

@profile
def memory_intensive_function():
    # ... your code

# Run
python -m memory_profiler your_script.py
```

### Python: Security Analysis

#### Bandit (Security Linter)
```bash
pip install bandit --break-system-packages
```

**Usage**:
```bash
# Basic scan
bandit -r src/

# JSON output for automation
bandit -r src/ -f json -o security-report.json

# With confidence levels
bandit -r src/ --confidence-level high

# Exclude tests
bandit -r src/ --exclude src/tests/
```

**Configuration** (`.bandit`):
```yaml
# .bandit
exclude_dirs:
  - /tests/
  - /venv/

skips:
  - B101  # assert_used (if using pytest)

tests:
  - B201  # flask_debug_true
  - B601  # paramiko_calls
  - B602  # subprocess_popen_with_shell_equals_true
```

#### Safety (Dependency Vulnerability Scanner)
```bash
pip install safety --break-system-packages
```

**Usage**:
```bash
# Scan installed packages
safety check

# Scan requirements.txt
safety check --file requirements.txt

# JSON output
safety check --json

# Only production dependencies
safety check --file requirements.txt --full-report
```

### Python: Scalability Analysis

#### pydeps (Dependency Visualization)
```bash
pip install pydeps --break-system-packages

# Also install graphviz for visualization
# Ubuntu/Debian:
sudo apt-get install graphviz
# macOS:
brew install graphviz
```

**Usage**:
```bash
# Generate dependency graph
pydeps your_module --max-bacon=2

# Show circular dependencies only
pydeps your_module --show-cycles

# Export as SVG
pydeps your_module -o dependencies.svg

# JSON output for automation
pydeps your_module --format json > deps.json
```

### JavaScript/TypeScript: Performance Analysis

#### webpack-bundle-analyzer
```bash
npm install --save-dev webpack-bundle-analyzer
```

**Configuration** (`next.config.js` for Next.js):
```javascript
const withBundleAnalyzer = require('@next/bundle-analyzer')({
  enabled: process.env.ANALYZE === 'true',
})

module.exports = withBundleAnalyzer({
  // ... your Next.js config
})
```

**Usage**:
```bash
ANALYZE=true npm run build
```

#### Lighthouse (Performance Auditing)
```bash
npm install -g lighthouse

# Or use Chrome DevTools (F12 -> Lighthouse)
```

**Usage**:
```bash
# Audit a URL
lighthouse https://example.com --output html --output-path ./report.html

# Focus on performance
lighthouse https://example.com --only-categories=performance

# JSON output for CI/CD
lighthouse https://example.com --output json --output-path ./report.json
```

### JavaScript/TypeScript: Security Analysis

#### eslint-plugin-security
```bash
npm install --save-dev eslint-plugin-security
```

**Configuration** (`eslint.config.mjs`):
```javascript
import security from 'eslint-plugin-security'

export default [
  {
    plugins: {
      security
    },
    rules: {
      ...security.configs.recommended.rules,
      'security/detect-object-injection': 'warn',
      'security/detect-non-literal-regexp': 'warn',
      'security/detect-unsafe-regex': 'error'
    }
  }
]
```

#### npm audit (Built-in)
```bash
# Check for vulnerabilities
npm audit

# Auto-fix (may break dependencies)
npm audit fix

# Force fix (be careful!)
npm audit fix --force

# JSON output for automation
npm audit --json > audit-report.json

# Check production dependencies only
npm audit --production
```

#### Snyk (Optional - Cloud-based)
```bash
npm install -g snyk

# Authenticate
snyk auth

# Test for vulnerabilities
snyk test

# Monitor over time
snyk monitor
```

### JavaScript/TypeScript: Scalability Analysis

#### dependency-cruiser
```bash
npm install --save-dev dependency-cruiser
```

**Configuration** (`.dependency-cruiser.js`):
```javascript
module.exports = {
  forbidden: [
    {
      name: 'no-circular',
      severity: 'error',
      from: {},
      to: { circular: true }
    },
    {
      name: 'no-deprecated',
      severity: 'warn',
      from: {},
      to: { dependencyTypes: ['deprecated'] }
    }
  ]
}
```

**Usage**:
```bash
# Validate dependencies
npx depcruise src --validate

# Generate visual graph
npx depcruise src --output-type dot | dot -T svg > dependencies.svg

# Check for circular dependencies only
npx depcruise src --output-type err-html --output-to report.html
```

#### madge (Circular Dependency Detection)
```bash
npm install --save-dev madge
```

**Usage**:
```bash
# Check for circular dependencies
npx madge --circular src/

# JSON output
npx madge --circular --json src/

# Generate visual graph
npx madge --image graph.svg src/

# Find orphan files
npx madge --orphans src/
```

### JavaScript/TypeScript: Reusability Analysis

#### jscpd (Copy-Paste Detector)
```bash
npm install --save-dev jscpd
```

**Configuration** (`.jscpd.json`):
```json
{
  "threshold": 5,
  "reporters": ["html", "json", "console"],
  "ignore": [
    "**/node_modules/**",
    "**/*.min.js",
    "**/dist/**"
  ],
  "format": ["javascript", "typescript"],
  "minLines": 5,
  "minTokens": 50
}
```

**Usage**:
```bash
# Basic check
npx jscpd src/

# With threshold (fail if duplication > 5%)
npx jscpd src/ --threshold 5

# Generate HTML report
npx jscpd src/ --format html

# JSON output for CI/CD
npx jscpd src/ --format json -o report.json
```

## Multi-Dimensional Analysis: Quick Setup

### Python Complete Installation
```bash
# All tools for multi-dimensional analysis
pip install --break-system-packages \
  radon \
  pylint \
  rope \
  pyright \
  bandit \
  safety \
  pydeps \
  line-profiler \
  memory-profiler

# Verify installation
python -c "import radon, pylint, rope, bandit; print('✓ All tools installed')"
```

### JavaScript/TypeScript Complete Installation
```bash
# All tools for multi-dimensional analysis
npm install --save-dev \
  eslint \
  @typescript-eslint/eslint-plugin \
  @typescript-eslint/parser \
  eslint-plugin-react \
  eslint-plugin-react-hooks \
  eslint-plugin-security \
  @next/eslint-plugin-next \
  dependency-cruiser \
  madge \
  jscpd \
  webpack-bundle-analyzer

# Global tools
npm install -g lighthouse

# Verify installation
node -e "require('eslint'); require('madge'); console.log('✓ All tools installed')"
```

## CI/CD Integration for Multi-Dimensional Analysis

### GitHub Actions Example

```yaml
name: Multi-Dimensional Code Analysis

on: [push, pull_request]

jobs:
  python-analysis:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install analysis tools
        run: |
          pip install radon pylint bandit safety --break-system-packages
      
      - name: Run multi-dimensional analysis
        run: |
          python scripts/analyze_multidim.py . --all --output analysis.json
      
      - name: Check thresholds
        run: |
          python -c "
          import json
          with open('analysis.json') as f:
              data = json.load(f)
              if data['overall_health'] < 70:
                  raise Exception(f'Health score too low: {data[\"overall_health\"]}')
              if data['dimensions']['security']['score'] < 80:
                  raise Exception('Security score too low')
          "
      
      - name: Upload report
        uses: actions/upload-artifact@v3
        with:
          name: analysis-report
          path: analysis.json

  javascript-analysis:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Run multi-dimensional analysis
        run: |
          node scripts/analyze_multidim.js . --all --output analysis.json
      
      - name: Check thresholds
        run: |
          node -e "
          const data = require('./analysis.json');
          if (data.overall_health < 70) {
              throw new Error(\`Health score too low: \${data.overall_health}\`);
          }
          if (data.dimensions.security.score < 80) {
              throw new Error('Security score too low');
          }
          "
      
      - name: Upload report
        uses: actions/upload-artifact@v3
        with:
          name: analysis-report
          path: analysis.json
```

## Troubleshooting Multi-Dimensional Tools

### Python Issues

**Bandit fails with import errors**:
```bash
# Ensure project is in PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
bandit -r src/
```

**pydeps graphviz not found**:
```bash
# Install graphviz system package
sudo apt-get install graphviz  # Ubuntu/Debian
brew install graphviz  # macOS
```

**Memory profiler slows down code**:
```python
# Use sampling mode instead of tracing
@profile(precision=1)  # 1-second precision
def function():
    pass
```

### JavaScript Issues

**npm audit showing false positives**:
```bash
# Audit production dependencies only
npm audit --production

# Override specific packages (be careful!)
npm audit fix --force
```

**jscpd taking too long**:
```json
{
  "threshold": 10,  // Increase threshold
  "ignore": ["**/tests/**"],  // Exclude tests
  "minLines": 10  // Only detect larger blocks
}
```

**madge not finding TypeScript files**:
```bash
# Use TypeScript config
npx madge --ts-config ./tsconfig.json src/
```


