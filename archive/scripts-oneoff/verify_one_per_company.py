#!/usr/bin/env python3
"""
One-Per-Company Email Verification Pipeline
============================================
Validates ONE email per company. If valid → lock pattern. If invalid → flag for research.

This is the efficient approach from OUTREACH_WATERFALL_DOCTRINE.md v1.3:
- One verified email = pattern for entire company
- Failed validation = company needs pattern research

Strategy:
1. Group all unverified emails by company
2. Pick the BEST candidate per company (prefer filled slots, CEO > CFO > HR)
3. Verify only that one email
4. If VALID: derive pattern, promote to CT, lock
5. If INVALID: flag company for pattern research

Usage:
    # Dry run
    doppler run -- python scripts/verify_one_per_company.py --dry-run

    # Test with 10 companies
    doppler run -- python scripts/verify_one_per_company.py --limit 10

    # Full run
    doppler run -- python scripts/verify_one_per_company.py

Created: 2026-02-03
"""

import os
import sys
import asyncio
import argparse
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict

import psycopg2
import aiohttp


# MillionVerifier result codes
MV_RESULT_VALID = ['ok', 'valid', 'deliverable']
MV_RESULT_RISKY = ['catch_all', 'accept_all', 'risky', 'role']


@dataclass
class CompanyCandidate:
    """Best email candidate for a company"""
    company_unique_id: str
    outreach_id: str
    person_id: str
    email: str
    first_name: str
    last_name: str
    slot_type: str
    source_system: str
    priority: int  # Lower = better


def derive_email_pattern(email: str, first_name: str, last_name: str) -> Tuple[str, str]:
    """Derive email pattern from verified email. Returns (pattern, confidence)."""
    if not email or '@' not in email:
        return ('unknown@domain', 'LOW')
    
    local_part, domain = email.split('@', 1)
    first = (first_name or '').lower().strip()
    last = (last_name or '').lower().strip()
    
    if not first and not last:
        return ('unknown@domain', 'LOW')
    
    # Check common patterns
    if first and last and local_part.lower() == f"{first}.{last}":
        return ("first.last@domain", "HIGH")
    if first and last and local_part.lower() == f"{first}_{last}":
        return ("first_last@domain", "HIGH")
    if first and last and local_part.lower() == f"{first}{last}":
        return ("firstlast@domain", "HIGH")
    if first and last and local_part.lower() == f"{first[0]}{last}":
        return ("flast@domain", "HIGH")
    if first and last and local_part.lower() == f"{first}{last[0]}":
        return ("firstl@domain", "HIGH")
    if first and local_part.lower() == first:
        return ("first@domain", "MEDIUM")
    if last and local_part.lower() == last:
        return ("last@domain", "MEDIUM")
    
    return ("unknown@domain", "LOW")


