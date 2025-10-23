#!/usr/bin/env python3
"""
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: sys/github-factory
Barton ID: 04.04.06.03
Unique ID: CTB-REMEDIATE-001
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: HEIR
─────────────────────────────────────────────

CTB Remediation Script

Automatically repairs CTB compliance issues:
1. Fixes Barton IDs (00.00.00 → proper branch-based IDs)
2. Improves enforcement classification
3. Generates ctb_registry.json
4. Creates GitHub Actions workflow
5. Regenerates audit report

Target: 90+ compliance score
"""

import os
import re
import json
import hashlib
import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

# Barton ID mapping - CORRECTED based on CTB branch structure
BARTON_ID_MAP = {
    # sys/ branches
    'sys/firebase-workbench': '04.04.01',
    'sys/composio-mcp': '04.04.02',
    'sys/neon-vault': '04.04.03',
    'sys/github-factory': '04.04.06',
    'sys/security-audit': '04.04.11',
    'sys/chartdb': '04.04.07',
    'sys/activepieces': '04.04.08',
    'sys/windmill': '04.04.09',
    'sys/api': '04.04.12',
    'sys/ops': '04.04.13',
    'sys/cli': '04.04.14',
    'sys/services': '04.04.15',
    'sys/tooling': '04.04.16',
    'sys/tests': '04.04.17',
    'sys/packages': '04.04.18',
    'sys/factory': '04.04.19',
    'sys/mechanic': '04.04.20',
    'sys/modules': '04.04.21',
    'sys/nodes': '04.04.22',
    'sys/libs': '04.04.23',
    'sys/tools': '04.04.24',

    # ai/ branches
    'ai/agents': '03.01.01',
    'ai/garage-bay': '03.01.02',
    'ai/testing': '03.01.03',
    'ai/scripts': '03.01.04',
    'ai/tools': '03.01.05',

    # data/ branches
    'data/infra': '05.01.01',
    'data/migrations': '05.01.02',
    'data/schemas': '05.01.03',

    # docs/ branches
    'docs/analysis': '06.01.01',
    'docs/audit': '06.01.02',
    'docs/examples': '06.01.03',
    'docs/scripts': '06.01.04',
    'docs/archive': '06.01.05',
    'docs/blueprints': '06.01.06',
    'docs/pages': '06.01.07',
    'docs/diagrams': '06.01.08',
    'docs/branches': '06.01.09',
    'docs/wiki': '06.01.10',

    # ui/ branches
    'ui/apps': '07.01.01',
    'ui/src': '07.01.02',
    'ui/public': '07.01.03',
    'ui/templates': '07.01.04',
    'ui/packages': '07.01.05',
    'ui/lovable': '07.01.06',
    'ui/placeholders': '07.01.07',

    # meta/ branches
    'meta/global-config': '08.01.01',
    'meta/config': '08.01.02',
    'meta/.vscode': '08.01.03',
    'meta/.devcontainer': '08.01.04',
    'meta/.gitingest': '08.01.05',

    # Root level branches (fallback)
    'sys': '04.04.00',
    'ai': '03.01.00',
    'data': '05.01.00',
    'docs': '06.01.00',
    'ui': '07.01.00',
    'meta': '08.01.00',
}

# Enhanced enforcement classification
ENFORCEMENT_PATTERNS = {
    'HEIR': [
        'agent', 'orchestrator', 'specialist', 'validator',
        'test', 'spec', 'check', 'verify', 'audit',
        'runner', 'executor', 'manager'
    ],
    'ORBT': [
        'migration', 'schema', 'api', 'endpoint', 'service',
        'route', 'controller', 'model', 'database', 'sql',
        'deployment', 'build', 'deploy', 'workflow'
    ],
}

SKIP_PATTERNS = ['node_modules', '.git', '__pycache__', 'dist', 'build', '.next']
SKIP_EXTENSIONS = ['.map', '.pyc', '.min.js', '.min.css', '.png', '.jpg', '.jpeg', '.gif', '.ico']


def get_ctb_branch(filepath: Path, ctb_root: Path) -> str:
    """Get CTB branch from file path."""
    rel_path = filepath.relative_to(ctb_root)
    parts = list(rel_path.parts)

    # Try to match most specific path first
    for i in range(len(parts), 0, -1):
        branch = '/'.join(parts[:i])
        if branch in BARTON_ID_MAP:
            return branch

    # Fallback to first part
    if len(parts) >= 1:
        return parts[0]

    return "unknown"


