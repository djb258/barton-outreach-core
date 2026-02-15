#!/usr/bin/env python3
"""
Validate & Fill Slots Pipeline
==============================
Phase 1: Validate ONE email per company to discover pattern
Phase 2: Once pattern is locked, fill all 3 slots with confidence

This is the efficient approach:
- Don't waste money validating 3 bad emails
- Validate 1 → lock pattern → fill slots
"""

import os
import sys
import time
import argparse
import requests
import psycopg2
from datetime import datetime
from typing import Optional, Tuple, List, Dict

# ============================================================================
# CONFIGURATION
# ============================================================================

API_URL = "https://api.millionverifier.com/api/v3/"
VALID_RESULTS = {'ok', 'valid', 'deliverable'}
RISKY_RESULTS = {'catch_all', 'risky', 'unknown'}
INVALID_RESULTS = {'invalid', 'disposable', 'error'}

PATTERN_MAP = {
    'first.last': '{first}.{last}@{domain}',
    'flast': '{f}{last}@{domain}',
    'firstl': '{first}{l}@{domain}',
    'first_last': '{first}_{last}@{domain}',
    'lastf': '{last}{f}@{domain}',
    'first': '{first}@{domain}',
    'last.first': '{last}.{first}@{domain}',
}

# ============================================================================
# DATABASE
# ============================================================================

def get_connection():
    return psycopg2.connect(
        host=os.environ['NEON_HOST'],
        database=os.environ['NEON_DATABASE'],
        user=os.environ['NEON_USER'],
        password=os.environ['NEON_PASSWORD'],
        sslmode='require'
    )

# ============================================================================
# EMAIL PATTERN DETECTION
# ============================================================================

def detect_pattern(email: str, first_name: str, last_name: str) -> Optional[str]:
    """Detect which pattern an email uses."""
    if not all([email, first_name, last_name]):
        return None
    
    local = email.split('@')[0].lower()
    first = first_name.lower().strip()
    last = last_name.lower().strip()
    f = first[0] if first else ''
    l = last[0] if last else ''
    
    patterns = {
        f'{first}.{last}': 'first.last',
        f'{f}{last}': 'flast',
        f'{first}{l}': 'firstl',
        f'{first}_{last}': 'first_last',
        f'{last}{f}': 'lastf',
        f'{first}': 'first',
        f'{last}.{first}': 'last.first',
        f'{first}{last}': 'firstlast',
    }
    
    return patterns.get(local)

def generate_email(pattern: str, first_name: str, last_name: str, domain: str) -> Optional[str]:
    """Generate email from pattern and name."""
    if not all([pattern, first_name, last_name, domain]):
        return None
    
    first = first_name.lower().strip()
    last = last_name.lower().strip()
    f = first[0] if first else ''
    l = last[0] if last else ''
    
    templates = {
        'first.last': f'{first}.{last}@{domain}',
        'flast': f'{f}{last}@{domain}',
        'firstl': f'{first}{l}@{domain}',
        'first_last': f'{first}_{last}@{domain}',
        'lastf': f'{last}{f}@{domain}',
        'first': f'{first}@{domain}',
        'last.first': f'{last}.{first}@{domain}',
        'firstlast': f'{first}{last}@{domain}',
    }
    
    return templates.get(pattern)

# ============================================================================
# MILLIONVERIFIER API
# ============================================================================

def verify_email(email: str, api_key: str) -> Tuple[str, str, dict]:
    """
    Verify single email with MillionVerifier.
    Returns: (status, result_code, full_response)
    status: 'valid', 'invalid', 'risky'
    """
    try:
        resp = requests.get(API_URL, params={'api': api_key, 'email': email}, timeout=30)
        data = resp.json()
        
        result = data.get('result', '').lower()
        
        if result in VALID_RESULTS:
            return 'valid', result, data
        elif result in RISKY_RESULTS:
            return 'risky', result, data
        else:
            return 'invalid', result, data
            
    except Exception as e:
        return 'error', str(e), {}

# ============================================================================
# PHASE 1: VALIDATE ONE PER COMPANY
# ============================================================================

