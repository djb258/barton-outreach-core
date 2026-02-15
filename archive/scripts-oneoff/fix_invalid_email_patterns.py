#!/usr/bin/env python3
"""
Email Pattern Remediation Script
Fixes invalid literal patterns and hardcoded domain patterns
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import re

load_dotenv()

# Neon connection
conn = psycopg2.connect(
    host=os.getenv('NEON_HOST'),
    database=os.getenv('NEON_DATABASE'),
    user=os.getenv('NEON_USER'),
    password=os.getenv('NEON_PASSWORD'),
    sslmode='require'
)

# Pattern mapping for literal text -> template variables
PATTERN_FIXES = {
    'first': '{first}',
    'last': '{last}',
    'flast': '{f}{last}',
    'firstlast': '{first}{last}',
    'firstl': '{first}{l}',
    'first.last': '{first}.{last}',
    'f.last': '{f}.{last}',
    'first_last': '{first}_{last}',
    'first-last': '{first}-{last}',
    'last.first': '{last}.{first}',
    'lastfirst': '{last}{first}',
}

def identify_invalid_patterns():
    """Identify invalid literal patterns (no template variables)"""
    query = """
    SELECT
        ct.target_id,
        ct.outreach_id,
        o.domain,
        ct.email_method,
        ct.confidence_score,
        ct.method_type
    FROM outreach.company_target ct
    JOIN outreach.outreach o ON ct.outreach_id = o.outreach_id
    WHERE ct.email_method IS NOT NULL
      AND ct.email_method NOT LIKE '%{%'  -- No template variables
    ORDER BY ct.confidence_score DESC;
    """

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query)
        return cur.fetchall()

def identify_hardcoded_domains():
    """Identify patterns with hardcoded domains"""
    query = """
    SELECT
        ct.target_id,
        ct.outreach_id,
        o.domain,
        ct.email_method,
        ct.confidence_score
    FROM outreach.company_target ct
    JOIN outreach.outreach o ON ct.outreach_id = o.outreach_id
    WHERE ct.email_method LIKE '%@%.%';  -- Contains @ domain
    """

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query)
        return cur.fetchall()

def fix_literal_pattern(pattern):
    """Convert literal pattern to template pattern"""
    # Direct mapping
    if pattern in PATTERN_FIXES:
        return PATTERN_FIXES[pattern], 'mapped'

    # Try to infer pattern
    if pattern.startswith('first') and pattern.endswith('last'):
        separator = pattern[5:-4]  # Extract separator
        if separator in ['.', '_', '-', '']:
            return f'{{first}}{separator}{{last}}', 'inferred'

    # Cannot fix
    return None, 'unknown'

def fix_hardcoded_domain(pattern):
    """Remove hardcoded domain from pattern"""
    # Extract pattern before @
    if '@' in pattern:
        return pattern.split('@')[0], 'stripped'
    return pattern, 'no_change'

def preview_fixes(dry_run=True):
    """Preview pattern fixes before applying"""
    print("\n" + "="*80)
    print("INVALID LITERAL PATTERNS - REMEDIATION PREVIEW")
    print("="*80 + "\n")

    invalid_patterns = identify_invalid_patterns()

    if not invalid_patterns:
        print("[OK] No invalid literal patterns found!")
        return []

    fixes = []
    for row in invalid_patterns:
        target_id = row['target_id']
        old_pattern = row['email_method']
        domain = row['domain']
        confidence = row['confidence_score']

        new_pattern, fix_type = fix_literal_pattern(old_pattern)

        fixes.append({
            'target_id': target_id,
            'old_pattern': old_pattern,
            'new_pattern': new_pattern,
            'fix_type': fix_type,
            'domain': domain,
            'confidence': confidence
        })

    # Group by fix type
    mapped = [f for f in fixes if f['fix_type'] == 'mapped']
    inferred = [f for f in fixes if f['fix_type'] == 'inferred']
    unknown = [f for f in fixes if f['fix_type'] == 'unknown']

    print(f"Total Invalid Patterns: {len(fixes)}\n")
    print(f"  [OK] Mapped (direct replacement): {len(mapped)}")
    print(f"  [?] Inferred (pattern guess): {len(inferred)}")
    print(f"  [X] Unknown (manual review needed): {len(unknown)}\n")

    if mapped:
        print("\nMAPPED FIXES (High Confidence):")
        print("-" * 80)
        for f in mapped[:20]:  # Show first 20
            print(f"  {f['old_pattern']:20} -> {f['new_pattern']:20} [{f['domain']}]")
        if len(mapped) > 20:
            print(f"  ... and {len(mapped) - 20} more")

    if inferred:
        print("\nINFERRED FIXES (Medium Confidence):")
        print("-" * 80)
        for f in inferred[:20]:
            print(f"  {f['old_pattern']:20} -> {f['new_pattern']:20} [{f['domain']}]")
        if len(inferred) > 20:
            print(f"  ... and {len(inferred) - 20} more")

    if unknown:
        print("\nUNKNOWN PATTERNS (Manual Review Required):")
        print("-" * 80)
        for f in unknown:
            print(f"  {f['old_pattern']:20} -> CANNOT AUTO-FIX [{f['domain']}]")

    return fixes

def preview_hardcoded_domains(dry_run=True):
    """Preview hardcoded domain fixes"""
    print("\n" + "="*80)
    print("HARDCODED DOMAIN PATTERNS - REMEDIATION PREVIEW")
    print("="*80 + "\n")

    hardcoded = identify_hardcoded_domains()

    if not hardcoded:
        print("[OK] No hardcoded domain patterns found!")
        return []

    fixes = []
    for row in hardcoded:
        target_id = row['target_id']
        old_pattern = row['email_method']
        domain = row['domain']

        new_pattern, fix_type = fix_hardcoded_domain(old_pattern)

        fixes.append({
            'target_id': target_id,
            'old_pattern': old_pattern,
            'new_pattern': new_pattern,
            'domain': domain
        })

    print(f"Total Hardcoded Patterns: {len(fixes)}\n")

    for f in fixes:
        print(f"  {f['old_pattern']:40} -> {f['new_pattern']:20} [{f['domain']}]")

    return fixes

def apply_fixes(fixes, dry_run=True):
    """Apply pattern fixes to database"""
    if dry_run:
        print("\n" + "="*80)
        print("DRY RUN MODE - No changes will be applied")
        print("="*80 + "\n")
        return

    print("\n" + "="*80)
    print("APPLYING FIXES TO DATABASE")
    print("="*80 + "\n")

    with conn.cursor() as cur:
        for fix in fixes:
            if fix['new_pattern'] is None:
                print(f"[X] SKIP {fix['target_id']}: Cannot auto-fix '{fix['old_pattern']}'")
                continue

            update_query = """
            UPDATE outreach.company_target
            SET email_method = %s,
                updated_at = NOW()
            WHERE target_id = %s;
            """

            cur.execute(update_query, (fix['new_pattern'], fix['target_id']))
            print(f"[OK] FIXED {fix['target_id']}: {fix['old_pattern']} -> {fix['new_pattern']}")

        conn.commit()
        print(f"\n[OK] Applied {len([f for f in fixes if f['new_pattern']])} fixes")

def create_manual_review_csv(unknown_fixes):
    """Create CSV for manual review of unknown patterns"""
    if not unknown_fixes:
        return

    csv_path = "C:\\Users\\CUSTOM PC\\Desktop\\Cursor Builds\\barton-outreach-core\\unknown_patterns_manual_review.csv"

    with open(csv_path, 'w') as f:
        f.write("target_id,domain,old_pattern,suggested_fix,confidence\n")
        for fix in unknown_fixes:
            f.write(f"{fix['target_id']},{fix['domain']},{fix['old_pattern']},,{fix['confidence']}\n")

    print(f"\n[OK] Manual review CSV created: {csv_path}")

def main():
    print("\n" + "="*80)
    print("EMAIL PATTERN REMEDIATION SCRIPT")
    print("="*80)

    # Preview literal pattern fixes
    literal_fixes = preview_fixes(dry_run=True)

    # Preview hardcoded domain fixes
    domain_fixes = preview_hardcoded_domains(dry_run=True)

    # Create manual review CSV for unknown patterns
    unknown = [f for f in literal_fixes if f['new_pattern'] is None]
    if unknown:
        create_manual_review_csv(unknown)

    # Summary
    print("\n" + "="*80)
    print("REMEDIATION SUMMARY")
    print("="*80 + "\n")

    total_fixes = len([f for f in literal_fixes if f['new_pattern']])
    total_domain_fixes = len(domain_fixes)
    total_unknown = len(unknown)

    print(f"Literal Patterns:")
    print(f"  [OK] Auto-fixable: {total_fixes}")
    print(f"  [X] Manual review: {total_unknown}")
    print(f"\nHardcoded Domains:")
    print(f"  [OK] Auto-fixable: {total_domain_fixes}")
    print(f"\nTotal Impact: {total_fixes + total_domain_fixes} records")

    print("\n" + "="*80)
    print("NEXT STEPS")
    print("="*80 + "\n")
    print("1. Review preview output above")
    print("2. If unknown patterns exist, review unknown_patterns_manual_review.csv")
    print("3. To apply fixes, run: python fix_invalid_email_patterns.py --apply")
    print("4. Re-run analyze_email_patterns.py to verify fixes\n")

if __name__ == '__main__':
    import sys

    try:
        if '--apply' in sys.argv:
            # Apply fixes
            literal_fixes = preview_fixes(dry_run=True)
            domain_fixes = preview_hardcoded_domains(dry_run=True)

            confirm = input("\n[WARNING] Apply fixes to production database? (yes/no): ")
            if confirm.lower() == 'yes':
                all_fixes = literal_fixes + domain_fixes
                apply_fixes(all_fixes, dry_run=False)
            else:
                print("Aborted.")
        else:
            # Preview only
            main()

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

    finally:
        conn.close()
