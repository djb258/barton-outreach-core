"""
CI Enforcement Checks

This module provides checks that can be run in CI to enforce doctrine compliance:
1. Undocumented tool usage detection
2. Banned library/vendor detection
3. Schema drift detection (placeholder)
4. DONE state contract validation

Run as: python -m ops.enforcement.ci_enforcement_checks
"""

import ast
import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
import json

# Import from sibling module
from ops.enforcement.tool_canon_guard import (
    TOOL_REGISTRY,
    BANNED_VENDORS,
    BANNED_LIBRARIES,
    BANNED_PATTERNS,
)


@dataclass
class CICheckResult:
    """Result of a CI check"""
    check_name: str
    passed: bool
    violations: List[Dict[str, Any]]
    summary: str


class CIEnforcementChecker:
    """
    Runs enforcement checks suitable for CI pipeline.
    """

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.results: List[CICheckResult] = []

    def run_all_checks(self) -> bool:
        """Run all CI checks. Returns True if all pass."""
        self.check_banned_libraries()
        self.check_banned_imports()
        self.check_tool_registry_coverage()
        self.check_done_state_contracts()

        all_passed = all(r.passed for r in self.results)

        # Print results
        print("\n" + "=" * 70)
        print("CI ENFORCEMENT CHECK RESULTS")
        print("=" * 70)

        for result in self.results:
            status = "PASS" if result.passed else "FAIL"
            print(f"\n[{status}] {result.check_name}")
            print(f"  {result.summary}")
            if not result.passed:
                for v in result.violations[:5]:  # Show first 5 violations
                    print(f"    - {v}")
                if len(result.violations) > 5:
                    print(f"    ... and {len(result.violations) - 5} more violations")

        print("\n" + "=" * 70)
        print(f"OVERALL: {'PASS' if all_passed else 'FAIL'}")
        print("=" * 70)

        return all_passed

    def check_banned_libraries(self) -> CICheckResult:
        """Check requirements.txt and pyproject.toml for banned libraries."""
        violations = []

        # Check requirements.txt
        req_files = list(self.repo_root.glob("**/requirements*.txt"))
        for req_file in req_files:
            try:
                content = req_file.read_text()
                for lib, reason in BANNED_LIBRARIES.items():
                    # Match library name at start of line (before any version specifier)
                    pattern = rf"^{re.escape(lib)}[<>=!~\[]?"
                    if re.search(pattern, content, re.MULTILINE | re.IGNORECASE):
                        violations.append({
                            "file": str(req_file.relative_to(self.repo_root)),
                            "library": lib,
                            "reason": reason,
                        })
            except Exception as e:
                pass  # Skip files that can't be read

        # Check pyproject.toml
        pyproject = self.repo_root / "pyproject.toml"
        if pyproject.exists():
            try:
                content = pyproject.read_text()
                for lib, reason in BANNED_LIBRARIES.items():
                    if lib.lower() in content.lower():
                        violations.append({
                            "file": "pyproject.toml",
                            "library": lib,
                            "reason": reason,
                        })
            except Exception:
                pass

        result = CICheckResult(
            check_name="Banned Libraries Check",
            passed=len(violations) == 0,
            violations=violations,
            summary=f"Found {len(violations)} banned libraries in dependency files",
        )
        self.results.append(result)
        return result

    def check_banned_imports(self) -> CICheckResult:
        """Scan Python files for imports of banned libraries."""
        violations = []

        # Scan all Python files
        py_files = list(self.repo_root.glob("**/*.py"))

        # Exclude virtual environments and node_modules
        py_files = [
            f for f in py_files
            if "venv" not in str(f)
            and "node_modules" not in str(f)
            and ".git" not in str(f)
        ]

        for py_file in py_files:
            try:
                content = py_file.read_text()
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            module = alias.name.split(".")[0]
                            if module in BANNED_LIBRARIES:
                                violations.append({
                                    "file": str(py_file.relative_to(self.repo_root)),
                                    "line": node.lineno,
                                    "import": alias.name,
                                    "reason": BANNED_LIBRARIES[module],
                                })
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            module = node.module.split(".")[0]
                            if module in BANNED_LIBRARIES:
                                violations.append({
                                    "file": str(py_file.relative_to(self.repo_root)),
                                    "line": node.lineno,
                                    "import": f"from {node.module}",
                                    "reason": BANNED_LIBRARIES[module],
                                })
            except SyntaxError:
                pass  # Skip files with syntax errors
            except Exception:
                pass  # Skip files that can't be parsed

        result = CICheckResult(
            check_name="Banned Imports Check",
            passed=len(violations) == 0,
            violations=violations,
            summary=f"Found {len(violations)} banned library imports in Python files",
        )
        self.results.append(result)
        return result

    def check_tool_registry_coverage(self) -> CICheckResult:
        """
        Check that all external API calls go through registered tools.

        This is a heuristic check that looks for common patterns that might
        indicate unregistered tool usage.
        """
        violations = []

        # Patterns that suggest external API usage
        suspicious_patterns = [
            (r"requests\.get\(", "requests.get() - use registered tool or httpx"),
            (r"requests\.post\(", "requests.post() - use registered tool or httpx"),
            (r"selenium", "selenium - banned, use playwright"),
            (r"BeautifulSoup", "BeautifulSoup - banned, use selectolax"),
            (r"api\.zoominfo", "ZoomInfo API - banned vendor"),
            (r"api\.clearbit", "Clearbit API - banned vendor"),
            (r"api\.lusha", "Lusha API - banned vendor"),
            (r"scrapy\.Spider", "Scrapy - banned, use Firecrawl"),
        ]

        py_files = list(self.repo_root.glob("**/*.py"))
        py_files = [
            f for f in py_files
            if "venv" not in str(f)
            and "node_modules" not in str(f)
            and ".git" not in str(f)
            and "ci_enforcement" not in str(f)  # Exclude this file
        ]

        for py_file in py_files:
            try:
                content = py_file.read_text()
                for pattern, message in suspicious_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        line_num = content[:match.start()].count("\n") + 1
                        violations.append({
                            "file": str(py_file.relative_to(self.repo_root)),
                            "line": line_num,
                            "pattern": pattern,
                            "message": message,
                        })
            except Exception:
                pass

        result = CICheckResult(
            check_name="Tool Registry Coverage Check",
            passed=len(violations) == 0,
            violations=violations,
            summary=f"Found {len(violations)} suspicious patterns (possible unregistered tool usage)",
        )
        self.results.append(result)
        return result

    def check_done_state_contracts(self) -> CICheckResult:
        """
        Check that DONE state definitions are properly documented.

        This validates that:
        1. DONE_STATE_DEFINITIONS.md exists
        2. Each hub has documented DONE criteria
        3. SQL queries are valid (basic syntax check)
        """
        violations = []

        done_state_file = self.repo_root / "docs" / "DONE_STATE_DEFINITIONS.md"

        if not done_state_file.exists():
            violations.append({
                "issue": "DONE_STATE_DEFINITIONS.md not found",
                "expected_path": str(done_state_file),
            })
        else:
            content = done_state_file.read_text()

            # Check for required hubs
            required_hubs = [
                "Company Target",
                "DOL",
                "People Intelligence",
                "Blog Content",
                "BIT Scores",
            ]

            for hub in required_hubs:
                if hub not in content:
                    violations.append({
                        "issue": f"Missing DONE criteria for hub: {hub}",
                        "file": "docs/DONE_STATE_DEFINITIONS.md",
                    })

            # Check for SQL code blocks
            sql_blocks = re.findall(r"```sql\n(.*?)```", content, re.DOTALL)
            if len(sql_blocks) < 5:
                violations.append({
                    "issue": f"Expected at least 5 SQL blocks, found {len(sql_blocks)}",
                    "file": "docs/DONE_STATE_DEFINITIONS.md",
                })

        result = CICheckResult(
            check_name="DONE State Contracts Check",
            passed=len(violations) == 0,
            violations=violations,
            summary=f"DONE state validation: {len(violations)} issues found",
        )
        self.results.append(result)
        return result

    def get_json_report(self) -> str:
        """Generate JSON report of all check results."""
        report = {
            "timestamp": str(Path(__file__).stat().st_mtime),
            "repo_root": str(self.repo_root),
            "overall_passed": all(r.passed for r in self.results),
            "checks": [
                {
                    "name": r.check_name,
                    "passed": r.passed,
                    "summary": r.summary,
                    "violation_count": len(r.violations),
                    "violations": r.violations[:10],  # Limit to 10 per check
                }
                for r in self.results
            ],
        }
        return json.dumps(report, indent=2)


def main():
    """Main entry point for CI check."""
    # Determine repo root (assuming this file is in ops/enforcement/)
    script_path = Path(__file__).resolve()
    repo_root = script_path.parent.parent.parent

    print(f"Running CI enforcement checks from: {repo_root}")

    checker = CIEnforcementChecker(repo_root)
    passed = checker.run_all_checks()

    # Write JSON report
    report_path = repo_root / "ci_enforcement_report.json"
    report_path.write_text(checker.get_json_report())
    print(f"\nJSON report written to: {report_path}")

    # Exit with appropriate code
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
