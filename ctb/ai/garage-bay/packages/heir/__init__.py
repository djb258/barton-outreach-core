"""
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: ai/garage-bay
Barton ID: 03.01.02
Unique ID: CTB-C0D3820C
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: None
─────────────────────────────────────────────
"""

"""
HEIR compliance module for garage-mcp
"""

from .checks import run_checks, check_lowercase_filenames, check_migrations_location, check_tool_documentation, check_test_coverage, check_namespace_compliance

HEIR_VERSION = "0.1.0"

__all__ = [
    "run_checks",
    "check_lowercase_filenames", 
    "check_migrations_location",
    "check_tool_documentation",
    "check_test_coverage", 
    "check_namespace_compliance",
    "HEIR_VERSION"
]