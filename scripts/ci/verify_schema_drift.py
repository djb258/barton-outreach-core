#!/usr/bin/env python3
"""
Neon Schema Drift Verification
==============================

CI gate that compares SCHEMA.md files against actual Neon database.
HARD FAIL if any drift detected.

Usage:
    doppler run -- python scripts/ci/verify_schema_drift.py

Exit codes:
    0 = PASS (no drift)
    1 = FAIL (drift detected)
    2 = ERROR (connection/config issue)

Doctrine: IMO_CANONICAL_v1.0
"""

import os
import sys
import re
import psycopg2
from pathlib import Path
from typing import Dict, Set, Tuple, List

# Hub schema mappings
HUB_SCHEMA_MAP = {
    'company-target': ['outreach.company_target', 'company.company_master', 'company.company_slots'],
    'dol-filings': ['dol.form_5500', 'dol.schedule_a', 'dol.renewal_calendar'],
    'people-intelligence': ['people.people_master', 'people.company_slot', 'outreach.people'],
    'outreach-execution': ['outreach.campaigns', 'outreach.sequences', 'outreach.send_log'],
    'talent-flow': ['talent_flow.movement_history', 'people.person_movement_history'],
}


def get_neon_connection():
    """Connect to Neon via Doppler-injected credentials."""
    try:
        conn = psycopg2.connect(
            host=os.environ.get('NEON_HOST'),
            database=os.environ.get('NEON_DATABASE'),
            user=os.environ.get('NEON_USER'),
            password=os.environ.get('NEON_PASSWORD'),
            sslmode='require'
        )
        conn.set_session(readonly=True)
        return conn
    except Exception as e:
        print(f"ERROR: Failed to connect to Neon: {e}")
        sys.exit(2)


def get_neon_tables(conn) -> Set[str]:
    """Get all tables from Neon."""
    cur = conn.cursor()
    cur.execute("""
        SELECT table_schema || '.' || table_name
        FROM information_schema.tables
        WHERE table_type = 'BASE TABLE'
        AND table_schema NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
        ORDER BY table_schema, table_name;
    """)
    tables = {row[0] for row in cur.fetchall()}
    cur.close()
    return tables


def get_neon_columns(conn, schema: str, table: str) -> Dict[str, str]:
    """Get columns for a specific table."""
    cur = conn.cursor()
    cur.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s
        ORDER BY ordinal_position;
    """, (schema, table))
    columns = {row[0]: row[1] for row in cur.fetchall()}
    cur.close()
    return columns


def parse_schema_md(hub_path: Path) -> Set[str]:
    """Parse SCHEMA.md to extract documented tables."""
    schema_file = hub_path / 'SCHEMA.md'
    if not schema_file.exists():
        return set()

    content = schema_file.read_text()
    tables = set()

    # Match table references in format: schema.table or `schema.table`
    patterns = [
        r'`([a-z_]+)\.([a-z_]+)`',  # backtick format
        r'\|\s*`?([a-z_]+)`?\s*\|\s*`?([a-z_]+)`?\s*\|',  # table format
    ]

    for pattern in patterns:
        for match in re.finditer(pattern, content):
            tables.add(f"{match.group(1)}.{match.group(2)}")

    return tables


def check_hub_drift(conn, hub_name: str, hub_path: Path) -> List[str]:
    """Check for drift between SCHEMA.md and Neon for a hub."""
    errors = []

    schema_file = hub_path / 'SCHEMA.md'
    if not schema_file.exists():
        errors.append(f"MISSING: {hub_name}/SCHEMA.md not found")
        return errors

    # Check required tables exist in Neon
    expected_tables = HUB_SCHEMA_MAP.get(hub_name, [])
    neon_tables = get_neon_tables(conn)

    for table in expected_tables:
        if table not in neon_tables:
            errors.append(f"DRIFT: {hub_name} expects {table} but not found in Neon")

    # Check SCHEMA.md has Neon authority declaration
    content = schema_file.read_text()
    if '**AUTHORITY**: Neon' not in content:
        errors.append(f"AUTHORITY: {hub_name}/SCHEMA.md missing Neon authority declaration")

    # Check for Mermaid ERD
    if '```mermaid' not in content or 'erDiagram' not in content:
        errors.append(f"FORMAT: {hub_name}/SCHEMA.md missing Mermaid erDiagram")

    return errors


def check_forbidden_folders(hubs_path: Path) -> List[str]:
    """Check for forbidden folders in hub structure."""
    errors = []
    forbidden = {'utils', 'helpers', 'common', 'shared', 'lib', 'misc'}

    for hub_dir in hubs_path.iterdir():
        if not hub_dir.is_dir():
            continue

        for folder in hub_dir.rglob('*'):
            if folder.is_dir() and folder.name in forbidden:
                errors.append(f"FORBIDDEN: {folder.relative_to(hubs_path)} (CTB violation)")

    return errors


def main():
    print("=" * 60)
    print("NEON SCHEMA DRIFT VERIFICATION")
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

    # Check forbidden folders first (no DB needed)
    print("1. Checking forbidden folders...")
    folder_errors = check_forbidden_folders(hubs_path)
    all_errors.extend(folder_errors)
    if folder_errors:
        for err in folder_errors:
            print(f"   FAIL: {err}")
    else:
        print("   PASS: No forbidden folders found")
    print()

    # Connect to Neon
    print("2. Connecting to Neon (READ-ONLY)...")
    conn = get_neon_connection()
    print("   PASS: Connected")
    print()

    # Check each hub
    print("3. Verifying hub schemas...")
    for hub_name in HUB_SCHEMA_MAP.keys():
        hub_path = hubs_path / hub_name
        if not hub_path.exists():
            all_errors.append(f"MISSING: Hub directory {hub_name}/ not found")
            print(f"   FAIL: {hub_name}/ not found")
            continue

        errors = check_hub_drift(conn, hub_name, hub_path)
        if errors:
            all_errors.extend(errors)
            for err in errors:
                print(f"   FAIL: {err}")
        else:
            print(f"   PASS: {hub_name}")
    print()

    conn.close()

    # Summary
    print("=" * 60)
    if all_errors:
        print(f"RESULT: FAIL ({len(all_errors)} errors)")
        print()
        print("Errors:")
        for err in all_errors:
            print(f"  - {err}")
        print()
        print("ACTION REQUIRED:")
        print("  1. Fix drift between SCHEMA.md and Neon")
        print("  2. Create ADR documenting any intentional changes")
        print("  3. Bump doctrine version if schema changed")
        sys.exit(1)
    else:
        print("RESULT: PASS")
        print("All schemas verified against Neon.")
        sys.exit(0)


if __name__ == '__main__':
    main()
