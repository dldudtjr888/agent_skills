# Code Metrics Interpretation Guide

Understanding and interpreting code quality metrics for refactoring decisions.

## Core Metrics

### Cyclomatic Complexity (CC)

**Definition**: Number of linearly independent paths through code

**Calculation**:
```
CC = E - N + 2P
E = edges in control flow graph
N = nodes in control flow graph
P = number of connected components
```

**Simplified**: Count decision points + 1
- Each `if`, `for`, `while`, `case`: +1
- Each `&&`, `||`, `?`: +1

**Interpretation**:
- **1-5**: Simple, low risk
- **6-10**: Moderate, acceptable
- **11-20**: Complex, consider refactoring
- **21-50**: High risk, refactor urgently
- **> 50**: Critical, untestable

**Refactoring Threshold**: 10

**Example**:
```python
def calculate_price(item, quantity, customer):  # CC = 1 (start)
    price = item.base_price
    
    if quantity > 100:           # +1 = 2
        price *= 0.9
    elif quantity > 50:          # +1 = 3
        price *= 0.95
    
    if customer.is_premium:      # +1 = 4
        price *= 0.9
    
    return price * quantity
# Total CC = 4 (Acceptable)
```

### Maintainability Index (MI)

**Definition**: 0-100 score combining complexity, LOC, and Halstead volume

**Calculation**:
```
MI = 171 - 5.2 * ln(HV) - 0.23 * CC - 16.2 * ln(LOC)

Where:
HV = Halstead Volume
CC = Cyclomatic Complexity
LOC = Lines of Code
```

**Interpretation**:
- **85-100**: Excellent (A) - Easy to maintain
- **65-84**: Good (B) - Moderate maintenance
- **40-64**: Fair (C) - Needs attention
- **20-39**: Poor (D) - Difficult to maintain
- **0-19**: Critical (F) - Very difficult to maintain

**Refactoring Threshold**: < 65

**Rank Colors**:
- **Green** (A): MI 85-100
- **Yellow** (B): MI 65-84
- **Orange** (C): MI 40-64
- **Red** (D-F): MI < 40

### Lines of Code (LOC)

**Types**:
- **Physical LOC**: All lines including blanks
- **Source LOC**: Lines with actual code
- **Logical LOC**: Number of statements

**Function/Method Thresholds**:
- **< 50**: Good
- **50-100**: Acceptable
- **100-200**: Consider splitting
- **> 200**: Refactor immediately

**Class Thresholds**:
- **< 300**: Good
- **300-500**: Acceptable
- **500-1000**: Consider splitting
- **> 1000**: Refactor immediately

**File Thresholds**:
- **< 500**: Good
- **500-1000**: Acceptable
- **> 1000**: Consider splitting

### Code Duplication

**Measurement**: Percentage of duplicated lines

**Thresholds**:
- **0-3%**: Excellent
- **3-5%**: Good
- **5-10%**: Moderate, address major duplications
- **10-20%**: High, requires refactoring
- **> 20%**: Critical, serious technical debt

**Detection**:
- Exact duplicates
- Structural duplicates (renamed variables)
- Similar code blocks (> 6 lines)

**Refactoring Priority**:
1. > 50 lines duplicated
2. Duplicated in > 3 places
3. Core business logic
4. Frequently changing code

### Nesting Depth

**Definition**: Maximum depth of nested control structures

**Thresholds**:
- **1-2**: Good
- **3**: Acceptable
- **4-5**: Complex, consider refactoring
- **> 5**: Critical, refactor immediately

**Example**:
```python
def process(data):
    if data:                    # Depth 1
        for item in data:       # Depth 2
            if item.valid:      # Depth 3
                while item.process():  # Depth 4
                    if item.needs_retry:  # Depth 5 - TOO DEEP
                        # ...
```

### Parameter Count

**Thresholds**:
- **0-3**: Good
- **4-5**: Acceptable
- **6-7**: Consider parameter object
- **> 7**: Refactor immediately

**Refactorings**:
- Introduce Parameter Object
- Preserve Whole Object
- Replace Parameters with Query

### Test Coverage

**Types**:
- **Line Coverage**: % of lines executed
- **Branch Coverage**: % of decision branches taken
- **Function Coverage**: % of functions called

**Thresholds**:
- **80-100%**: Excellent
- **60-80%**: Good
- **40-60%**: Acceptable
- **< 40%**: Poor, increase before refactoring

**Priority for Refactoring**:
- Ensure > 60% coverage before major refactoring
- Focus on critical business logic
- Cover refactored code with new tests

## Composite Metrics

### Technical Debt Ratio

**Calculation**:
```
TD Ratio = (Remediation Cost / Development Cost) * 100

Remediation Cost = Sum of effort to fix all issues
Development Cost = Total development effort
```

**Interpretation**:
- **< 5%**: Excellent
- **5-10%**: Good
- **10-20%**: Moderate debt
- **> 20%**: High debt, impacts velocity

### Code Churn

**Definition**: Lines added + modified + deleted per time period

