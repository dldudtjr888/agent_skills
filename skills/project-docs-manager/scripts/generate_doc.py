#!/usr/bin/env python3
"""
Document Generator for naviseoAI project.

Generates documents from templates with automatic metadata (timestamp, author).
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


class DocumentGenerator:
    """Generates documents from templates."""

    def __init__(self, template_dir: str):
        self.template_dir = Path(template_dir)

    def generate(
        self,
        template_name: str,
        output_path: str,
        variables: Optional[Dict[str, str]] = None,
        author: str = "Claude (AI Assistant)",
    ) -> str:
        """
        Generate document from template.

        Args:
            template_name: Template file name (e.g., "plan_template.md")
            output_path: Output file path
            variables: Template variables to replace
            author: Document author

        Returns:
            Path to generated document
        """
        template_path = self.template_dir / template_name

        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")

        # Read template
        template = template_path.read_text(encoding="utf-8")

        # Default variables
        default_vars = {
            "{DATE}": datetime.now().strftime("%Y-%m-%d"),
            "{TIMESTAMP}": datetime.now().strftime("%Y%m%d%H%M"),
            "{AUTHOR}": author,
        }

        # Merge with user variables
        if variables:
            default_vars.update(variables)

        # Replace variables
        content = template
        for key, value in default_vars.items():
            content = content.replace(key, value)

        # Write output
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(content, encoding="utf-8")

        return str(output_file)


def main():
    """Main entry point."""
    if len(sys.argv) < 4:
        print("Usage: generate_doc.py <template_dir> <template_name> <output_path> [key=value ...]")
        print("\nExample:")
        print("  generate_doc.py assets plan_template.md docs/plan/new_plan.md TASK_NAME='Add Feature'")
        sys.exit(1)

    template_dir = sys.argv[1]
    template_name = sys.argv[2]
    output_path = sys.argv[3]

    # Parse variables (key=value format)
    variables = {}
    for arg in sys.argv[4:]:
        if "=" in arg:
            key, value = arg.split("=", 1)
            variables[f"{{{key}}}"] = value

    generator = DocumentGenerator(template_dir)

    try:
        result = generator.generate(template_name, output_path, variables)
        print(f"✅ Document generated: {result}")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