class OnePerCompanyVerifier:
    """Verify one email per company, then lock or flag."""
    
    def __init__(self, api_key: str = None, dry_run: bool = False):
        self.api_key = api_key or os.getenv('MILLIONVERIFIER_API_KEY')
        self.dry_run = dry_run
        self.conn = None
        self.stats = {
            'companies_processed': 0,
            'emails_verified': 0,
            'valid': 0,
            'invalid': 0,
            'patterns_locked': 0,
            'flagged_for_research': 0,
            'errors': 0,
        }
    
    def connect_db(self):
        """Connect to Neon PostgreSQL"""
        self.conn = psycopg2.connect(
            host=os.environ['NEON_HOST'],
            database=os.environ['NEON_DATABASE'],
            user=os.environ['NEON_USER'],
            password=os.environ['NEON_PASSWORD'],
            sslmode='require'
        )
        return self.conn
    
    def get_companies_needing_verification(self, limit: int = None) -> Dict[str, CompanyCandidate]:
        """
        Get ONE best candidate email per company.
        
        Priority:
        1. Filled slots (CEO > CFO > HR)
        2. Apollo/Clay source (higher quality)
        3. Most recent
        """
        cur = self.conn.cursor()
        
        # Get all unverified emails with company and slot info
        cur.execute("""
            SELECT 
                pm.company_unique_id,
                cs.outreach_id,
                pm.unique_id as person_id,
                pm.email,
                pm.first_name,
                pm.last_name,
                COALESCE(cs.slot_type, 'OTHER') as slot_type,
                COALESCE(pm.source_system, 'unknown') as source_system,
                cs.is_filled
            FROM people.people_master pm
            LEFT JOIN people.company_slot cs ON pm.unique_id = cs.person_unique_id
            WHERE pm.email IS NOT NULL AND pm.email != ''
              AND (pm.email_verified = FALSE OR pm.email_verified IS NULL)
              AND pm.email_verified_at IS NULL
            ORDER BY 
                pm.company_unique_id,
                -- Priority: filled slots first
                CASE WHEN cs.is_filled = TRUE THEN 0 ELSE 1 END,
                -- Priority: CEO > CFO > HR > OTHER
                CASE cs.slot_type 
                    WHEN 'CEO' THEN 1 
                    WHEN 'CFO' THEN 2 
                    WHEN 'HR' THEN 3 
                    ELSE 4 
                END,
                -- Priority: better sources
                CASE pm.source_system 
                    WHEN 'apollo_import' THEN 1 
                    WHEN 'clay' THEN 2 
                    ELSE 3 
                END,
                pm.created_at DESC
        """)
        
        rows = cur.fetchall()
        
        # Group by company, take first (best) candidate per company
        companies = {}
        for row in rows:
            company_id = row[0]
            if company_id and company_id not in companies:
                companies[company_id] = CompanyCandidate(
                    company_unique_id=row[0],
                    outreach_id=row[1],
                    person_id=row[2],
                    email=row[3],
                    first_name=row[4] or '',
                    last_name=row[5] or '',
                    slot_type=row[6],
                    source_system=row[7],
                    priority=0
                )
        
        # Apply limit
        if limit:
            companies = dict(list(companies.items())[:limit])
        
        return companies
    
    async def verify_email(self, email: str) -> Tuple[bool, str]:
        """Call MillionVerifier API. Returns (is_valid, result_code)."""
        if not self.api_key:
            return (False, 'no_api_key')
        
        url = f"https://api.millionverifier.com/api/v3/?api={self.api_key}&email={email}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        data = await response.json()
                        result_code = data.get('result', 'unknown').lower()
                        is_valid = result_code in MV_RESULT_VALID or result_code in MV_RESULT_RISKY
                        return (is_valid, result_code)
                    else:
                        return (False, f'http_{response.status}')
        except asyncio.TimeoutError:
            return (False, 'timeout')
        except Exception as e:
            return (False, f'error_{str(e)[:20]}')
    
    def update_person_verified(self, person_id: str, is_valid: bool):
        """Update people.people_master with verification result."""
        cur = self.conn.cursor()
        cur.execute("""
            UPDATE people.people_master
            SET email_verified = %s,
                email_verified_at = %s,
                email_verification_source = 'MillionVerifier',
                updated_at = NOW()
            WHERE unique_id = %s
        """, (is_valid, datetime.now(), person_id))
        self.conn.commit()
    
    def promote_pattern_to_ct(self, candidate: CompanyCandidate, pattern: str, confidence: str) -> bool:
        """Promote verified pattern to company_target."""
        if not candidate.outreach_id:
            return False
        
        cur = self.conn.cursor()
        try:
            cur.execute("""
                UPDATE outreach.company_target
                SET email_method = %s,
                    method_type = 'verified',
                    confidence_score = %s,
                    updated_at = NOW()
                WHERE outreach_id = %s
            """, (
                pattern,
                1.0 if confidence == 'HIGH' else (0.8 if confidence == 'MEDIUM' else 0.5),
                candidate.outreach_id
            ))
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            return False
    
    def flag_company_for_research(self, candidate: CompanyCandidate, reason: str):
        """
        Flag company as needing pattern research.
        
        For now, we'll track in people.people_errors. In future, 
        this could trigger a research workflow.
        """
        cur = self.conn.cursor()
        try:
            # Check if people_errors table exists and has right columns
            cur.execute("""
                INSERT INTO people.people_errors (
                    person_unique_id,
                    error_type,
                    error_message,
                    created_at
                ) VALUES (%s, %s, %s, NOW())
                ON CONFLICT DO NOTHING
            """, (
                candidate.person_id,
                'PATTERN_RESEARCH_NEEDED',
                f"Email validation failed ({reason}). Company needs pattern research. Email: {candidate.email}"
            ))
            self.conn.commit()
        except Exception as e:
            # Table might not have this schema, just log
            self.conn.rollback()
            print(f"    [NOTE] Could not log to people_errors: {e}")
    
    async def run(self, limit: int = None):
        """Main execution."""
        print("=" * 70)
        print("One-Per-Company Email Verification")
        print("=" * 70)
        print("Strategy: Verify ONE email per company → lock pattern OR flag for research")
        print()
        
        if not self.api_key:
            print("[ERROR] MILLIONVERIFIER_API_KEY not configured!")
            return
        
        print(f"[OK] API Key: {self.api_key[:8]}...")
        
        if self.dry_run:
            print("[DRY RUN] No API calls or DB writes")
        
        # Connect
        print("\n[DB] Connecting...")
        self.connect_db()
        print("[DB] Connected!")
        
        # Get companies
        print("\n[FETCH] Getting best candidate per company...")
        companies = self.get_companies_needing_verification(limit=limit)
        print(f"[FETCH] Found {len(companies):,} companies to verify")
        
        if not companies:
            print("[INFO] No companies need verification!")
            return
        
        # Cost estimate
        cost = len(companies) * 0.001
        print(f"[COST] Estimated: ${cost:,.2f} (ONE email per company)")
        
        if self.dry_run:
            print("\n[DRY RUN] Would verify these companies:")
            for i, (cid, c) in enumerate(list(companies.items())[:15]):
                print(f"  {c.email[:40]:40} | {c.slot_type:6} | {c.source_system}")
            if len(companies) > 15:
                print(f"  ... and {len(companies) - 15} more companies")
            return
        
        # Process
        print("\n[PROCESSING] Starting verification...")
        print("-" * 70)
        
        for i, (company_id, candidate) in enumerate(companies.items(), 1):
            print(f"\n[{i}/{len(companies)}] Company: {company_id[:20]}...")
            print(f"    Email: {candidate.email}")
            print(f"    Slot: {candidate.slot_type} | Source: {candidate.source_system}")
            
            # Verify
            print(f"    → MillionVerifier...", end=" ")
            is_valid, result_code = await self.verify_email(candidate.email)
            self.stats['emails_verified'] += 1
            self.stats['companies_processed'] += 1
            
            if is_valid:
                print(f"[VALID] {result_code}")
                self.stats['valid'] += 1
                
                # Update person
                self.update_person_verified(candidate.person_id, True)
                
                # Derive pattern
                pattern, confidence = derive_email_pattern(
                    candidate.email, candidate.first_name, candidate.last_name
                )
                print(f"    → Pattern: {pattern} ({confidence})")
                
                # Promote to CT
                if candidate.outreach_id:
                    print(f"    → Promoting to CT...", end=" ")
                    if self.promote_pattern_to_ct(candidate, pattern, confidence):
                        print("[OK - LOCKED]")
                        self.stats['patterns_locked'] += 1
                    else:
                        print("[SKIP]")
                else:
                    print(f"    → No outreach_id - skipping CT")
            else:
                print(f"[INVALID] {result_code}")
                self.stats['invalid'] += 1
                
                # Update person as invalid
                self.update_person_verified(candidate.person_id, False)
                
                # Flag for research
                print(f"    → Flagging for pattern research...")
                self.flag_company_for_research(candidate, result_code)
                self.stats['flagged_for_research'] += 1
            
            # Rate limit
            await asyncio.sleep(0.1)
        
        # Summary
        print("\n" + "=" * 70)
        print("VERIFICATION COMPLETE")
        print("=" * 70)
        print(f"  Companies processed:     {self.stats['companies_processed']:,}")
        print(f"  Emails verified:         {self.stats['emails_verified']:,}")
        print()
        print(f"  ✅ Valid (patterns locked): {self.stats['valid']:,}")
        print(f"  ❌ Invalid (need research): {self.stats['invalid']:,}")
        print()
        print(f"  Patterns promoted to CT:   {self.stats['patterns_locked']:,}")
        print(f"  Flagged for research:      {self.stats['flagged_for_research']:,}")
        
        if self.stats['companies_processed'] > 0:
            valid_rate = self.stats['valid'] / self.stats['companies_processed'] * 100
            print(f"\n  Valid rate: {valid_rate:.1f}%")
        
        self.conn.close()


def main():
    parser = argparse.ArgumentParser(description='One-per-company email verification')
    parser.add_argument('--dry-run', action='store_true', help='No API calls')
    parser.add_argument('--limit', type=int, help='Limit companies to verify')
    
    args = parser.parse_args()
    
    verifier = OnePerCompanyVerifier(dry_run=args.dry_run)
    asyncio.run(verifier.run(limit=args.limit))


if __name__ == "__main__":
    main()
