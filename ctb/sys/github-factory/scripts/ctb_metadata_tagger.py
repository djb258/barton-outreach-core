#!/usr/bin/env python3
"""
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: sys/github-factory
Barton ID: 04.04.06.01
Unique ID: CTB-TAGGER-001
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: HEIR
─────────────────────────────────────────────

CTB Metadata Tagger

Injects CTB metadata headers into all files in the CTB structure.
Follows strict mode: no hallucinations, only factual data.
"""

import os
import re
import hashlib
import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Skip these files/directories
SKIP_PATTERNS = [
    'node_modules',
    '.git',
    '.env',
    '__pycache__',
    'dist',
    'build',
    '.next',
    'coverage',
]

# Skip these file extensions
SKIP_EXTENSIONS = [
    '.map',      # Source maps
    '.pyc',      # Python bytecode
    '.min.js',   # Minified
    '.min.css',  # Minified
    '.png',      # Binary
    '.jpg',      # Binary
    '.jpeg',     # Binary
    '.gif',      # Binary
    '.svg',      # Binary (usually)
    '.ico',      # Binary
    '.ttf',      # Binary
    '.woff',     # Binary
    '.woff2',    # Binary
    '.eot',      # Binary
    '.lock',     # Lock files
    '.lockb',    # Bun lock
]

# Barton ID mapping by CTB branch
BARTON_ID_MAP = {
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
    'sys': '04.04.00',

    'ai/agents': '03.01.01',
    'ai/garage-bay': '03.01.02',
    'ai/testing': '03.01.03',
    'ai/scripts': '03.01.04',
    'ai/tools': '03.01.05',
    'ai': '03.01.00',

    'data/infra': '05.01.01',
    'data/migrations': '05.01.02',
    'data/schemas': '05.01.03',
    'data': '05.01.00',

    'docs/analysis': '06.01.01',
    'docs/audit': '06.01.02',
    'docs/examples': '06.01.03',
    'docs/scripts': '06.01.04',
    'docs/archive': '06.01.05',
    'docs': '06.01.00',

    'ui/apps': '07.01.01',
    'ui/src': '07.01.02',
    'ui/public': '07.01.03',
    'ui/templates': '07.01.04',
    'ui/packages': '07.01.05',
    'ui': '07.01.00',

    'meta/global-config': '08.01.01',
    'meta/config': '08.01.02',
    'meta': '08.01.00',
}

# Enforcement type by file pattern
ENFORCEMENT_MAP = {
    'validator': 'HEIR',
    'test': 'HEIR',
    'migration': 'ORBT',
    'schema': 'ORBT',
    'agent': 'HEIR',
    'api': 'ORBT',
    'config': 'None',
    'doc': 'None',
}


def get_file_extension(filepath: Path) -> str:
    """Get file extension."""
    return filepath.suffix.lower()


def should_skip_file(filepath: Path) -> bool:
    """Check if file should be skipped."""
    # Check path patterns
    for pattern in SKIP_PATTERNS:
        if pattern in str(filepath):
            return True

    # Check extension
    ext = get_file_extension(filepath)
    if ext in SKIP_EXTENSIONS:
        return True

    # Skip empty files
    if filepath.stat().st_size == 0:
        return True

    return False


