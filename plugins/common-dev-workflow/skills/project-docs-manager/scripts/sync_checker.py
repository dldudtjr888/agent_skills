#!/usr/bin/env python3
"""
Documentation Sync Checker for naviseoAI project.

Analyzes code/config changes and identifies which documentation needs updating
based on project sync rules.
"""

import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Set


class SyncChecker:
    """Checks which documents need updating based on changes."""

    # Change type -> Affected documents mapping
    SYNC_RULES = {
        "new_agent": [
            "AGENTS.md",
            "docs/status/architecture.md",
            "navis/README.md",
        ],
        "mcp_tool": [
            "mcps/{server}/README.md",
            "docs/status/architecture.md",
            "docs/status/mcp_guide.md",
        ],
        "config_change": [
            "config/README.md",
            ".env.example",
            "AGENTS.md",
        ],
        "prompt_change": [
            "prompts/README.md",
            "prompts/{agent}_agent.yaml",
        ],
        "sdk_update": [
            "docs/sdk_info/openai_agents.md",
            "pyproject.toml",
        ],
        "architecture_change": [
            "AGENTS.md",
            "docs/status/architecture.md",
            "관련 README들",
        ],
    }

    # File patterns to detect change types
    CHANGE_PATTERNS = {
        "new_agent": [
            r"navis/.*_agent\.py$",
        ],
        "mcp_tool": [
            r"mcps/.*/tools\.py$",
            r"mcps/.*/resources\.py$",
        ],
        "config_change": [
            r"config/.*\.yaml$",
            r"\.env",
        ],
        "prompt_change": [
            r"prompts/.*\.yaml$",
        ],
        "sdk_update": [
            r"pyproject\.toml",
        ],
    }

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.changed_files: Set[str] = set()
        self.change_types: Set[str] = set()
        self.docs_to_update: Set[str] = set()

    def analyze_changes(self, git_diff: bool = True) -> Dict[str, List[str]]:
        """
        Analyze changes and return documents to update.

        Args:
            git_diff: Use git diff to detect changes (default: True)

        Returns:
            Dictionary mapping change types to document lists
        """
        if git_diff:
            self._get_git_changes()

        self._detect_change_types()
        self._identify_docs_to_update()

        return {
            "change_types": list(self.change_types),
            "docs_to_update": list(self.docs_to_update),
        }

    def _get_git_changes(self):
        """Get changed files from git."""
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True,
            )
            self.changed_files = set(result.stdout.strip().split("\n"))
        except subprocess.CalledProcessError:
            print("⚠️  git diff failed, using manual file list")

    def _detect_change_types(self):
        """Detect change types from file patterns."""
        for change_type, patterns in self.CHANGE_PATTERNS.items():
            for file in self.changed_files:
                for pattern in patterns:
                    if re.search(pattern, file):
                        self.change_types.add(change_type)
                        break

    def _identify_docs_to_update(self):
        """Identify documents that need updating."""
        for change_type in self.change_types:
            if change_type in self.SYNC_RULES:
                self.docs_to_update.update(self.SYNC_RULES[change_type])

    def generate_checklist(self) -> str:
        """Generate markdown checklist for document updates."""
        if not self.docs_to_update:
            return "✅ No documentation updates needed"

        checklist = "## 📝 Documentation Update Checklist\n\n"
        checklist += f"**Detected changes**: {', '.join(self.change_types)}\n\n"
        checklist += "**Files to update**:\n"

        for doc in sorted(self.docs_to_update):
            checklist += f"- [ ] {doc}\n"

        checklist += "\n**How to update**: Review each file and apply sync rules from AGENTS.md\n"

        return checklist


def main():
    """Main entry point."""
    project_root = sys.argv[1] if len(sys.argv) > 1 else "."

    checker = SyncChecker(project_root)
    result = checker.analyze_changes()

    print("\n🔍 Documentation Sync Analysis\n")
    print(f"Changed files: {len(checker.changed_files)}")
    print(f"Change types detected: {result['change_types']}")
    print(f"Documents to update: {len(result['docs_to_update'])}\n")

    print(checker.generate_checklist())


if __name__ == "__main__":
    main()
