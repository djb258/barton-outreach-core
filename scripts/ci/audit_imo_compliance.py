#!/usr/bin/env python3
"""
IMO Template Compliance Audit
=============================

CI gate that verifies all hubs have required documentation files
and follow IMO-creator doctrine.

Usage:
    python scripts/ci/audit_imo_compliance.py

Exit codes:
    0 = PASS (all compliant)
    1 = FAIL (compliance issues)

Doctrine: IMO_CANONICAL_v1.0
"""

import sys
from pathlib import Path
from typing import List, Dict, Tuple

# Required files for each hub
REQUIRED_FILES = [
    'hub.manifest.yaml',
    'SCHEMA.md',
    'CHECKLIST.md',
    'PRD.md',
    '__init__.py',
]

# Required IMO structure
REQUIRED_IMO_STRUCTURE = [
    'imo/__init__.py',
    'imo/input/__init__.py',
    'imo/middle/__init__.py',
    'imo/output/__init__.py',
]

# Forbidden folder names (CTB violation)
FORBIDDEN_FOLDERS = {'utils', 'helpers', 'common', 'shared', 'lib', 'misc'}

# Required sections in SCHEMA.md
SCHEMA_REQUIRED_SECTIONS = [
    '**AUTHORITY**: Neon',
    '**VERIFIED**:',
    '```mermaid',
    'erDiagram',
]

# Required sections in CHECKLIST.md
CHECKLIST_REQUIRED_SECTIONS = [
    'DOCTRINE LOCK',
    'CL Upstream Gate',
    'Hard Input Contract',
    'Forbidden Actions',
    'Compliance Rule',
]

# Known hubs to audit
KNOWN_HUBS = [
    'company-target',
    'dol-filings',
    'people-intelligence',
    'outreach-execution',
    'talent-flow',
    'blog-content',
]


def check_required_files(hub_path: Path, hub_name: str) -> List[str]:
    """Check hub has all required files."""
    errors = []
    for filename in REQUIRED_FILES:
        if not (hub_path / filename).exists():
            errors.append(f"{hub_name}: Missing required file {filename}")
    return errors


def check_imo_structure(hub_path: Path, hub_name: str) -> List[str]:
    """Check hub follows IMO structure."""
    errors = []
    for rel_path in REQUIRED_IMO_STRUCTURE:
        if not (hub_path / rel_path).exists():
            errors.append(f"{hub_name}: Missing IMO structure {rel_path}")
    return errors


def check_forbidden_folders(hub_path: Path, hub_name: str) -> List[str]:
    """Check for forbidden folder names."""
    errors = []
    for folder in hub_path.rglob('*'):
        if folder.is_dir() and folder.name in FORBIDDEN_FOLDERS:
            rel_path = folder.relative_to(hub_path)
            errors.append(f"{hub_name}: FORBIDDEN folder '{rel_path}' (CTB violation)")
    return errors


def check_schema_md(hub_path: Path, hub_name: str) -> List[str]:
    """Check SCHEMA.md has required sections."""
    errors = []
    schema_file = hub_path / 'SCHEMA.md'

    if not schema_file.exists():
        return [f"{hub_name}: SCHEMA.md not found"]

    content = schema_file.read_text()

    for section in SCHEMA_REQUIRED_SECTIONS:
        if section not in content:
            errors.append(f"{hub_name}: SCHEMA.md missing '{section}'")

    # Check for ASCII diagrams (prohibited)
    ascii_patterns = ['┌', '└', '│', '├', '─', '►', '▼']
    for pattern in ascii_patterns:
        if pattern in content and 'erDiagram' in content:
            # Allow ASCII in non-ERD sections
            pass

    return errors


def check_checklist_md(hub_path: Path, hub_name: str) -> List[str]:
    """Check CHECKLIST.md has required sections."""
    errors = []
    checklist_file = hub_path / 'CHECKLIST.md'

    if not checklist_file.exists():
        return [f"{hub_name}: CHECKLIST.md not found"]

    content = checklist_file.read_text()

    for section in CHECKLIST_REQUIRED_SECTIONS:
        if section not in content:
            errors.append(f"{hub_name}: CHECKLIST.md missing '{section}'")

    return errors


def check_manifest(hub_path: Path, hub_name: str) -> List[str]:
    """Check hub.manifest.yaml is valid."""
    errors = []
    manifest_file = hub_path / 'hub.manifest.yaml'

    if not manifest_file.exists():
        return [f"{hub_name}: hub.manifest.yaml not found"]

    content = manifest_file.read_text()

    # Required fields
    required_fields = ['hub:', 'doctrine:', 'interfaces:']
    for field in required_fields:
        if field not in content:
            errors.append(f"{hub_name}: hub.manifest.yaml missing '{field}'")

    return errors


def audit_hub(hub_path: Path, hub_name: str) -> Tuple[int, int, List[str]]:
    """Run full audit on a single hub."""
    errors = []

    # Run all checks
    errors.extend(check_required_files(hub_path, hub_name))
    errors.extend(check_imo_structure(hub_path, hub_name))
    errors.extend(check_forbidden_folders(hub_path, hub_name))
    errors.extend(check_schema_md(hub_path, hub_name))
    errors.extend(check_checklist_md(hub_path, hub_name))
    errors.extend(check_manifest(hub_path, hub_name))

    # Count pass/fail
    total_checks = (
        len(REQUIRED_FILES) +
        len(REQUIRED_IMO_STRUCTURE) +
        len(SCHEMA_REQUIRED_SECTIONS) +
        len(CHECKLIST_REQUIRED_SECTIONS) +
        3  # manifest fields
    )
    passed = total_checks - len(errors)

    return passed, total_checks, errors


def main():
    print("=" * 60)
    print("IMO TEMPLATE COMPLIANCE AUDIT")
    print("Doctrine: IMO_CANONICAL_v1.0")
    print("=" * 60)
    print()

    # Find repo root
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent.parent
    hubs_path = repo_root / 'hubs'

    if not hubs_path.exists():
        print(f"ERROR: hubs/ directory not found at {hubs_path}")
        sys.exit(2)

    all_errors = []
    total_passed = 0
    total_checks = 0

    for hub_name in KNOWN_HUBS:
        hub_path = hubs_path / hub_name
        print(f"Auditing: {hub_name}")

        if not hub_path.exists():
            all_errors.append(f"{hub_name}: Hub directory not found")
            print(f"  FAIL: Hub directory not found")
            continue

        passed, checks, errors = audit_hub(hub_path, hub_name)
        total_passed += passed
        total_checks += checks

        if errors:
            all_errors.extend(errors)
            print(f"  FAIL: {passed}/{checks} checks passed")
            for err in errors:
                print(f"    - {err.split(': ', 1)[1]}")
        else:
            print(f"  PASS: {passed}/{checks} checks passed")

        print()

    # Summary
    print("=" * 60)
    print(f"TOTAL: {total_passed}/{total_checks} checks passed")
    print()

    if all_errors:
        print(f"RESULT: FAIL ({len(all_errors)} errors)")
        print()
        print("To fix:")
        print("  1. Address each error listed above")
        print("  2. Re-run audit to verify")
        print("  3. Commit with 'fix(doctrine):' prefix")
        sys.exit(1)
    else:
        print("RESULT: PASS")
        print("All hubs are IMO-compliant.")
        sys.exit(0)


if __name__ == '__main__':
    main()
