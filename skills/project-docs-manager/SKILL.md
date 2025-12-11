---
name: project-docs-manager
description: |
  Comprehensive documentation management for software projects with automatic sync checking,
  quality validation, and template-based generation. Use this skill when working with naviseoAI
  or similar projects that require: (1) Creating new documentation (plans, features, analysis),
  (2) Validating document quality against project standards, (3) Checking which documents need
  updating after code changes, (4) Understanding documentation structure and sync rules,
  (5) Ensuring documentation completeness and consistency. Supports Korean and English documentation.
---

# Project Documentation Manager

Automated documentation management for naviseoAI and similar multi-component projects.

## Core Capabilities

1. **Document Generation** - Create docs from templates with auto-metadata
2. **Quality Validation** - Check against project standards
3. **Sync Checking** - Identify docs needing updates after code changes
4. **Structure Navigation** - Understand documentation organization

## Quick Start

### Generate New Document

```bash
# Create plan document
python scripts/generate_doc.py assets plan_template.md \
  docs/plan/202501201430_new_feature.md \
  TASK_NAME="Add Authentication"

# Create feature doc
python scripts/generate_doc.py assets feature_template.md \
  docs/status/auth_guide.md \
  FEATURE_NAME="JWT Authentication"
```

### Validate Document Quality

```bash
# Check document against standards
python scripts/validate_document.py docs/plan/my_plan.md

# Output:
# ✅ Document is valid!
# OR
# ❌ ERRORS:
#   - Missing required section: ##\s+(목적|개요)
#   - Sensitive info detected (API Key): 1 occurrence(s)
```

### Check Sync Requirements

```bash
# After code changes, check which docs need updating
python scripts/sync_checker.py .

# Output:
# 📝 Documentation Update Checklist
# Detected changes: new_agent, config_change
# Files to update:
#   - [ ] AGENTS.md
#   - [ ] docs/status/architecture.md
#   - [ ] config/README.md
```

## Document Structure

naviseoAI organizes documentation into 15 categories:

```
docs/
├── plan/           # Work plans (YYYYMMDDHHMM_task.md)
├── tasks/          # Phase-based execution tasks
├── queue/          # Backlog
├── status/         # Architecture, guides (always current)
├── analysis/       # Deep analysis reports
├── ref/            # Design references
├── memo/           # User notes (DO NOT MODIFY)
├── info/           # Information
└── sdk_info/       # SDK references
```

**Root docs**: `AGENTS.md` (project overview), `CLAUDE.md` (AI guide)

**Module docs**: `config/`, `prompts/`, `memory/`, `navis/`, `mcps/`, `tests/`

## Templates Available

### Plan Template (`assets/plan_template.md`)

For work planning before implementation:
- Filename: `{YYYYMMDDHHMM}_{task-name}.md`
- Sections: 목표, 배경, 범위, 작업 단계, 위험 요소, 테스트, 문서 체크리스트
- Variables: `{TASK_NAME}`, `{DATE}`, `{AUTHOR}`

### Feature Template (`assets/feature_template.md`)

For feature documentation:
- Sections: 목적, 빠른 시작, 상세 설명, 예제, 문제 해결
- Variables: `{FEATURE_NAME}`, `{DATE}`, `{AUTHOR}`

### Analysis Template (`assets/analysis_template.md`)

For code analysis reports:
- Sections: 종합 평가, Critical/Important Issues, Recommendations, Action Items
- Variables: `{ANALYSIS_TITLE}`, `{DATE}`, `{AUTHOR}`

## Sync Rules

**Read [references/sync_rules.md](references/sync_rules.md) for complete sync rules.**

Quick reference:

| Change Type | Docs to Update |
|-------------|----------------|
| New agent | AGENTS.md, architecture.md, navis/README.md |
| MCP tool | mcps/{server}/README.md, architecture.md, mcp_guide.md |
| Config | config/README.md, .env.example, AGENTS.md |
| Prompt | prompts/README.md, prompts/{agent}_agent.yaml |
| SDK | docs/sdk_info/openai_agents.md, pyproject.toml |

## Quality Standards

**Read [references/quality_checklist.md](references/quality_checklist.md) for full checklist.**

All documents must have:
- ✅ Metadata: `**작성**: YYYY-MM-DD, Author`
- ✅ Purpose: Clear objective in first paragraph
- ✅ Quick Start: 5-minute getting started (recommended)
- ✅ No sensitive info: No API keys, passwords

Run validation: `python scripts/validate_document.py <file>`

