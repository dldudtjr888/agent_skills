# Documentation Quality Checklist

Comprehensive quality standards for naviseoAI documentation.

## After Writing (9 items)

### ✅ Content Quality

- [ ] **Purpose is clear** - First paragraph explains what/why
- [ ] **Quick start included** - 5 minutes to key functionality
- [ ] **Examples work** - Copy-paste and run successfully
- [ ] **Code blocks have language** - ```python not just ```

### ✅ Metadata

- [ ] **Author/date specified** - `**작성**: 2025-01-20, Author`
- [ ] **References linked** - Related docs linked at bottom

### ✅ Safety

- [ ] **No sensitive info** - No API keys, passwords, secrets
- [ ] **Links verified** - All internal links work
- [ ] **No orphaned TODOs** - All TODOs addressed or removed

## Periodic Review (Monthly)

### 🔄 Freshness

- [ ] **Remove deprecated** - Mark or delete outdated content
- [ ] **Update screenshots** - If UI changed
- [ ] **Fix broken links** - Test all URLs
- [ ] **Deduplicate** - Merge redundant sections
- [ ] **Verify accuracy** - Code matches documentation

## Auto-Checkable Items

These can be verified by `validate_document.py`:

✅ **Automated checks**:
- Required sections present (작성, 목적, 빠른 시작)
- No sensitive patterns (API keys, passwords)
- Internal links valid
- Code blocks have language tags

⚠️ **Manual checks required**:
- Content quality and clarity
- Examples actually work
- Screenshots up to date
- Technical accuracy

## Document-Specific Standards

### Plan Documents (`docs/plan/`)

- [ ] Filename: `{YYYYMMDDHHMM}_{task-name}.md`
- [ ] Required sections: 목표, 배경, 범위, 작업 단계
- [ ] Checkboxes for tracking
- [ ] Phase/dependency markers
- [ ] Success criteria defined

### Status Documents (`docs/status/`)

- [ ] Always current (update with code changes)
- [ ] Diagrams if architecture
- [ ] Version info if applicable
- [ ] Last updated date

### Analysis Documents (`docs/analysis/`)

- [ ] Date of analysis
- [ ] Methodology explained
- [ ] Evidence/data provided
- [ ] Conclusions actionable
- [ ] Next steps clear

### Task Documents (`docs/tasks/`)

- [ ] Phase number in title
- [ ] Priority marker (🔴/🟡/🟢)
- [ ] Estimated time
- [ ] Verification checklist
- [ ] Dependencies listed

## Quality Metrics

**Target standards**:
- All documents have metadata (작성): **100%**
- Documents with Quick Start: **>80%**
- Documents passing validation: **>95%**
- Broken links: **<5%**
- Age < 3 months: **>70%** (status docs)

## Common Issues

| Issue | Detection | Fix |
|-------|-----------|-----|
| Missing metadata | Auto-check | Add `**작성**: DATE, AUTHOR` |
| No Quick Start | Manual review | Add ## 빠른 시작 section |
| Broken links | Auto-check | Update or remove link |
| Sensitive data | Auto-check | Remove and use .env |
| Outdated screenshots | Manual review | Regenerate screenshots |
| Code doesn't run | Manual testing | Update examples |

## Validation Workflow

1. **Write document** - Follow template
2. **Self-check** - Use checklist above
3. **Auto-validate** - Run `validate_document.py`
4. **Peer review** - Ask for feedback
5. **Periodic audit** - Monthly review

## Tools

```bash
# Validate document
python scripts/validate_document.py docs/plan/my_plan.md

# Check sync requirements
python scripts/sync_checker.py

# Generate from template
python scripts/generate_doc.py assets plan_template.md docs/plan/new.md
```