**Thresholds**:
- **High churn + high complexity**: Hot spot, refactor
- **High churn + low complexity**: Volatile requirements
- **Low churn + high complexity**: Legacy, technical debt
- **Low churn + low complexity**: Stable, good

### Coupling Metrics

**Afferent Coupling (Ca)**: Number of classes that depend on this class

**Efferent Coupling (Ce)**: Number of classes this class depends on

**Instability (I)**:
```
I = Ce / (Ca + Ce)

0 = Maximally stable
1 = Maximally unstable
```

**Thresholds**:
- **Core business logic**: I < 0.3 (stable)
- **Adapters/glue code**: I > 0.7 (unstable okay)

## Python-Specific Metrics

### Halstead Metrics

**Operators**: Keywords, operators
**Operands**: Variables, constants

**Metrics**:
- **Vocabulary**: n = n1 + n2 (unique operators + operands)
- **Length**: N = N1 + N2 (total operators + operands)
- **Volume**: V = N * log2(n)
- **Difficulty**: D = (n1/2) * (N2/n2)
- **Effort**: E = D * V

**Interpretation**:
- Higher values = more complex
- Use for relative comparison

### Import Complexity

**Metrics**:
- Number of imports per file
- Cyclic imports (critical issue)
- Import depth

**Thresholds**:
- **< 10 imports**: Good
- **10-20 imports**: Acceptable
- **> 20 imports**: Consider splitting module

## React/JavaScript-Specific Metrics

### Component Metrics

**Props Count**:
- **< 5**: Good
- **5-7**: Acceptable
- **> 7**: Consider composition or context

**Hooks Count per Component**:
- **< 5**: Good
- **5-10**: Acceptable
- **> 10**: Extract custom hooks

**JSX Nesting Depth**:
- **< 5 levels**: Good
- **5-7 levels**: Acceptable
- **> 7 levels**: Extract components

### Bundle Size Metrics

**Thresholds**:
- **Initial JS**: < 200KB (gzipped)
- **Total JS**: < 500KB (gzipped)
- **Per route**: < 100KB (gzipped)

**First Contentful Paint (FCP)**:
- **Good**: < 1.8s
- **Needs Improvement**: 1.8-3.0s
- **Poor**: > 3.0s

**Time to Interactive (TTI)**:
- **Good**: < 3.8s
- **Needs Improvement**: 3.8-7.3s
- **Poor**: > 7.3s

## Analysis Tools Output

### Radon (Python)

```bash
radon cc myfile.py -s
# A: 1-5 (Low risk)
# B: 6-10 (Moderate risk)
# C: 11-20 (High risk)
# D: 21-50 (Very high risk)
# F: > 50 (Unmaintainable)

radon mi myfile.py -s
# A: 85-100 (Excellent)
# B: 65-84 (Good)
# C: 40-64 (Fair)
# D: 20-39 (Poor)
# F: 0-19 (Critical)
```

### ESLint (JavaScript)

```bash
eslint --format json myfile.js
# Outputs:
# - severity: 0 (off), 1 (warning), 2 (error)
# - ruleId: specific rule violated
# - message: description
# - line, column: location
```

### SonarQube

**Quality Gate Conditions**:
- Bugs: 0
- Vulnerabilities: 0
- Code Smells: < Rating A (< 5)
- Coverage: > 80%
- Duplications: < 3%
- Maintainability: > Rating A

**Ratings**:
- **A**: 0-5% technical debt ratio
- **B**: 6-10%
- **C**: 11-20%
- **D**: 21-50%
- **E**: > 50%

## Metrics Dashboard

**Essential Metrics to Track**:

1. **Complexity Trends**
   - Average CC over time
   - Files with CC > 10

2. **Technical Debt**
   - TD Ratio
   - Remediation time

3. **Quality Trends**
   - Maintainability Index
   - Code duplication %

4. **Test Health**
   - Coverage %
   - Tests passing %

5. **Hot Spots**
   - High churn + high complexity files
   - Most changed files

## Interpreting Reports

### Priority Matrix

```
Impact vs Effort:
┌─────────────┬─────────────┐
│ High Impact │ High Impact │
│ Low Effort  │ High Effort │
│ (DO FIRST)  │ (PLAN)      │
├─────────────┼─────────────┤
│ Low Impact  │ Low Impact  │
│ Low Effort  │ High Effort │
│ (MAYBE)     │ (AVOID)     │
└─────────────┴─────────────┘
```

### Risk Assessment

**High Risk Refactoring**:
- CC > 20
- No test coverage
- Core business logic
- Frequently changed
- → Manual, careful, incremental

**Low Risk Refactoring**:
- CC 10-15
- Good test coverage
- Utility functions
- Stable code
- → Can automate

## Best Practices

1. **Baseline First**: Measure before refactoring
2. **Set Targets**: Define acceptable thresholds
3. **Track Trends**: Monitor over time, not point-in-time
4. **Context Matters**: Some complexity is inherent
5. **Prioritize**: Focus on high-impact, low-effort wins
6. **Automate**: Integrate metrics into CI/CD
7. **Review Regularly**: Weekly/sprint reviews
