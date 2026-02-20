"""
Test: No Illegal Writers to Sovereign Tables
=============================================

This test statically analyzes the codebase to ensure no code outside
of sanctioned IMO middle layers writes to protected sovereign tables.

Protected Tables:
- outreach.company_hub_status
- outreach.hub_registry

NOTE: outreach.manual_overrides was DROPPED 2026-02-20 (0 rows, table
consolidation Phase 1). Removed from protected list.

Sanctioned Writers:
- hubs/*/imo/middle/hub_status.py
- infra/migrations/*.sql
"""

import pytest
import os
import re
from pathlib import Path


# Get project root
PROJECT_ROOT = Path(__file__).parent.parent.parent


# Protected tables (mutations forbidden outside IMO)
PROTECTED_TABLES = [
    'company_hub_status',
    'hub_registry',
]

# Sanctioned paths that ARE allowed to write
SANCTIONED_PATTERNS = [
    r'hubs[\\/].*[\\/]imo[\\/]middle[\\/]hub_status\.py$',
    r'infra[\\/]migrations[\\/].*\.sql$',
    r'templates[\\/].*\.md$',  # Documentation only
    r'docs[\\/].*\.md$',        # Documentation only
    r'tests[\\/].*\.py$',       # Tests can reference patterns
]

# Mutation patterns to detect
MUTATION_PATTERNS = [
    r'INSERT\s+INTO\s+["\']?outreach\.["\']?{table}',
    r'UPDATE\s+["\']?outreach\.["\']?{table}',
    r'DELETE\s+FROM\s+["\']?outreach\.["\']?{table}',
    r'INSERT\s+INTO\s+["\']?{table}',
    r'UPDATE\s+["\']?{table}\s',
    r'DELETE\s+FROM\s+["\']?{table}',
]

# Paths to scan (non-sanctioned areas)
SCAN_PATHS = [
    'spokes',
    'ctb',
    'ops',
    'scripts',
    'src',
    'enrichment-hub',
    'integrations',
    'shared',
    'outreach_core',
]


def is_sanctioned_path(file_path: str) -> bool:
    """Check if file is a sanctioned writer."""
    path_normalized = str(file_path).replace('\\', '/')
    
    for pattern in SANCTIONED_PATTERNS:
        if re.search(pattern, path_normalized, re.IGNORECASE):
            return True
    
    return False


def scan_file_for_illegal_mutations(file_path: Path) -> list:
    """
    Scan a single file for illegal mutations.
    
    Returns list of (line_num, line_content, table) tuples.
    """
    violations = []
    
    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        return []
    
    lines = content.split('\n')
    
    for table in PROTECTED_TABLES:
        for pattern_template in MUTATION_PATTERNS:
            pattern = pattern_template.format(table=table)
            regex = re.compile(pattern, re.IGNORECASE)
            
            for line_num, line in enumerate(lines, 1):
                if regex.search(line):
                    # Skip if it's a comment
                    stripped = line.strip()
                    if stripped.startswith('#') or stripped.startswith('--'):
                        continue
                    if stripped.startswith('"""') or stripped.startswith("'''"):
                        continue
                    
                    violations.append((line_num, line.strip()[:100], table))
    
    return violations


def test_no_illegal_writers_in_spokes():
    """Ensure no spoke writes to sovereign tables."""
    spokes_path = PROJECT_ROOT / 'spokes'
    if not spokes_path.exists():
        pytest.skip("spokes directory not found")
    
    all_violations = []
    
    for py_file in spokes_path.rglob('*.py'):
        if is_sanctioned_path(str(py_file)):
            continue
        violations = scan_file_for_illegal_mutations(py_file)
        for v in violations:
            all_violations.append((str(py_file), v))
    
    assert len(all_violations) == 0, (
        f"Found {len(all_violations)} illegal mutations in spokes:\n" +
        "\n".join(f"  {f}:{v[0]} -> {v[2]}" for f, v in all_violations)
    )


def test_no_illegal_writers_in_ctb():
    """Ensure no CTB module writes to sovereign tables."""
    ctb_path = PROJECT_ROOT / 'ctb'
    if not ctb_path.exists():
        pytest.skip("ctb directory not found")
    
    all_violations = []
    
    for py_file in ctb_path.rglob('*.py'):
        if is_sanctioned_path(str(py_file)):
            continue
        violations = scan_file_for_illegal_mutations(py_file)
        for v in violations:
            all_violations.append((str(py_file), v))
    
    assert len(all_violations) == 0, (
        f"Found {len(all_violations)} illegal mutations in ctb:\n" +
        "\n".join(f"  {f}:{v[0]} -> {v[2]}" for f, v in all_violations)
    )