def get_barton_id(ctb_branch: str) -> str:
    """Get Barton ID for a CTB branch."""
    return BARTON_ID_MAP.get(ctb_branch, '00.00.00')


def infer_enforcement(filepath: Path) -> str:
    """Infer enforcement type from filename and path."""
    path_lower = str(filepath).lower()
    filename_lower = filepath.stem.lower()

    # Check for HEIR patterns
    for pattern in ENFORCEMENT_PATTERNS['HEIR']:
        if pattern in filename_lower or pattern in path_lower:
            return 'HEIR'

    # Check for ORBT patterns
    for pattern in ENFORCEMENT_PATTERNS['ORBT']:
        if pattern in filename_lower or pattern in path_lower:
            return 'ORBT'

    # Default based on directory
    if 'test' in path_lower or 'agent' in path_lower:
        return 'HEIR'
    elif 'migration' in path_lower or 'schema' in path_lower or 'api' in path_lower:
        return 'ORBT'
    elif 'doc' in path_lower or 'readme' in path_lower:
        return 'None'
    else:
        return 'None'


def should_skip(filepath: Path) -> bool:
    """Check if file should be skipped."""
    for pattern in SKIP_PATTERNS:
        if pattern in str(filepath):
            return True
    if filepath.suffix.lower() in SKIP_EXTENSIONS:
        return True
    return False


def extract_metadata(filepath: Path) -> Optional[Dict]:
    """Extract existing CTB metadata from file."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(2000)

            if 'CTB Classification Metadata' not in content:
                return None

            metadata = {}

            if match := re.search(r'CTB Branch:\s*(.+)', content):
                metadata['ctb_branch'] = match.group(1).strip()
            if match := re.search(r'Barton ID:\s*(.+)', content):
                metadata['barton_id'] = match.group(1).strip()
            if match := re.search(r'Unique ID:\s*(.+)', content):
                metadata['unique_id'] = match.group(1).strip()
            if match := re.search(r'Enforcement:\s*(.+)', content):
                metadata['enforcement'] = match.group(1).strip()

            return metadata
    except:
        return None


def update_metadata_in_file(filepath: Path, ctb_root: Path, dry_run: bool = False) -> Tuple[bool, str]:
    """Update metadata in a file."""
    # Get correct values
    ctb_branch = get_ctb_branch(filepath, ctb_root)
    barton_id = get_barton_id(ctb_branch)
    enforcement = infer_enforcement(filepath)

    # Extract existing metadata
    existing = extract_metadata(filepath)
    if not existing:
        return False, "No metadata found"

    # Check what needs updating
    needs_update = False
    updates = []

    if existing.get('barton_id') == '00.00.00' and barton_id != '00.00.00':
        needs_update = True
        updates.append(f"Barton ID: 00.00.00 → {barton_id}")

    if existing.get('enforcement') == 'None' and enforcement != 'None':
        needs_update = True
        updates.append(f"Enforcement: None → {enforcement}")

    # Also check if branch is wrong
    if existing.get('ctb_branch') != ctb_branch:
        needs_update = True
        updates.append(f"CTB Branch: {existing.get('ctb_branch')} → {ctb_branch}")

    if not needs_update:
        return False, "Already correct"

    # Read full content
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return False, f"Read error: {e}"

    # Update metadata fields
    new_content = content

    # Update Barton ID (use lambda to avoid backreference issues)
    new_content = re.sub(
        r'(Barton ID:\s*)(.+)',
        lambda m: m.group(1) + barton_id,
        new_content
    )

    # Update Enforcement
    new_content = re.sub(
        r'(Enforcement:\s*)(.+)',
        lambda m: m.group(1) + enforcement,
        new_content
    )

    # Update CTB Branch
    new_content = re.sub(
        r'(CTB Branch:\s*)(.+)',
        lambda m: m.group(1) + ctb_branch,
        new_content
    )

    # Write updated content
    if not dry_run:
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True, ', '.join(updates)
        except Exception as e:
            return False, f"Write error: {e}"
    else:
        return True, f"Would update: {', '.join(updates)}"


def remediate_repository(ctb_root: Path, dry_run: bool = False) -> Dict:
    """Remediate all files in repository."""
    stats = {
        'scanned': 0,
        'skipped': 0,
        'no_metadata': 0,
        'already_correct': 0,
        'updated': 0,
        'errors': 0,
        'updates_detail': defaultdict(int),
    }

    for filepath in ctb_root.rglob('*'):
        if not filepath.is_file():
            continue

        stats['scanned'] += 1

        if should_skip(filepath):
            stats['skipped'] += 1
            continue

        success, message = update_metadata_in_file(filepath, ctb_root, dry_run)

        if success:
            stats['updated'] += 1
            if 'Barton ID' in message:
                stats['updates_detail']['barton_id'] += 1
            if 'Enforcement' in message:
                stats['updates_detail']['enforcement'] += 1
            if 'CTB Branch' in message:
                stats['updates_detail']['ctb_branch'] += 1
        elif 'No metadata' in message:
            stats['no_metadata'] += 1
        elif 'Already correct' in message:
            stats['already_correct'] += 1
        else:
            stats['errors'] += 1

    return stats


def generate_registry(ctb_root: Path) -> Dict:
    """Generate CTB registry of all tagged files."""
    registry = {
        'generated': datetime.datetime.now().isoformat(),
        'version': '1.0',
        'total_files': 0,
        'branches': {},
        'files': [],
    }

    for filepath in ctb_root.rglob('*'):
        if not filepath.is_file():
            continue

        if should_skip(filepath):
            continue

        metadata = extract_metadata(filepath)
        if not metadata:
            continue

        registry['total_files'] += 1

        # Add to branch stats
        branch = metadata.get('ctb_branch', 'unknown')
        if branch not in registry['branches']:
            registry['branches'][branch] = {
                'count': 0,
                'barton_id': get_barton_id(branch),
                'enforcement_dist': {'HEIR': 0, 'ORBT': 0, 'None': 0},
            }

        registry['branches'][branch]['count'] += 1
        enf = metadata.get('enforcement', 'None')
        if enf in ['HEIR', 'ORBT', 'None']:
            registry['branches'][branch]['enforcement_dist'][enf] += 1

        # Add file entry
        registry['files'].append({
            'path': str(filepath.relative_to(ctb_root)),
            'ctb_branch': branch,
            'barton_id': metadata.get('barton_id'),
            'unique_id': metadata.get('unique_id'),
            'enforcement': enf,
        })

    return registry


def create_github_workflow() -> str:
    """Create GitHub Actions workflow for CTB enforcement."""
    workflow = """name: CTB Doctrine Enforcement

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]
  schedule:
    # Run weekly on Sundays at midnight
    - cron: '0 0 * * 0'