def get_companies_needing_validation(conn) -> List[Dict]:
    """
    Get companies that need pattern validation.
    Returns ONE best candidate per company.
    
    Priority:
    1. Companies with no verified emails yet
    2. Best candidate: CEO > CFO > HR, better sources first
    """
    cur = conn.cursor()
    
    # Get companies with NO verified emails, pick best candidate
    cur.execute('''
    WITH companies_no_verified AS (
        -- Companies where NO email has been verified valid
        SELECT pm.company_unique_id
        FROM people.people_master pm
        WHERE pm.email IS NOT NULL AND pm.email != ''
        GROUP BY pm.company_unique_id
        HAVING BOOL_OR(pm.email_verified = TRUE) = FALSE
    ),
    candidates AS (
        -- For each company, rank people by quality
        SELECT 
            pm.unique_id as person_unique_id,
            pm.company_unique_id,
            pm.email,
            pm.first_name,
            pm.last_name,
            pm.title,
            pm.source_system,
            c.website_url,
            c.company_name,
            ROW_NUMBER() OVER (
                PARTITION BY pm.company_unique_id
                ORDER BY 
                    -- Prefer better sources
                    CASE pm.source_system 
                        WHEN 'apollo_import' THEN 1
                        WHEN 'clay' THEN 2
                        ELSE 3
                    END,
                    -- Prefer executive titles
                    CASE 
                        WHEN LOWER(pm.title) LIKE '%ceo%' OR LOWER(pm.title) LIKE '%chief executive%' THEN 1
                        WHEN LOWER(pm.title) LIKE '%cfo%' OR LOWER(pm.title) LIKE '%chief financial%' THEN 2
                        WHEN LOWER(pm.title) LIKE '%president%' THEN 3
                        WHEN LOWER(pm.title) LIKE '%owner%' THEN 4
                        WHEN LOWER(pm.title) LIKE '%hr%' OR LOWER(pm.title) LIKE '%human%' THEN 5
                        ELSE 6
                    END,
                    -- Prefer records not yet API-tested
                    CASE WHEN pm.email_verified_at IS NULL THEN 0 ELSE 1 END,
                    pm.created_at DESC
            ) as rn
        FROM companies_no_verified cnv
        JOIN people.people_master pm ON pm.company_unique_id = cnv.company_unique_id
        JOIN company.company_master c ON c.company_unique_id = pm.company_unique_id
        WHERE pm.email IS NOT NULL AND pm.email != ''
          AND pm.first_name IS NOT NULL AND pm.first_name != ''
          AND pm.last_name IS NOT NULL AND pm.last_name != ''
          -- Skip emails that look malformed (credentials in name)
          AND LENGTH(SPLIT_PART(pm.email, '@', 1)) < 40
    )
    SELECT 
        person_unique_id,
        company_unique_id,
        email,
        first_name,
        last_name,
        title,
        source_system,
        website_url,
        company_name
    FROM candidates
    WHERE rn = 1  -- Only the BEST candidate per company
    ORDER BY 
        CASE source_system 
            WHEN 'apollo_import' THEN 1
            WHEN 'clay' THEN 2
            ELSE 3
        END
    ''')
    
    columns = ['person_id', 'company_id', 'email', 'first_name', 'last_name', 
               'title', 'source', 'website', 'company_name']
    
    return [dict(zip(columns, row)) for row in cur.fetchall()]

def update_person_verification(conn, person_id: str, email: str, is_valid: bool, 
                                result_code: str, api_response: dict):
    """Update person record with verification result."""
    cur = conn.cursor()
    cur.execute('''
    UPDATE people.people_master
    SET email_verified = %s,
        email_verified_at = NOW(),
        email_verification_source = %s,
        updated_at = NOW()
    WHERE unique_id = %s
    ''', (is_valid, result_code, person_id))
    conn.commit()

def lock_company_pattern(conn, company_id: str, pattern: str, confidence: int = 90):
    """Lock the email pattern on company_master."""
    cur = conn.cursor()
    cur.execute('''
    UPDATE company.company_master
    SET email_pattern = %s,
        email_pattern_confidence = %s,
        email_pattern_source = 'millionverifier_validated',
        email_pattern_verified_at = NOW(),
        updated_at = NOW()
    WHERE company_unique_id = %s
    ''', (pattern, confidence, company_id))
    conn.commit()

def flag_company_for_research(conn, company_id: str, failed_pattern: str, failed_email: str):
    """Flag company as needing pattern research."""
    cur = conn.cursor()
    # Store in email_pattern_source that research is needed
    cur.execute('''
    UPDATE company.company_master
    SET email_pattern = %s,
        email_pattern_confidence = 0,
        email_pattern_source = %s,
        updated_at = NOW()
    WHERE company_unique_id = %s
    ''', (failed_pattern, f'needs_research::{failed_email}', company_id))
    conn.commit()