def test_no_illegal_writers_in_ops():
    """Ensure no ops module writes to sovereign tables."""
    ops_path = PROJECT_ROOT / 'ops'
    if not ops_path.exists():
        pytest.skip("ops directory not found")
    
    all_violations = []
    
    for py_file in ops_path.rglob('*.py'):
        if is_sanctioned_path(str(py_file)):
            continue
        violations = scan_file_for_illegal_mutations(py_file)
        for v in violations:
            all_violations.append((str(py_file), v))
    
    assert len(all_violations) == 0, (
        f"Found {len(all_violations)} illegal mutations in ops:\n" +
        "\n".join(f"  {f}:{v[0]} -> {v[2]}" for f, v in all_violations)
    )


def test_no_illegal_writers_in_scripts():
    """Ensure no script writes to sovereign tables."""
    scripts_path = PROJECT_ROOT / 'scripts'
    if not scripts_path.exists():
        pytest.skip("scripts directory not found")
    
    all_violations = []
    
    for py_file in scripts_path.rglob('*.py'):
        if is_sanctioned_path(str(py_file)):
            continue
        violations = scan_file_for_illegal_mutations(py_file)
        for v in violations:
            all_violations.append((str(py_file), v))
    
    assert len(all_violations) == 0, (
        f"Found {len(all_violations)} illegal mutations in scripts:\n" +
        "\n".join(f"  {f}:{v[0]} -> {v[2]}" for f, v in all_violations)
    )


def test_no_illegal_writers_in_src():
    """Ensure no src module writes to sovereign tables."""
    src_path = PROJECT_ROOT / 'src'
    if not src_path.exists():
        pytest.skip("src directory not found")
    
    all_violations = []
    
    for py_file in src_path.rglob('*.py'):
        if is_sanctioned_path(str(py_file)):
            continue
        violations = scan_file_for_illegal_mutations(py_file)
        for v in violations:
            all_violations.append((str(py_file), v))
    
    assert len(all_violations) == 0, (
        f"Found {len(all_violations)} illegal mutations in src:\n" +
        "\n".join(f"  {f}:{v[0]} -> {v[2]}" for f, v in all_violations)
    )


def test_sanctioned_writers_exist():
    """Verify sanctioned writers are in expected locations."""
    expected_sanctioned = [
        PROJECT_ROOT / 'hubs' / 'people-intelligence' / 'imo' / 'middle' / 'hub_status.py',
        PROJECT_ROOT / 'hubs' / 'talent-flow' / 'imo' / 'middle' / 'hub_status.py',
        PROJECT_ROOT / 'hubs' / 'blog-content' / 'imo' / 'middle' / 'hub_status.py',
    ]
    
    for path in expected_sanctioned:
        assert path.exists(), f"Expected sanctioned writer not found: {path}"


def test_comprehensive_scan():
    """
    Comprehensive scan of all non-sanctioned paths.
    
    This is the main guardrail test.
    """
    all_violations = []
    
    for scan_dir in SCAN_PATHS:
        scan_path = PROJECT_ROOT / scan_dir
        if not scan_path.exists():
            continue
        
        for py_file in scan_path.rglob('*.py'):
            if is_sanctioned_path(str(py_file)):
                continue
            
            violations = scan_file_for_illegal_mutations(py_file)
            for v in violations:
                all_violations.append((str(py_file), v))
    
    if all_violations:
        violation_report = "\n".join(
            f"  ❌ {f}:{v[0]} - writes to {v[2]}"
            for f, v in all_violations[:20]  # First 20
        )
        if len(all_violations) > 20:
            violation_report += f"\n  ... and {len(all_violations) - 20} more"
        
        pytest.fail(
            f"MUTATION GUARD VIOLATION: {len(all_violations)} illegal writers detected!\n\n"
            f"Protected tables: {PROTECTED_TABLES}\n"
            f"Sanctioned writers: hubs/*/imo/middle/hub_status.py only\n\n"
            f"Violations:\n{violation_report}"
        )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