## Workflows

### Creating New Work Plan

1. **Generate from template**:
   ```bash
   TIMESTAMP=$(date +%Y%m%d%H%M)
   python scripts/generate_doc.py assets plan_template.md \
     docs/plan/${TIMESTAMP}_task_name.md \
     TASK_NAME="Your Task Name"
   ```

2. **Fill in sections**:
   - 목표: What are you building?
   - 배경: Why is this needed?
   - 범위: What's included/excluded?
   - 작업 단계: Break into phases with checkboxes

3. **Track progress**:
   - Update checkboxes as you complete tasks
   - Add notes in "진행 노트" if issues arise

### Validating Documentation

**Before committing**:
```bash
# Validate document
python scripts/validate_document.py docs/plan/my_plan.md

# Fix any errors
# - Add missing sections
# - Remove sensitive info
# - Fix broken links

# Re-validate
python scripts/validate_document.py docs/plan/my_plan.md
```

### Checking Sync After Changes

**After code changes**:
```bash
# Check what docs need updating
python scripts/sync_checker.py .

# Follow generated checklist
# Update each listed document
# Verify changes with git diff
```

## Common Tasks

### "Create a plan for new feature"

```bash
# Generate plan
TIMESTAMP=$(date +%Y%m%d%H%M)
python scripts/generate_doc.py assets plan_template.md \
  docs/plan/${TIMESTAMP}_add_new_feature.md \
  TASK_NAME="Add New Feature"

# Edit: Fill in 목표, 배경, 범위, 작업 단계
# Validate
python scripts/validate_document.py docs/plan/${TIMESTAMP}_add_new_feature.md
```

### "I added a new agent, which docs need updating?"

```bash
# Check sync requirements
python scripts/sync_checker.py .

# Output will list:
# - AGENTS.md (add to agent list)
# - docs/status/architecture.md (update diagram)
# - navis/README.md (add agent doc)
# - config/agents.yaml (add config)
# - prompts/{agent}_agent.yaml (create prompt)
```

### "Validate this document meets standards"

```bash
python scripts/validate_document.py <file_path>

# Fix reported errors:
# - Add missing metadata: **작성**: 2025-01-20, Your Name
# - Add missing sections: ## 목적, ## 빠른 시작
# - Remove sensitive info
# - Fix broken links
```

### "Generate analysis report"

```bash
python scripts/generate_doc.py assets analysis_template.md \
  docs/analysis/performance_analysis.md \
  ANALYSIS_TITLE="Performance Analysis" \
  AUTHOR="Your Name"
```

## Best Practices

1. **Always use templates** - Ensures consistency and completeness
2. **Validate before commit** - Catch issues early
3. **Check sync after changes** - Keep docs in sync with code
4. **Update timestamps** - Use YYYYMMDDHHMM format for plans
5. **Track with checkboxes** - [ ] for pending, [x] for done
6. **Reference related docs** - Link to architecture, guides, etc.

## Project-Specific Notes

**naviseoAI conventions**:
- **Korean primary**: Internal docs, comments (한국어 우선)
- **English required**: Variables, functions, commit messages (영어 필수)
- **Metadata format**: `**작성**: YYYY-MM-DD, Author`
- **Plan filename**: `{YYYYMMDDHHMM}_{task-name}.md`
- **Sync rules**: AGENTS.md lists all sync requirements

**docs/memo/** is user's personal space - DO NOT MODIFY unless explicitly requested

## Troubleshooting

**"Template not found"**:
- Ensure you're in project root
- Template path is relative to template_dir argument
- Templates are in `assets/` directory

**"Validation failed"**:
- Read error messages carefully
- Most common: missing metadata, missing sections
- Fix and re-run validation

**"No sync rules match my change"**:
- Check [references/sync_rules.md](references/sync_rules.md) for full list
- If truly new change type, update sync_checker.py CHANGE_PATTERNS

## Files in This Skill

**Scripts** (executable):
- `scripts/validate_document.py` - Quality validation
- `scripts/sync_checker.py` - Sync requirement checker
- `scripts/generate_doc.py` - Template-based generation

**References** (load as needed):
- `references/sync_rules.md` - Complete sync rules
- `references/quality_checklist.md` - Full quality standards

**Assets** (templates):
- `assets/plan_template.md` - Work plan template
- `assets/feature_template.md` - Feature doc template
- `assets/analysis_template.md` - Analysis report template

When in doubt, read the reference files for comprehensive details.
