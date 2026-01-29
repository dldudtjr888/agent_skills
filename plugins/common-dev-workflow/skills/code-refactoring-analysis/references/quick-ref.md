# Quick Reference

Fast lookup tables for score interpretation and action mapping.

## Score Interpretation

| Score | Status | Action |
|-------|--------|--------|
| 90-100 | Excellent | Maintain |
| 75-89 | Good | Minor fixes |
| 60-74 | Fair | Plan sprint |
| 45-59 | Poor | Prioritize |
| <45 | Critical | Immediate |

## Severity Mapping

| Severity | Response Time | Examples |
|----------|---------------|----------|
| critical | Immediate | SQL injection, hardcoded secrets |
| high | 24h | Complexity >20, no auth checks |
| medium | Sprint | Complexity 10-15, code duplication |
| low | Backlog | Style issues, minor optimizations |

## Dimension Weights

| Dimension | Weight | Focus |
|-----------|--------|-------|
| Maintainability | 35% | Complexity, readability |
| Security | 25% | Vulnerabilities, auth |
| Performance | 20% | Bottlenecks, algorithms |
| Scalability | 10% | Architecture, coupling |
| Reusability | 10% | DRY, modularity |

## Common Issues → Refactoring

| Issue | Refactoring | Risk |
|-------|-------------|------|
| High complexity | Extract Method | Low |
| Long method | Split Function | Low |
| Duplicate code | Extract Common | Medium |
| Deep nesting | Guard Clauses | Low |
| God class | Extract Class | High |
| Feature envy | Move Method | Medium |

## Tool → Dimension Mapping

| Tool | Dimensions |
|------|------------|
| radon | Maintainability |
| bandit | Security |
| eslint | Maintainability, Performance |
| madge | Scalability, Reusability |
| jscpd | Reusability |

## Confidence Adjustment

| Condition | Adjustment |
|-----------|------------|
| All tools ran | +0% |
| 1 tool missing | -10% |
| 2+ tools missing | -25% |
| Partial failure | -15% |
