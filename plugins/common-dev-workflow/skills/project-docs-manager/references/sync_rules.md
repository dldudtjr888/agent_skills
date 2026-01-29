# Documentation Sync Rules

Complete reference for naviseoAI documentation synchronization.

## Change Type → Document Mapping

### New Agent Added

**Files to update**:
- [ ] `AGENTS.md` - Add to agent list, update architecture section
- [ ] `docs/status/architecture.md` - Update architecture diagram
- [ ] `navis/README.md` - Add agent documentation
- [ ] `config/agents.yaml` - Add agent configuration
- [ ] `prompts/{agent}_agent.yaml` - Create prompt file

**How to verify**: Grep for agent name across all these files

### MCP Tool Added/Modified

**Files to update**:
- [ ] `mcps/{server}/README.md` - Update tool list
- [ ] `docs/status/architecture.md` - Update tool count
- [ ] `docs/status/mcp_guide.md` - Add usage examples

**How to verify**: Count tools in architecture.md matches implementation

### Configuration Changed

**Files to update**:
- [ ] `config/README.md` - Document new options
- [ ] `.env.example` - Add new environment variables
- [ ] `AGENTS.md` - Update environment section
- [ ] Related agent README if agent-specific

**How to verify**: All config keys documented in README

### Prompt Changed

**Files to update**:
- [ ] `prompts/README.md` - Update version history if needed
- [ ] `prompts/{agent}_agent.yaml` - Increment version
- [ ] Related documentation mentioning prompt behavior

**How to verify**: Test agent with new prompt

### SDK Updated

**Files to update**:
- [ ] `docs/sdk_info/openai_agents.md` - API changes
- [ ] `pyproject.toml` - Version number
- [ ] Related examples using updated API

**How to verify**: All examples still run

### Architecture Changed

**Files to update**:
- [ ] `AGENTS.md` - Major changes
- [ ] `docs/status/architecture.md` - Diagrams
- [ ] All affected module READMEs

**How to verify**: Architecture doc matches code structure

## Dependency Graph

```
AGENTS.md (hub)
    ├── architecture.md
    ├── development_guide.md
    ├── mcp_guide.md
    ├── config/README.md
    └── prompts/README.md

config/agents.yaml
    ├── prompts/*.yaml
    └── .env.example

Code changes
    └── Trigger sync rules above
```

## Update Priorities

| Priority | Timing | Examples |
|----------|--------|----------|
| 🔴 Critical | Immediate | Breaking changes, security |
| 🟡 High | Same day | New features, config changes |
| 🟢 Normal | Weekly | Minor improvements, typos |

## Verification Commands

```bash
# Check for broken links
grep -r "\[.*\](" docs/ | grep -v "http" | while read line; do
  # Extract and verify local links
done

# Check for TODO markers
grep -r "TODO" docs/

# Verify environment variables documented
diff <(grep "^[A-Z_]*=" .env.example | cut -d= -f1 | sort) \
     <(grep "^-.*\`" config/README.md | grep -o "[A-Z_]*" | sort)
```
