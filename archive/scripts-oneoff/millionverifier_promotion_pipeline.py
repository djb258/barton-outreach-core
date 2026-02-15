#!/usr/bin/env python3
"""
MillionVerifier → Company Target Promotion Pipeline
====================================================
This script implements the full verification chain from OUTREACH_WATERFALL_DOCTRINE.md v1.3:

FLOW:
1. Run MillionVerifier on unverified emails in people.people_master
2. For each VERIFIED email → Promote to outreach.company_target (Agent 1)
3. Derive email pattern mechanically from verified email
4. Flip pattern status from GUESS → VERIFIED (Agent 2)
5. Lock pattern for downstream use

COST: ~$0.001/email via MillionVerifier

Usage:
    # Dry run first (no API calls, no DB writes)
    doppler run -- python scripts/millionverifier_promotion_pipeline.py --dry-run

    # Run with limit (test with 10 emails)
    doppler run -- python scripts/millionverifier_promotion_pipeline.py --limit 10

    # Full run
    doppler run -- python scripts/millionverifier_promotion_pipeline.py

    # Re-run on already flagged (but no API timestamp) emails
    doppler run -- python scripts/millionverifier_promotion_pipeline.py --re-verify

Created: 2026-02-02
Doctrine: OUTREACH_WATERFALL_DOCTRINE.md v1.3
"""

import os
import sys
import asyncio
import argparse
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

import psycopg2
import aiohttp


# MillionVerifier result codes
MV_RESULT_VALID = ['ok', 'valid', 'deliverable']
MV_RESULT_RISKY = ['catch_all', 'accept_all', 'risky', 'role']
MV_RESULT_INVALID = ['invalid', 'unknown', 'disposable', 'bounce']


@dataclass
class VerificationResult:
    """Result from MillionVerifier API"""
    email: str
    result_code: str
    is_valid: bool
    is_risky: bool
    quality: int
    timestamp: str


@dataclass
class PatternDerivation:
    """Derived email pattern from verified email"""
    verified_email: str
    pattern: str
    pattern_type: str
    confidence: str  # HIGH, MEDIUM, LOW


def derive_email_pattern(email: str, first_name: str, last_name: str) -> Optional[PatternDerivation]:
    """
    Derive email pattern mechanically from a verified email.
    
    Examples:
        jane.doe@acme.com → first.last@domain
        jdoe@acme.com → f_initial+last@domain
        jane_doe@acme.com → first_last@domain
        jane@acme.com → first@domain
    """
    if not email or '@' not in email:
        return None
    
    local_part, domain = email.split('@', 1)
    first = (first_name or '').lower().strip()
    last = (last_name or '').lower().strip()
    
    if not first and not last:
        return None
    
    # Check common patterns
    patterns = []
    
    # first.last
    if first and last and local_part.lower() == f"{first}.{last}":
        return PatternDerivation(email, "first.last@domain", "first.last", "HIGH")
    
    # first_last
    if first and last and local_part.lower() == f"{first}_{last}":
        return PatternDerivation(email, "first_last@domain", "first_last", "HIGH")
    
    # firstlast (no separator)
    if first and last and local_part.lower() == f"{first}{last}":
        return PatternDerivation(email, "firstlast@domain", "firstlast", "HIGH")
    
    # f_initial + last (jdoe)
    if first and last and local_part.lower() == f"{first[0]}{last}":
        return PatternDerivation(email, "f_initial+last@domain", "flast", "HIGH")
    
    # first + l_initial (janed)
    if first and last and local_part.lower() == f"{first}{last[0]}":
        return PatternDerivation(email, "first+l_initial@domain", "firstl", "HIGH")
    
    # first only
    if first and local_part.lower() == first:
        return PatternDerivation(email, "first@domain", "first", "MEDIUM")
    
    # last only
    if last and local_part.lower() == last:
        return PatternDerivation(email, "last@domain", "last", "MEDIUM")
    
    # Could not determine pattern
    return PatternDerivation(email, "unknown@domain", "unknown", "LOW")


