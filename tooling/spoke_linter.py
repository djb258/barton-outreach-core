#!/usr/bin/env python3
"""
Spoke Purity Linter
===================
Enforces that spokes are I/O-only connectors with no business logic.

RULES:
  1. FORBIDDEN IMPORTS: pandas, numpy, sqlalchemy, psycopg2, requests, httpx, redis, pymongo
  2. NO BUSINESS LOGIC: if/else trees with >3 branches, complex math operations
  3. LOC WARNING: Files with >50 lines of code get a warning

EXIT CODES:
  0 = All checks passed
  1 = Violations found (blocks PR/commit)
"""

import ast
import os
import sys
from dataclasses import dataclass
from typing import List, Optional

# ============================================================================
# CONFIGURATION
# ============================================================================

SPOKES_DIR = "spokes"

# Imports that are NEVER allowed in spokes
FORBIDDEN_IMPORTS = {
    "pandas",
    "numpy",
    "scipy",
    "sklearn",
    "sqlalchemy",
    "psycopg2",
    "psycopg",
    "asyncpg",
    "redis",
    "pymongo",
    "requests",
    "httpx",
    "aiohttp",
    "urllib3",
    "boto3",
    "firebase_admin",
    "neon",
}

# Patterns in source code that indicate impurity
FORBIDDEN_PATTERNS = [
    "sqlite3",
    "psycopg2.connect",
    "psycopg.connect",
    "create_engine",
    "Session(",
    "redis.Redis",
    "MongoClient",
    "requests.get",
    "requests.post",
    "requests.put",
    "requests.delete",
    "httpx.get",
    "httpx.post",
    "aiohttp.ClientSession",
    "boto3.client",
    "firebase.initialize",
]

# Maximum lines of code before warning
MAX_LOC_BEFORE_WARNING = 50

# Maximum if/else branches before failing
MAX_CONDITIONAL_BRANCHES = 3


# ============================================================================
# DATA CLASSES
# ============================================================================


@dataclass
class Violation:
    """Represents a linter violation."""

    file_path: str
    line: Optional[int]
    rule: str
    message: str
    severity: str  # "error" or "warning"


# ============================================================================
# LINTER CHECKS
# ============================================================================