# ============================================================================
# PHASE 2: FILL SLOTS FOR VALIDATED COMPANIES
# ============================================================================

def get_companies_ready_for_slots(conn, limit: int = 100) -> List[Dict]:
    """
    Get companies that have a validated pattern but unfilled slots.
    """
    cur = conn.cursor()
    
    cur.execute('''
    SELECT 
        c.company_unique_id,
        c.company_name,
        c.email_pattern,
        c.website_url
    FROM company.company_master c
    WHERE c.email_pattern IS NOT NULL
      AND c.email_pattern_confidence >= 80
      AND c.email_pattern_verified_at IS NOT NULL
      -- Has unfilled slots
      AND EXISTS (
          SELECT 1 FROM people.company_slot cs
          WHERE cs.company_unique_id = c.company_unique_id
            AND cs.person_unique_id IS NULL
      )
    LIMIT %s
    ''', (limit,))
    
    columns = ['company_id', 'company_name', 'pattern', 'website']
    return [dict(zip(columns, row)) for row in cur.fetchall()]

def fill_slots_for_company(conn, company: Dict, dry_run: bool = False) -> int:
    """
    Fill empty slots for a company using the validated pattern.
    Returns number of slots filled.
    """
    cur = conn.cursor()
    
    # Get empty slots
    cur.execute('''
    SELECT slot_id, slot_type
    FROM people.company_slot
    WHERE company_unique_id = %s AND person_unique_id IS NULL
    ORDER BY 
        CASE slot_type 
            WHEN 'ceo' THEN 1 
            WHEN 'cfo' THEN 2 
            WHEN 'hr' THEN 3 
            ELSE 4 
        END
    ''', (company['company_id'],))
    
    empty_slots = cur.fetchall()
    if not empty_slots:
        return 0
    
    # Get available people with verified emails
    cur.execute('''
    SELECT unique_id, first_name, last_name, title, email
    FROM people.people_master
    WHERE company_unique_id = %s
      AND email_verified = TRUE
      AND unique_id NOT IN (
          SELECT person_unique_id FROM people.company_slot 
          WHERE person_unique_id IS NOT NULL
      )
    ORDER BY 
        CASE 
            WHEN LOWER(title) LIKE '%%ceo%%' THEN 1
            WHEN LOWER(title) LIKE '%%cfo%%' THEN 2
            WHEN LOWER(title) LIKE '%%president%%' THEN 3
            WHEN LOWER(title) LIKE '%%hr%%' THEN 4
            ELSE 5
        END
    ''', (company['company_id'],))
    
    available_people = cur.fetchall()
    
    filled = 0
    for (slot_id, slot_type), person in zip(empty_slots, available_people):
        person_id, first, last, title, email = person
        
        if not dry_run:
            cur.execute('''
            UPDATE people.company_slot
            SET person_unique_id = %s,
                filled_at = NOW(),
                filled_by = 'validate_and_fill_slots'
            WHERE slot_id = %s
            ''', (person_id, slot_id))
        
        filled += 1
    
    if not dry_run:
        conn.commit()
    
    return filled

# ============================================================================
# MAIN PIPELINE
# ============================================================================

