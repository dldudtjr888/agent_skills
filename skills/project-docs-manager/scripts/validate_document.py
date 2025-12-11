#!/usr/bin/env python3
"""
Document Quality Validator for naviseoAI project.

Validates that documentation follows project guidelines:
- Required sections (작성일/작성자, 목적, 빠른 시작)
- Template compliance
- Link validity
- No sensitive information (API keys, passwords)
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple


class DocumentValidator:
    """Validates documentation against project standards."""

    # Required sections for all documents
    REQUIRED_SECTIONS = [
        r"^#\s+",  # Title (H1)
        r"\*\*작성\*\*:",  # Author/Date
        r"##\s+(목적|개요|목표)",  # Purpose/Overview
    ]

    # Recommended sections
    RECOMMENDED_SECTIONS = [
        r"##\s+(빠른\s*시작|Quick\s*Start)",  # Quick start
        r"##\s+참고",  # References
    ]

    # Sensitive patterns to detect
    SENSITIVE_PATTERNS = [
        (r"sk-[a-zA-Z0-9]{48}", "OpenAI API Key"),
        (r"[A-Z0-9]{20}", "AWS Access Key (potential)"),
        (r"password\s*[=:]\s*['\"]?[\w@#$%^&*]+", "Password"),
        (r"DB_PASSWORD\s*=\s*['\"][\w@#$%^&*]+", "Database Password"),
    ]

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.content = ""
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate(self) -> Tuple[bool, List[str], List[str]]:
        """
        Validate the document.

        Returns:
            (is_valid, errors, warnings)
        """
        if not self.file_path.exists():
            self.errors.append(f"File not found: {self.file_path}")
            return False, self.errors, self.warnings

        self.content = self.file_path.read_text(encoding="utf-8")

        # Run validations
        self._check_required_sections()
        self._check_recommended_sections()
        self._check_sensitive_info()
        self._check_links()

        is_valid = len(self.errors) == 0
        return is_valid, self.errors, self.warnings

    def _check_required_sections(self):
        """Check for required sections."""
        for pattern in self.REQUIRED_SECTIONS:
            if not re.search(pattern, self.content, re.MULTILINE):
                self.errors.append(f"Missing required section: {pattern}")

    def _check_recommended_sections(self):
        """Check for recommended sections."""
        for pattern in self.RECOMMENDED_SECTIONS:
            if not re.search(pattern, self.content, re.MULTILINE):
                self.warnings.append(f"Missing recommended section: {pattern}")

    def _check_sensitive_info(self):
        """Check for sensitive information."""
        for pattern, name in self.SENSITIVE_PATTERNS:
            matches = re.findall(pattern, self.content, re.IGNORECASE)
            if matches:
                self.errors.append(f"Sensitive info detected ({name}): {len(matches)} occurrence(s)")

    def _check_links(self):
        """Check for broken internal links."""
        # Find markdown links
        link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        links = re.findall(link_pattern, self.content)

        base_dir = self.file_path.parent

        for text, url in links:
            # Skip external links
            if url.startswith(('http://', 'https://', '#')):
                continue

            # Check relative links
            target_path = (base_dir / url).resolve()
            if not target_path.exists():
                self.warnings.append(f"Broken link: [{text}]({url})")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: validate_document.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    validator = DocumentValidator(file_path)
    is_valid, errors, warnings = validator.validate()

    # Print results
    print(f"\n📄 Validating: {file_path}\n")

    if errors:
        print("❌ ERRORS:")
        for error in errors:
            print(f"  - {error}")

    if warnings:
        print("\n⚠️  WARNINGS:")
        for warning in warnings:
            print(f"  - {warning}")

    if is_valid and not warnings:
        print("✅ Document is valid!")
    elif is_valid:
        print("\n✅ Document is valid (with warnings)")
    else:
        print("\n❌ Document validation failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