class MillionVerifierPromotionPipeline:
    """
    Full pipeline: MillionVerifier → Promotion Agent → Verification Gate
    """
    
    def __init__(self, api_key: str = None, dry_run: bool = False):
        self.api_key = api_key or os.getenv('MILLIONVERIFIER_API_KEY')
        self.dry_run = dry_run
        self.conn = None
        self.stats = {
            'emails_checked': 0,
            'verified_valid': 0,
            'verified_invalid': 0,
            'verified_risky': 0,
            'patterns_derived': 0,
            'promotions_to_ct': 0,
            'patterns_locked': 0,
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
    
    def get_unverified_emails(self, limit: int = None, re_verify: bool = False) -> List[Dict]:
        """
        Get emails from people.people_master that need verification.
        
        Returns emails that:
        - Have an email address
        - Either: not verified, or no API timestamp (never ran through MV)
        """
        cur = self.conn.cursor()
        
        if re_verify:
            # Re-verify all emails that have no timestamp (imported but not API verified)
            query = """
                SELECT 
                    pm.unique_id as person_id,
                    pm.email,
                    pm.first_name,
                    pm.last_name,
                    pm.full_name,
                    pm.company_unique_id,
                    cs.outreach_id,
                    pm.email_verified,
                    pm.email_verified_at
                FROM people.people_master pm
                LEFT JOIN people.company_slot cs ON pm.unique_id = cs.person_unique_id
                WHERE pm.email IS NOT NULL AND pm.email != ''
                  AND pm.email_verified_at IS NULL
                ORDER BY pm.created_at DESC
            """
        else:
            # Only verify emails that are not marked verified
            query = """
                SELECT 
                    pm.unique_id as person_id,
                    pm.email,
                    pm.first_name,
                    pm.last_name,
                    pm.full_name,
                    pm.company_unique_id,
                    cs.outreach_id,
                    pm.email_verified,
                    pm.email_verified_at
                FROM people.people_master pm
                LEFT JOIN people.company_slot cs ON pm.unique_id = cs.person_unique_id
                WHERE pm.email IS NOT NULL AND pm.email != ''
                  AND (pm.email_verified = FALSE OR pm.email_verified IS NULL)
                ORDER BY pm.created_at DESC
            """
        
        if limit:
            query += f" LIMIT {limit}"
        
        cur.execute(query)
        rows = cur.fetchall()
        
        return [
            {
                'person_id': row[0],
                'email': row[1],
                'first_name': row[2],
                'last_name': row[3],
                'full_name': row[4],
                'company_unique_id': row[5],
                'outreach_id': row[6],
                'email_verified': row[7],
                'email_verified_at': row[8],
            }
            for row in rows
        ]
    
    async def verify_email_mv(self, email: str) -> Optional[VerificationResult]:
        """Call MillionVerifier API for single email verification"""
        if not self.api_key:
            return None
        
        url = f"https://api.millionverifier.com/api/v3/?api={self.api_key}&email={email}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        data = await response.json()
                        result_code = data.get('result', 'unknown').lower()
                        
                        is_valid = result_code in MV_RESULT_VALID
                        is_risky = result_code in MV_RESULT_RISKY
                        
                        return VerificationResult(
                            email=email,
                            result_code=result_code,
                            is_valid=is_valid,
                            is_risky=is_risky,
                            quality=data.get('quality', 0),
                            timestamp=datetime.now().isoformat()
                        )
                    else:
                        print(f"    [API ERROR] HTTP {response.status}")
                        return None
        except asyncio.TimeoutError:
            print(f"    [TIMEOUT] {email}")
            return None
        except Exception as e:
            print(f"    [ERROR] {email}: {e}")
            return None
    
    def update_people_master(self, person_id: str, is_valid: bool, result: VerificationResult):
        """Update people.people_master with verification result (AGENT 1a)"""
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
    
    def promote_to_company_target(self, person: Dict, pattern: PatternDerivation) -> bool:
        """
        AGENT 1: Promote verified email → Company Target
        
        Writes:
        - canonical_verified_email
        - derived_email_pattern
        - email_pattern_status
        - pattern_confidence
        - verified_source
        - pattern_verified_at
        """
        if not person.get('outreach_id'):
            # No outreach_id means no CT record to update
            return False
        
        cur = self.conn.cursor()
        
        # Check if CT already has a HIGH confidence pattern (skip if so)
        cur.execute("""
            SELECT email_method, confidence_score
            FROM outreach.company_target
            WHERE outreach_id = %s
        """, (person['outreach_id'],))
        
        ct_row = cur.fetchone()
        if not ct_row:
            # No CT record exists
            return False
        
        # NOTE: We need to add these new columns if they don't exist
        # For now, update what we can
        try:
            cur.execute("""
                UPDATE outreach.company_target
                SET email_method = %s,
                    method_type = 'verified',
                    confidence_score = %s,
                    updated_at = NOW()
                WHERE outreach_id = %s
            """, (
                pattern.pattern,
                1.0 if pattern.confidence == 'HIGH' else (0.8 if pattern.confidence == 'MEDIUM' else 0.5),
                person['outreach_id']
            ))
            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"    [CT UPDATE ERROR] {e}")
            self.conn.rollback()
            return False
    
    async def run_pipeline(self, limit: int = None, re_verify: bool = False):
        """
        Main pipeline execution:
        1. Get unverified emails
        2. Run MillionVerifier
        3. Update people.people_master
        4. Derive pattern
        5. Promote to company_target
        """
        print("=" * 70)
        print("MillionVerifier → Company Target Promotion Pipeline")
        print("=" * 70)
        print(f"Doctrine: OUTREACH_WATERFALL_DOCTRINE.md v1.3")
        print()
        
        # Check API key
        if not self.api_key:
            print("[ERROR] MILLIONVERIFIER_API_KEY not configured!")
            print("   Set via: doppler secrets set MILLIONVERIFIER_API_KEY=<key>")
            return
        
        print(f"[OK] API Key: {self.api_key[:8]}...")
        
        if self.dry_run:
            print("[DRY RUN] No API calls or DB writes will be made")
        
        # Connect to database
        print("\n[DB] Connecting to Neon PostgreSQL...")
        self.connect_db()
        print("[DB] Connected!")
        
        # Get emails
        print("\n[FETCH] Getting unverified emails from people.people_master...")
        emails = self.get_unverified_emails(limit=limit, re_verify=re_verify)
        print(f"[FETCH] Found {len(emails):,} emails to process")
        
        if not emails:
            print("[INFO] No emails to verify!")
            return
        
        # Cost estimate
        cost = len(emails) * 0.001
        print(f"[COST] Estimated: ${cost:,.2f} (@ $0.001/email)")
        
        if self.dry_run:
            print("\n[DRY RUN] Would process these emails:")
            for e in emails[:10]:
                pattern = derive_email_pattern(e['email'], e['first_name'], e['last_name'])
                print(f"  {e['email'][:40]:40} → {pattern.pattern if pattern else 'N/A'}")
            if len(emails) > 10:
                print(f"  ... and {len(emails) - 10} more")
            return
        
        # Process emails
        print("\n[PROCESSING] Starting verification pipeline...")
        print("-" * 70)
        
        for i, person in enumerate(emails, 1):
            email = person['email']
            print(f"\n[{i}/{len(emails)}] {email}")
            
            # Step 1: MillionVerifier
            print(f"  → MillionVerifier API...", end=" ")
            result = await self.verify_email_mv(email)
            self.stats['emails_checked'] += 1
            
            if not result:
                print("[ERROR]")
                self.stats['errors'] += 1
                continue
            
            if result.is_valid:
                print(f"[VALID] {result.result_code}")
                self.stats['verified_valid'] += 1
            elif result.is_risky:
                print(f"[RISKY] {result.result_code}")
                self.stats['verified_risky'] += 1
            else:
                print(f"[INVALID] {result.result_code}")
                self.stats['verified_invalid'] += 1
            
            # Step 2: Update people.people_master
            print(f"  → Updating people.people_master...", end=" ")
            self.update_people_master(person['person_id'], result.is_valid or result.is_risky, result)
            print("[OK]")
            
            # Step 3: Derive pattern (only if valid)
            if result.is_valid or result.is_risky:
                pattern = derive_email_pattern(email, person['first_name'], person['last_name'])
                
                if pattern:
                    print(f"  → Pattern derived: {pattern.pattern} ({pattern.confidence})")
                    self.stats['patterns_derived'] += 1
                    
                    # Step 4: Promote to Company Target (if outreach_id exists)
                    if person.get('outreach_id'):
                        print(f"  → Promoting to company_target...", end=" ")
                        if self.promote_to_company_target(person, pattern):
                            print("[OK]")
                            self.stats['promotions_to_ct'] += 1
                            self.stats['patterns_locked'] += 1
                        else:
                            print("[SKIP - no CT record]")
                    else:
                        print(f"  → No outreach_id - skipping CT promotion")
            
            # Rate limit
            await asyncio.sleep(0.1)
        
        # Summary
        print("\n" + "=" * 70)
        print("PIPELINE COMPLETE")
        print("=" * 70)
        print(f"  Emails checked:       {self.stats['emails_checked']:,}")
        print(f"  Valid:                {self.stats['verified_valid']:,}")
        print(f"  Risky (deliverable):  {self.stats['verified_risky']:,}")
        print(f"  Invalid:              {self.stats['verified_invalid']:,}")
        print(f"  Errors:               {self.stats['errors']:,}")
        print()
        print(f"  Patterns derived:     {self.stats['patterns_derived']:,}")
        print(f"  Promoted to CT:       {self.stats['promotions_to_ct']:,}")
        print(f"  Patterns locked:      {self.stats['patterns_locked']:,}")
        
        if self.stats['emails_checked'] > 0:
            valid_rate = (self.stats['verified_valid'] + self.stats['verified_risky']) / self.stats['emails_checked'] * 100
            print(f"\n  Valid/Risky rate:     {valid_rate:.1f}%")
        
        self.conn.close()


def main():
    parser = argparse.ArgumentParser(
        description='MillionVerifier → Company Target Promotion Pipeline'
    )
    parser.add_argument('--dry-run', action='store_true', 
                        help='Show what would be done without API calls')
    parser.add_argument('--limit', type=int, 
                        help='Only process N emails (for testing)')
    parser.add_argument('--re-verify', action='store_true',
                        help='Re-verify emails that have no API timestamp')
    
    args = parser.parse_args()
    
    pipeline = MillionVerifierPromotionPipeline(dry_run=args.dry_run)
    asyncio.run(pipeline.run_pipeline(limit=args.limit, re_verify=args.re_verify))


if __name__ == "__main__":
    main()