def already_has_metadata(filepath: Path) -> bool:
    """Check if file already has CTB metadata."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            first_lines = ''.join([f.readline() for _ in range(15)])
            return 'CTB Classification Metadata' in first_lines or 'CTB Branch:' in first_lines
    except:
        return False


def get_barton_id(filepath: Path, ctb_root: Path) -> str:
    """Determine Barton ID based on file location."""
    rel_path = filepath.relative_to(ctb_root)
    parts = list(rel_path.parts)

    # Try to match against known patterns (most specific first)
    for i in range(len(parts), 0, -1):
        branch = '/'.join(parts[:i])
        if branch in BARTON_ID_MAP:
            return BARTON_ID_MAP[branch]

    # Default to 00.00.00 (unknown)
    return '00.00.00'


def get_enforcement_type(filepath: Path) -> str:
    """Determine enforcement type based on filename/content."""
    filename = filepath.stem.lower()

    for pattern, enforcement in ENFORCEMENT_MAP.items():
        if pattern in filename:
            return enforcement

    # Default based on directory
    path_str = str(filepath).lower()
    if 'test' in path_str or 'agent' in path_str:
        return 'HEIR'
    elif 'migration' in path_str or 'schema' in path_str or 'api' in path_str:
        return 'ORBT'
    else:
        return 'None'


def generate_unique_id(filepath: Path, ctb_root: Path) -> str:
    """Generate unique ID based on file path."""
    rel_path = str(filepath.relative_to(ctb_root))
    hash_part = hashlib.md5(rel_path.encode()).hexdigest()[:8].upper()
    return f"CTB-{hash_part}"


def get_ctb_branch(filepath: Path, ctb_root: Path) -> str:
    """Get CTB branch from file path."""
    rel_path = filepath.relative_to(ctb_root)
    parts = list(rel_path.parts)

    if len(parts) >= 2:
        return f"{parts[0]}/{parts[1]}"
    elif len(parts) >= 1:
        return parts[0]
    else:
        return "unknown"


def create_header_block(filepath: Path, ctb_root: Path, comment_style: str) -> str:
    """Create CTB metadata header block."""
    barton_id = get_barton_id(filepath, ctb_root)
    unique_id = generate_unique_id(filepath, ctb_root)
    ctb_branch = get_ctb_branch(filepath, ctb_root)
    enforcement = get_enforcement_type(filepath)
    today = datetime.date.today().isoformat()

    # Create header based on comment style
    if comment_style == 'js':  # JavaScript/TypeScript/CSS
        return f"""/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: {ctb_branch}
Barton ID: {barton_id}
Unique ID: {unique_id}
Blueprint Hash:
Last Updated: {today}
Enforcement: {enforcement}
─────────────────────────────────────────────
*/

"""
    elif comment_style == 'py':  # Python
        return f'''"""
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: {ctb_branch}
Barton ID: {barton_id}
Unique ID: {unique_id}
Blueprint Hash:
Last Updated: {today}
Enforcement: {enforcement}
─────────────────────────────────────────────
"""

'''
    elif comment_style == 'sql':  # SQL
        return f"""-- ─────────────────────────────────────────────
-- 📁 CTB Classification Metadata
-- ─────────────────────────────────────────────
-- CTB Branch: {ctb_branch}
-- Barton ID: {barton_id}
-- Unique ID: {unique_id}
-- Blueprint Hash:
-- Last Updated: {today}
-- Enforcement: {enforcement}
-- ─────────────────────────────────────────────

"""
    elif comment_style == 'md':  # Markdown
        return f"""<!--
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: {ctb_branch}
Barton ID: {barton_id}
Unique ID: {unique_id}
Blueprint Hash:
Last Updated: {today}
Enforcement: {enforcement}
─────────────────────────────────────────────
-->

"""
    elif comment_style == 'sh':  # Shell/Bash
        return f"""# ─────────────────────────────────────────────
# 📁 CTB Classification Metadata
# ─────────────────────────────────────────────
# CTB Branch: {ctb_branch}
# Barton ID: {barton_id}
# Unique ID: {unique_id}
# Blueprint Hash:
# Last Updated: {today}
# Enforcement: {enforcement}
# ─────────────────────────────────────────────