jobs:
  ctb-compliance:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Run CTB Audit
      id: audit
      run: |
        cd ctb/sys/github-factory/scripts
        python ctb_audit_generator.py ../../../../ctb/ -o audit_output.md

        # Extract score
        score=$(grep "Overall: " audit_output.md | head -1 | grep -oP '\\d+')
        echo "CTB Compliance Score: $score/100"
        echo "score=$score" >> $GITHUB_OUTPUT

    - name: Check Compliance Threshold
      run: |
        score=${{ steps.audit.outputs.score }}
        if [ "$score" -lt 90 ]; then
          echo "❌ CTB Compliance Score ($score/100) is below threshold (90)"
          echo "Please run remediation: python ctb/sys/github-factory/scripts/ctb_remediation.py ctb/"
          exit 1
        else
          echo "✅ CTB Compliance Score ($score/100) meets threshold"
        fi

    - name: Upload Audit Report
      if: always()
      uses: actions/upload-artifact@v3
      with:
        name: ctb-audit-report
        path: ctb/sys/github-factory/scripts/audit_output.md

    - name: Comment on PR
      if: github.event_name == 'pull_request' && always()
      uses: actions/github-script@v6
      with:
        script: |
          const score = ${{ steps.audit.outputs.score }};
          const status = score >= 90 ? '✅' : '❌';
          const grade = score >= 90 ? 'EXCELLENT' : score >= 75 ? 'GOOD' : score >= 60 ? 'FAIR' : 'NEEDS WORK';

          github.rest.issues.createComment({
            issue_number: context.issue.number,
            owner: context.repo.owner,
            repo: context.repo.repo,
            body: `## ${status} CTB Doctrine Compliance

**Score**: ${score}/100
**Grade**: ${grade}

${score >= 90 ? 'All CTB compliance checks passed!' : 'Some compliance issues detected. Please review the audit report.'}

[View Full Audit Report](../actions/runs/${{ github.run_id }})
`
          })
