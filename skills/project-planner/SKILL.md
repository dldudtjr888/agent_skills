---
name: project-planner
description: Deep project analysis and implementation planning for feature additions, refactoring, bug fixes, and modifications. Use when user asks to add features, refactor code, fix bugs, modify functionality, or create implementation plans for existing projects.
---

# Project Planner

## Workflow

```
1. Clarify → 2. Analyze → 3. Plan
```

## Phase 1: Clarify Requirements

Before analyzing, confirm with user:
- **Change type**: Feature / Refactor / Bugfix / Modification
- **Scope**: Specific files or project-wide?
- **Constraints**: Backwards compatibility? Deadline? Dependencies?
- **Success criteria**: How do we know it's done?

## Phase 2: Project Analysis

### Step 1: Project Overview

```bash
view /project                    # Directory structure
view package.json               # or requirements.txt, go.mod, Cargo.toml
```

Identify:
- Tech stack (language, framework, DB, testing)
- Project structure pattern (feature-based, layered, etc.)
- Build/dev scripts

### Step 2: Entry Points & Flow

Examine in order:
1. **Main entry**: `index.ts`, `main.py`, `app.ts`, `server.ts`
2. **Routing**: Where URLs/endpoints are defined
3. **Config**: `.env*`, framework configs, `tsconfig.json`
4. **Schema**: Database models, API types, validation schemas

### Step 3: Change Area Deep Dive

**For the specific area being changed:**
- Read the target files completely
- Find similar existing features → extract patterns to follow
- Trace data flow: where does input come from? where does output go?
- Check for shared state, context, or global dependencies

**Find related tests:**
```
__tests__/, tests/, test/, spec/
*.test.ts, *.spec.ts, test_*.py, *_test.py
```

### Step 4: Dependency Mapping

**Upstream (what target depends on):**
- Read imports in target files
- Understand APIs being consumed

**Downstream (what depends on target):**
- Search for imports of target file
- These files need verification after changes

**Shared resources:**
- Database tables/collections accessed
- External APIs called
- Shared state (Redux, Context, global variables)

### Step 5: Risk Assessment

Check for these signals:

| Signal | Risk | Action |
|--------|------|--------|
| No tests for area | High | Plan to add tests first |
| Many dependents (5+) | High | Plan incremental migration |
| TODO/FIXME/HACK in area | Medium | Understand workarounds before changing |
| Complex file (300+ lines, deep nesting) | Medium | Consider refactoring first |
| Touches auth/payment/data | High | Extra review, rollback plan |
| External API integration | Medium | Check rate limits, error handling |

### Step 6: Pattern Extraction

Document these from existing code:
- **Naming**: Files, functions, variables, components
- **Error handling**: try-catch, Result types, error boundaries
- **Data fetching**: Hooks, server actions, API calls
- **State management**: Local state, global store, context
- **File organization**: Where similar code lives

## Change Type Specific Analysis

### For Features
- Find most similar existing feature → use as template
- Identify all layers to touch (DB → API → UI)
- Check if new dependencies needed

### For Refactoring
- Document current behavior (write tests if missing)
- Identify all usages to migrate
- Plan backwards-compatible intermediate steps

### For Bug Fixes
- Reproduce the bug first
- Trace execution path to find root cause
- Check for same bug pattern elsewhere

### For Modifications
- Understand why current implementation exists
- Check for dependents relying on current behavior
- Plan deprecation if breaking change

## Phase 3: Implementation Plan

### Output Template

```markdown
# Implementation Plan: [Change Name]

## Summary
- **Type**: Feature / Refactor / Bugfix / Modification
- **Risk**: Low / Medium / High
- **Effort**: [X hours/days]

## Analysis Summary

### Tech Stack
[language, framework, database, testing]

### Key Files
| File | Purpose | Action |
|------|---------|--------|
| `path/to/file.ts` | [what it does] | Create / Modify / Review |

### Dependencies
- **Imports**: [what we depend on]
- **Dependents**: [what depends on us - needs verification]

### Patterns to Follow
- Naming: [convention]
- Error handling: [pattern]
- [other patterns observed]

## Tasks

### Phase 1: Preparation [Xh]
- [ ] [Read/understand specific files]
- [ ] [Set up test environment]
- [ ] [Write failing test if applicable]

### Phase 2: Foundation [Xh]
- [ ] [Types/interfaces/schemas]
- [ ] [Database changes if any]
Parallel tasks marked with (P)

### Phase 3: Implementation [Xh]
- [ ] [Core logic] (depends on: 2.x)
- [ ] [API layer] (depends on: 2.x)
- [ ] [UI components] (depends on: 3.x)

### Phase 4: Integration [Xh]
- [ ] [Wire components together]
- [ ] [Update routing/navigation]

### Phase 5: Verification [Xh]
- [ ] [Unit tests]
- [ ] [Integration tests]
- [ ] [Manual test scenarios]
- [ ] [Update documentation]

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| [what could go wrong] | [severity] | [prevention/recovery] |

## Rollback Plan
[How to undo if deployment fails]
```

## Quick Reference

### Estimation Guide
| Scope | Effort |
|-------|--------|
| Single file, < 50 lines | < 1h |
| 2-3 files, isolated | 1-3h |
| 5+ files, cross-cutting | 4-8h |
| Architectural change | 1-3 days |

Add buffer for: unfamiliar code (1.5x), no tests (1.3x), external dependencies (1.3x)