class SpokePurityLinter:
    """Lints spoke files for architectural purity."""

    def __init__(self):
        self.violations: List[Violation] = []
        self.files_checked = 0

    def lint_file(self, file_path: str) -> None:
        """Lint a single Python file."""
        self.files_checked += 1

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")
        except Exception as e:
            self.violations.append(
                Violation(
                    file_path=file_path,
                    line=None,
                    rule="READ_ERROR",
                    message=f"Could not read file: {e}",
                    severity="error",
                )
            )
            return

        # Parse AST
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            self.violations.append(
                Violation(
                    file_path=file_path,
                    line=e.lineno,
                    rule="SYNTAX_ERROR",
                    message=f"Syntax error: {e.msg}",
                    severity="error",
                )
            )
            return

        # Run all checks
        self._check_forbidden_imports(file_path, tree)
        self._check_forbidden_patterns(file_path, content)
        self._check_business_logic(file_path, tree)
        self._check_loc(file_path, lines)

    def _check_forbidden_imports(self, file_path: str, tree: ast.AST) -> None:
        """Check for forbidden imports."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_base = alias.name.split(".")[0]
                    if module_base in FORBIDDEN_IMPORTS:
                        self.violations.append(
                            Violation(
                                file_path=file_path,
                                line=node.lineno,
                                rule="FORBIDDEN_IMPORT",
                                message=f"Forbidden import: '{alias.name}' - Spokes must not import data processing or I/O libraries",
                                severity="error",
                            )
                        )

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module_base = node.module.split(".")[0]
                    if module_base in FORBIDDEN_IMPORTS:
                        self.violations.append(
                            Violation(
                                file_path=file_path,
                                line=node.lineno,
                                rule="FORBIDDEN_IMPORT",
                                message=f"Forbidden import from: '{node.module}' - Spokes must not import data processing or I/O libraries",
                                severity="error",
                            )
                        )

    def _check_forbidden_patterns(self, file_path: str, content: str) -> None:
        """Check for forbidden patterns in source code."""
        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            for pattern in FORBIDDEN_PATTERNS:
                if pattern in line:
                    self.violations.append(
                        Violation(
                            file_path=file_path,
                            line=i,
                            rule="FORBIDDEN_PATTERN",
                            message=f"Forbidden pattern: '{pattern}' - Direct I/O not allowed in spokes",
                            severity="error",
                        )
                    )

    def _check_business_logic(self, file_path: str, tree: ast.AST) -> None:
        """Check for business logic (complex conditionals, math operations)."""
        for node in ast.walk(tree):
            # Check for complex if/elif chains
            if isinstance(node, ast.If):
                branch_count = self._count_if_branches(node)
                if branch_count > MAX_CONDITIONAL_BRANCHES:
                    self.violations.append(
                        Violation(
                            file_path=file_path,
                            line=node.lineno,
                            rule="BUSINESS_LOGIC",
                            message=f"Complex conditional with {branch_count} branches (max {MAX_CONDITIONAL_BRANCHES}) - Business logic belongs in hubs",
                            severity="error",
                        )
                    )

            # Check for math operations (possible scoring/calculation logic)
            if isinstance(node, ast.BinOp):
                if isinstance(node.op, (ast.Mult, ast.Div, ast.Pow, ast.Mod)):
                    # Skip if it's inside a simple index or constant
                    parent_is_simple = False
                    if isinstance(node.left, ast.Constant) and isinstance(
                        node.right, ast.Constant
                    ):
                        parent_is_simple = True

                    if not parent_is_simple:
                        self.violations.append(
                            Violation(
                                file_path=file_path,
                                line=node.lineno,
                                rule="BUSINESS_LOGIC",
                                message="Math operation detected - Calculations belong in hub middle layer",
                                severity="warning",
                            )
                        )

            # Check for loops that might be processing data
            if isinstance(node, (ast.For, ast.While)):
                # Count nested depth
                nested_loops = sum(
                    1
                    for child in ast.walk(node)
                    if isinstance(child, (ast.For, ast.While)) and child != node
                )
                if nested_loops > 0:
                    self.violations.append(
                        Violation(
                            file_path=file_path,
                            line=node.lineno,
                            rule="BUSINESS_LOGIC",
                            message="Nested loops detected - Data processing belongs in hubs",
                            severity="warning",
                        )
                    )

    def _count_if_branches(self, node: ast.If) -> int:
        """Count total branches in an if/elif/else chain."""
        count = 1  # The if itself
        for child in node.orelse:
            if isinstance(child, ast.If):
                count += self._count_if_branches(child)
            else:
                count += 1  # else branch
                break
        return count

    def _check_loc(self, file_path: str, lines: List[str]) -> None:
        """Check lines of code."""
        # Count non-empty, non-comment lines
        loc = 0
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                loc += 1

        if loc > MAX_LOC_BEFORE_WARNING:
            self.violations.append(
                Violation(
                    file_path=file_path,
                    line=None,
                    rule="LOC_WARNING",
                    message=f"File has {loc} lines of code (recommended max: {MAX_LOC_BEFORE_WARNING}) - Consider splitting",
                    severity="warning",
                )
            )

    def lint_directory(self, directory: str) -> None:
        """Lint all Python files in a directory."""
        if not os.path.exists(directory):
            print(f"⚠️  Spokes directory '{directory}' not found")
            return

        for root, dirs, files in os.walk(directory):
            # Skip __pycache__
            dirs[:] = [d for d in dirs if d != "__pycache__"]

            for fname in files:
                if fname.endswith(".py"):
                    fpath = os.path.join(root, fname)
                    self.lint_file(fpath)

    def report(self) -> int:
        """Print report and return exit code."""
        errors = [v for v in self.violations if v.severity == "error"]
        warnings = [v for v in self.violations if v.severity == "warning"]

        print("\n" + "=" * 70)
        print("SPOKE PURITY LINTER REPORT")
        print("=" * 70)
        print(f"\nFiles checked: {self.files_checked}")
        print(f"Errors: {len(errors)}")
        print(f"Warnings: {len(warnings)}")

        if errors:
            print("\n" + "-" * 70)
            print("ERRORS (must fix)")
            print("-" * 70)
            for v in errors:
                line_info = f":{v.line}" if v.line else ""
                print(f"\n❌ [{v.rule}] {v.file_path}{line_info}")
                print(f"   {v.message}")

        if warnings:
            print("\n" + "-" * 70)
            print("WARNINGS (should fix)")
            print("-" * 70)
            for v in warnings:
                line_info = f":{v.line}" if v.line else ""
                print(f"\n⚠️  [{v.rule}] {v.file_path}{line_info}")
                print(f"   {v.message}")

        print("\n" + "=" * 70)

        if errors:
            print("❌ SPOKE PURITY CHECK FAILED")
            print("   Spokes must be I/O-only connectors with no business logic.")
            print("   Move processing code to hub middle layers.")
            return 1
        elif warnings:
            print("⚠️  SPOKE PURITY CHECK PASSED WITH WARNINGS")
            return 0
        else:
            print("✅ SPOKE PURITY CHECK PASSED")
            return 0


# ============================================================================
# MAIN
# ============================================================================


def main():
    """Main entry point."""
    print("🔍 Running Spoke Purity Linter...")

    linter = SpokePurityLinter()
    linter.lint_directory(SPOKES_DIR)
    exit_code = linter.report()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