def run_phase1(conn, api_key: str, limit: int, dry_run: bool = False) -> dict:
    """
    Phase 1: Validate ONE email per company.
    """
    stats = {
        'processed': 0,
        'valid': 0,
        'invalid': 0,
        'risky': 0,
        'errors': 0,
        'patterns_locked': 0,
        'flagged_for_research': 0,
    }
    
    print("\n" + "="*70)
    print("PHASE 1: VALIDATE ONE EMAIL PER COMPANY")
    print("="*70)
    
    candidates = get_companies_needing_validation(conn)
    
    if limit:
        candidates = candidates[:limit]
    
    print(f"[FOUND] {len(candidates)} companies to validate")
    
    if dry_run:
        print("[DRY RUN] Would validate these companies:")
        for c in candidates[:20]:
            domain = c['email'].split('@')[1] if '@' in c['email'] else 'no-domain'
            print(f"  {c['company_name'][:35]:35s} | {domain:25s} | {c['email']}")
        if len(candidates) > 20:
            print(f"  ... and {len(candidates) - 20} more")
        return stats
    
    print()
    
    for i, candidate in enumerate(candidates):
        email = candidate['email']
        company_name = candidate['company_name'][:30]
        
        print(f"[{i+1}/{len(candidates)}] {company_name:30s} | {email}")
        
        # Call MillionVerifier
        status, result, response = verify_email(email, api_key)
        stats['processed'] += 1
        
        # Update person record
        update_person_verification(
            conn, 
            candidate['person_id'], 
            email,
            status == 'valid',
            result,
            response
        )
        
        if status == 'valid':
            stats['valid'] += 1
            # Detect and lock pattern
            pattern = detect_pattern(email, candidate['first_name'], candidate['last_name'])
            if pattern:
                lock_company_pattern(conn, candidate['company_id'], pattern)
                stats['patterns_locked'] += 1
                print(f"  ✓ VALID - Pattern locked: {pattern}")
            else:
                print(f"  ✓ VALID - Pattern unknown")
        
        elif status == 'risky':
            stats['risky'] += 1
            print(f"  ? RISKY ({result})")
        
        else:
            stats['invalid'] += 1
            stats['flagged_for_research'] += 1
            # Flag for research
            pattern = detect_pattern(email, candidate['first_name'], candidate['last_name']) or 'unknown'
            flag_company_for_research(conn, candidate['company_id'], pattern, email)
            print(f"  ✗ INVALID - Flagged for research")
        
        # Rate limiting
        time.sleep(0.1)
    
    return stats

def run_phase2(conn, limit: int, dry_run: bool = False) -> dict:
    """
    Phase 2: Fill slots for companies with validated patterns.
    """
    stats = {
        'companies_processed': 0,
        'slots_filled': 0,
    }
    
    print("\n" + "="*70)
    print("PHASE 2: FILL SLOTS FOR VALIDATED COMPANIES")
    print("="*70)
    
    companies = get_companies_ready_for_slots(conn, limit or 1000)
    
    print(f"[FOUND] {len(companies)} companies ready for slot filling")
    
    if dry_run:
        print("[DRY RUN] Would fill slots for these companies:")
        for c in companies[:20]:
            print(f"  {c['company_name'][:40]:40s} | Pattern: {c['pattern']}")
        return stats
    
    for company in companies:
        filled = fill_slots_for_company(conn, company, dry_run)
        if filled > 0:
            stats['companies_processed'] += 1
            stats['slots_filled'] += filled
            print(f"  {company['company_name'][:40]:40s} | Filled {filled} slots")
    
    return stats

def main():
    parser = argparse.ArgumentParser(description='Validate & Fill Slots Pipeline')
    parser.add_argument('--phase', type=int, choices=[1, 2], 
                        help='Run specific phase (1=validate, 2=fill slots)')
    parser.add_argument('--limit', type=int, default=10,
                        help='Limit number of companies to process')
    parser.add_argument('--dry-run', action='store_true',
                        help='Preview without making changes')
    args = parser.parse_args()
    
    api_key = os.environ.get('MILLIONVERIFIER_API_KEY')
    if not api_key:
        print("[ERROR] MILLIONVERIFIER_API_KEY not set")
        sys.exit(1)
    
    print("="*70)
    print("VALIDATE & FILL SLOTS PIPELINE")
    print("="*70)
    print()
    print("Strategy:")
    print("  Phase 1: Validate ONE email per company → lock pattern")
    print("  Phase 2: Fill all 3 slots using validated pattern")
    print()
    print(f"[CONFIG] Limit: {args.limit}")
    print(f"[CONFIG] Dry Run: {args.dry_run}")
    print(f"[CONFIG] API Key: {api_key[:10]}...")
    
    conn = get_connection()
    
    try:
        if args.phase == 1 or args.phase is None:
            stats1 = run_phase1(conn, api_key, args.limit, args.dry_run)
            print("\n[PHASE 1 RESULTS]")
            for k, v in stats1.items():
                print(f"  {k}: {v}")
        
        if args.phase == 2 or args.phase is None:
            stats2 = run_phase2(conn, args.limit, args.dry_run)
            print("\n[PHASE 2 RESULTS]")
            for k, v in stats2.items():
                print(f"  {k}: {v}")
    
    finally:
        conn.close()
    
    print("\n[DONE]")

if __name__ == '__main__':
    main()