"""
    elif comment_style == 'json':  # JSON (as first property)
        # JSON doesn't support comments, so we'll add a special property
        return f'''  "__ctb_metadata__": {{
    "ctb_branch": "{ctb_branch}",
    "barton_id": "{barton_id}",
    "unique_id": "{unique_id}",
    "blueprint_hash": "",
    "last_updated": "{today}",
    "enforcement": "{enforcement}"
  }},
'''
    else:
        return ""


def get_comment_style(filepath: Path) -> Optional[str]:
    """Determine comment style based on file extension."""
    ext = get_file_extension(filepath)

    js_extensions = ['.js', '.ts', '.tsx', '.jsx', '.mjs', '.cjs', '.cts', '.css', '.scss']
    py_extensions = ['.py']
    sql_extensions = ['.sql']
    md_extensions = ['.md']
    sh_extensions = ['.sh', '.bash', '.bat']
    json_extensions = ['.json']

    if ext in js_extensions:
        return 'js'
    elif ext in py_extensions:
        return 'py'
    elif ext in sql_extensions:
        return 'sql'
    elif ext in md_extensions:
        return 'md'
    elif ext in sh_extensions:
        return 'sh'
    elif ext in json_extensions:
        return 'json'
    else:
        return None


def tag_file(filepath: Path, ctb_root: Path, dry_run: bool = False) -> Tuple[bool, str]:
    """Tag a single file with CTB metadata."""
    # Determine comment style
    comment_style = get_comment_style(filepath)
    if not comment_style:
        return False, "Unsupported file type"

    # Check if already tagged
    if already_has_metadata(filepath):
        return False, "Already tagged"

    # Read original content
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            original_content = f.read()
    except Exception as e:
        return False, f"Read error: {e}"

    # Handle JSON specially (inject metadata as property)
    if comment_style == 'json':
        # Try to parse JSON and inject metadata
        try:
            import json
            data = json.loads(original_content)
            if isinstance(data, dict):
                # Create metadata header as comment (not valid JSON, so skip)
                return False, "JSON metadata injection skipped (would break JSON format)"
            else:
                return False, "JSON must be object to inject metadata"
        except:
            return False, "Invalid JSON"

    # Handle shebang for Python/Shell
    if comment_style in ['py', 'sh']:
        lines = original_content.split('\n', 1)
        if lines[0].startswith('#!'):
            shebang = lines[0] + '\n'
            rest = lines[1] if len(lines) > 1 else ''
            header = create_header_block(filepath, ctb_root, comment_style)
            new_content = shebang + header + rest
        else:
            header = create_header_block(filepath, ctb_root, comment_style)
            new_content = header + original_content
    else:
        # Standard header injection
        header = create_header_block(filepath, ctb_root, comment_style)
        new_content = header + original_content

    # Write new content (unless dry run)
    if not dry_run:
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True, "Tagged successfully"
        except Exception as e:
            return False, f"Write error: {e}"
    else:
        return True, "Tagged (dry run)"


def tag_directory(directory: Path, dry_run: bool = False, verbose: bool = False) -> Dict[str, int]:
    """Tag all files in a directory recursively."""
    ctb_root = directory
    stats = {
        'total': 0,
        'skipped': 0,
        'already_tagged': 0,
        'tagged': 0,
        'errors': 0,
    }

    # Walk through directory
    for filepath in directory.rglob('*'):
        if not filepath.is_file():
            continue

        stats['total'] += 1

        # Check if should skip
        if should_skip_file(filepath):
            stats['skipped'] += 1
            if verbose:
                print(f"[SKIP] {filepath.relative_to(ctb_root)}")
            continue

        # Try to tag
        success, message = tag_file(filepath, ctb_root, dry_run)

        if success:
            stats['tagged'] += 1
            if verbose:
                print(f"[TAG]  {filepath.relative_to(ctb_root)}")
        elif 'Already tagged' in message:
            stats['already_tagged'] += 1
            if verbose:
                print(f"[EXIST] {filepath.relative_to(ctb_root)} - {message}")
        else:
            stats['errors'] += 1
            if verbose:
                print(f"[ERROR] {filepath.relative_to(ctb_root)} - {message}")

    return stats


def main():
    """Main entry point."""
    import argparse
    import sys

    # Force UTF-8 encoding for Windows
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(description='Tag CTB files with metadata headers')
    parser.add_argument('directory', help='CTB directory to tag')
    parser.add_argument('--dry-run', action='store_true', help='Dry run (no writes)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    args = parser.parse_args()

    directory = Path(args.directory).resolve()
    if not directory.exists():
        print(f"[X] Directory not found: {directory}")
        return 1

    print(f"CTB Metadata Tagger")
    print(f"Directory: {directory}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print()

    stats = tag_directory(directory, dry_run=args.dry_run, verbose=args.verbose)

    print()
    print("=" * 50)
    print("TAGGING SUMMARY")
    print("=" * 50)
    print(f"Total files scanned:     {stats['total']}")
    print(f"Skipped (excluded):      {stats['skipped']}")
    print(f"Already tagged:          {stats['already_tagged']}")
    print(f"Newly tagged:            {stats['tagged']}")
    print(f"Errors:                  {stats['errors']}")
    print("=" * 50)

    if not args.dry_run and stats['tagged'] > 0:
        print()
        print(f"[OK] Successfully tagged {stats['tagged']} files")
    elif args.dry_run:
        print()
        print(f"[INFO] Dry run complete. Run without --dry-run to apply tags.")

    return 0


if __name__ == '__main__':
    exit(main())