"""

    return workflow


def main():
    """Main entry point."""
    import argparse
    import sys

    # Force UTF-8 encoding
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(description='Remediate CTB compliance issues')
    parser.add_argument('directory', help='CTB directory to remediate')
    parser.add_argument('--dry-run', action='store_true', help='Dry run (no changes)')
    parser.add_argument('--skip-registry', action='store_true', help='Skip registry generation')
    parser.add_argument('--skip-workflow', action='store_true', help='Skip workflow creation')
    args = parser.parse_args()

    ctb_root = Path(args.directory).resolve()
    if not ctb_root.exists():
        print(f"[X] Directory not found: {ctb_root}")
        return 1

    print("=" * 60)
    print("CTB REMEDIATION SYSTEM")
    print("=" * 60)
    print(f"Directory: {ctb_root}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print()

    # Step 1: Remediate files
    print("[1/4] Remediating metadata...")
    stats = remediate_repository(ctb_root, dry_run=args.dry_run)

    print(f"  Scanned: {stats['scanned']:,} files")
    print(f"  Skipped: {stats['skipped']:,} files")
    print(f"  No metadata: {stats['no_metadata']:,} files")
    print(f"  Already correct: {stats['already_correct']:,} files")
    print(f"  Updated: {stats['updated']:,} files")
    print(f"    - Barton IDs: {stats['updates_detail']['barton_id']:,}")
    print(f"    - Enforcement: {stats['updates_detail']['enforcement']:,}")
    print(f"    - CTB Branch: {stats['updates_detail']['ctb_branch']:,}")
    print(f"  Errors: {stats['errors']:,}")
    print()

    # Step 2: Generate registry
    if not args.skip_registry:
        print("[2/4] Generating CTB registry...")
        registry = generate_registry(ctb_root)

        registry_path = ctb_root / 'meta' / 'ctb_registry.json'
        if not args.dry_run:
            registry_path.parent.mkdir(parents=True, exist_ok=True)
            with open(registry_path, 'w', encoding='utf-8') as f:
                json.dump(registry, f, indent=2)
            print(f"  [OK] Registry saved: {registry_path}")
            print(f"  Total indexed files: {registry['total_files']:,}")
            print(f"  Branches: {len(registry['branches'])}")
        else:
            print(f"  [DRY RUN] Would create: {registry_path}")
            print(f"  Total files to index: {registry['total_files']:,}")
    else:
        print("[2/4] Skipping registry generation")
    print()

    # Step 3: Create GitHub Actions workflow
    if not args.skip_workflow:
        print("[3/4] Creating GitHub Actions workflow...")
        workflow_content = create_github_workflow()

        workflow_path = ctb_root / 'sys' / 'github-factory' / '.github' / 'workflows' / 'ctb_enforcement.yml'
        if not args.dry_run:
            workflow_path.parent.mkdir(parents=True, exist_ok=True)
            with open(workflow_path, 'w', encoding='utf-8') as f:
                f.write(workflow_content)
            print(f"  [OK] Workflow created: {workflow_path}")
        else:
            print(f"  [DRY RUN] Would create: {workflow_path}")
    else:
        print("[3/4] Skipping workflow creation")
    print()

    # Step 4: Summary
    print("[4/4] Remediation Summary")
    print("=" * 60)

    if args.dry_run:
        print("[INFO] This was a dry run. No changes were made.")
        print()
        print("To apply changes, run without --dry-run:")
        print(f"  python {Path(__file__).name} {args.directory}")
    else:
        print("[OK] Remediation complete!")
        print()
        print("Next steps:")
        print("  1. Re-run audit to verify improvements:")
        print(f"     python ctb_audit_generator.py {args.directory}")
        print()
        print("  2. Expected improvements:")
        print(f"     - Barton IDs fixed: {stats['updates_detail']['barton_id']:,} files")
        print(f"     - Enforcement improved: {stats['updates_detail']['enforcement']:,} files")
        print()
        print("  3. If GitHub Actions workflow created:")
        print("     - Commit and push to enable automated checks")
        print("     - Workflow will run on push and weekly")

    print("=" * 60)

    return 0


if __name__ == '__main__':
    exit(main())
