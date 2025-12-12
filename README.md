# Claude Code Skills Marketplace

Production-ready skills for Claude Code that enhance your development workflows.

## Quick Start

### 1. Add Marketplace

```bash
/plugin marketplace add dldudtjr888/agent_skills
```

### 2. Install Plugins

```bash
# Install development workflow skills
/plugin install dev-skills@claude-dev-skills

# Install AI/LLM development skills
/plugin install ai-skills@claude-dev-skills
```

## Available Plugins

### dev-skills

Development workflow skills for code quality and project management.

| Skill | Description |
|-------|-------------|
| **code-refactoring-analysis** | Production-ready multi-dimensional code refactoring for Python and Next.js (React/JavaScript/TypeScript) projects |
| **sql-production-analyzer** | Deep analysis of database implementation in production environments (SQL, NoSQL, VectorDB, GraphDB) |
| **project-planner** | Deep project analysis and implementation planning for feature additions, refactoring, bug fixes |
| **task-decomposer** | Transform natural language plans into executable concrete tasks with dependency mapping |
| **project-docs-manager** | Comprehensive project documentation management |

### ai-skills

AI and LLM development skills.

| Skill | Description |
|-------|-------------|
| **agents-sdk-builder** | Guide for building production-ready multi-agent AI applications using OpenAI Agents Python SDK |

## Manual Installation

If you prefer to install skills manually without the marketplace:

```bash
# Clone the repository
git clone https://github.com/dldudtjr888/agent_skills.git

# Copy skills to your Claude Code skills directory
cp -r agent_skills/skills/* ~/.claude/skills/
```

## Skill Structure

Each skill follows the Claude Code Agent Skills specification:

```
skill-name/
├── SKILL.md          # Main skill definition with YAML frontmatter
├── references/       # Optional: Reference documentation
├── scripts/          # Optional: Helper scripts
└── assets/           # Optional: Assets and resources
```

## Contributing

1. Fork this repository
2. Create your skill in `skills/your-skill-name/`
3. Add a `SKILL.md` with proper frontmatter
4. Update `marketplace.json` to include your skill
5. Submit a Pull Request

## License

MIT License - see [LICENSE](LICENSE) for details.

## Resources

- [Claude Code Skills Documentation](https://docs.claude.com/en/docs/claude-code/skills)
- [Anthropic Official Skills Repository](https://github.com/anthropics/skills)
- [Agent Skills Announcement](https://www.anthropic.com/news/skills)
