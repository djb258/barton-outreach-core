#!/usr/bin/env python3
"""
Slot Email Verification Pipeline (Deduplicated)
================================================

Verifies ALL filled slot emails via Million Verifier.
DEDUPLICATES emails so each unique email only costs 1 credit.

Usage:
    # Dry run (show what would be done)
    doppler run -- python scripts/verify_slot_emails.py --dry-run

    # Verify 100 emails (test run)
    doppler run -- python scripts/verify_slot_emails.py --limit 100

    # Full verification
    doppler run -- python scripts/verify_slot_emails.py

    # Export results to CSV
    doppler run -- python scripts/verify_slot_emails.py --export

Created: 2026-02-07
"""

import os
import sys
import asyncio
import argparse
import csv
from datetime import datetime
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict

import psycopg2
import aiohttp


# MillionVerifier result classifications
MV_VALID = {'ok', 'valid', 'deliverable'}
MV_RISKY = {'catch_all', 'accept_all', 'risky', 'role'}
MV_INVALID = {'invalid', 'unknown', 'disposable', 'bounce', 'error'}


@dataclass
class EmailVerificationResult:
    """Verification result for a unique email"""
    email: str
    result: str  # ok, invalid, risky, etc.
    result_code: int
    quality: str
    subresult: str
    is_free: bool
    is_role: bool
    credits_used: int
    verified_at: datetime

    @property
    def status(self) -> str:
        """Return VALID, RISKY, or INVALID"""
        if self.result in MV_VALID:
            return 'VALID'
        elif self.result in MV_RISKY:
            return 'RISKY'
        else:
            return 'INVALID'


@dataclass
class InvalidSlotRecord:
    """Track an invalid email slot that needs a new contact"""
    outreach_id: str
    domain: str
    slot_type: str
    email: str
    result: str
    subresult: str


@dataclass
class VerificationStats:
    """Track verification statistics"""
    unique_emails: int = 0
    already_verified: int = 0
    to_verify: int = 0

    verified_valid: int = 0
    verified_risky: int = 0
    verified_invalid: int = 0
    api_errors: int = 0

    credits_used: int = 0
    people_updated: int = 0
    message_ready: int = 0  # Count of people marked outreach_ready = TRUE

    # Track which slots need more work - with full details
    invalid_slots: List[InvalidSlotRecord] = field(default_factory=list)


class SlotEmailVerifier:
    """
    Verifies emails in filled slots with deduplication.
    Each unique email = 1 API credit maximum.
    """

    def __init__(self, dry_run: bool = False):
        self.api_key = os.getenv('MILLIONVERIFIER_API_KEY')
        self.database_url = os.getenv('DATABASE_URL')
        self.dry_run = dry_run
        self.conn = None
        self.stats = VerificationStats()

        # Cache: email -> verification result
        self.verified_cache: Dict[str, EmailVerificationResult] = {}

        # Map: email -> list of person_unique_ids
        self.email_to_people: Dict[str, List[str]] = defaultdict(list)

    def connect(self):
        """Connect to database with keepalive settings"""
        self.conn = psycopg2.connect(
            self.database_url,
            keepalives=1,
            keepalives_idle=30,
            keepalives_interval=10,
            keepalives_count=5
        )
        self.conn.autocommit = True
        return self.conn

    def ping_db(self):
        """Keep connection alive by running a simple query"""
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT 1")
            cur.fetchone()
            return True
        except Exception:
            self.reconnect()
            return False

    def get_slot_emails(self) -> Dict[str, Dict]:
        """
        Get all unique emails from filled slots.
        Returns: {email: {person_ids: [...], slot_types: set(), already_verified: bool}}
        """
        cur = self.conn.cursor()

        # Get all filled slots with their people AND company domain
        # Order by source_system to prioritize Hunter emails (higher quality) first
        cur.execute("""
            SELECT
                pm.unique_id as person_id,
                pm.email,
                pm.email_verified,
                pm.email_verified_at,
                cs.slot_type,
                cs.outreach_id,
                o.domain
            FROM people.company_slot cs
            JOIN people.people_master pm ON cs.person_unique_id = pm.unique_id
            LEFT JOIN outreach.outreach o ON cs.outreach_id = o.outreach_id
            WHERE cs.is_filled = TRUE
              AND pm.email IS NOT NULL
              AND pm.email != ''
            ORDER BY
                CASE pm.source_system
                    WHEN 'hunter' THEN 1
                    WHEN 'clay' THEN 2
                    WHEN 'apollo_import' THEN 3
                    ELSE 4
                END,
                pm.email
        """)

        rows = cur.fetchall()

        # Aggregate by unique email
        emails: Dict[str, Dict] = {}

        for row in rows:
            person_id, email, verified, verified_at, slot_type, outreach_id, domain = row
            email_lower = email.lower().strip()

            if email_lower not in emails:
                emails[email_lower] = {
                    'email': email,
                    'person_ids': [],
                    'slot_types': set(),
                    'outreach_ids': set(),
                    'domains': set(),
                    'slot_details': [],  # List of (outreach_id, domain, slot_type) tuples
                    'already_verified': False,
                    'verified_at': None,
                }

            emails[email_lower]['person_ids'].append(person_id)
            emails[email_lower]['slot_types'].add(slot_type)
            emails[email_lower]['outreach_ids'].add(outreach_id)
            if domain:
                emails[email_lower]['domains'].add(domain)
            emails[email_lower]['slot_details'].append((outreach_id, domain or '', slot_type))

            # If ANY record has been through verification (regardless of result), skip it
            # This prevents re-verifying emails we already know are invalid
            if verified_at is not None:
                emails[email_lower]['already_verified'] = True
                emails[email_lower]['verified_at'] = verified_at

        return emails

    async def verify_single_email(self, email: str) -> Optional[EmailVerificationResult]:
        """Verify a single email via Million Verifier API"""

        url = f"https://api.millionverifier.com/api/v3/?api={self.api_key}&email={email}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        data = await response.json()

                        if data.get('error'):
                            print(f"    API Error: {data['error']}")
                            return None

                        return EmailVerificationResult(
                            email=email,
                            result=data.get('result', 'unknown').lower(),
                            result_code=data.get('resultcode', -1),
                            quality=data.get('quality', 'unknown'),
                            subresult=data.get('subresult', ''),
                            is_free=data.get('free', False),
                            is_role=data.get('role', False),
                            credits_used=1,
                            verified_at=datetime.now(),
                        )
                    else:
                        print(f"    HTTP {response.status}")
                        return None

        except asyncio.TimeoutError:
            print(f"    Timeout")
            return None
        except Exception as e:
            print(f"    Error: {e}")
            return None

    def reconnect(self):
        """Reconnect to database if connection was lost"""
        try:
            if self.conn:
                self.conn.close()
        except:
            pass

        print("    Reconnecting to database...")
        self.connect()
        self.conn.commit()  # Start fresh transaction
        print("    Reconnected!")

    def update_people_records(self, email: str, result: EmailVerificationResult, person_ids: List[str]):
        """Update all people_master records with this email"""

        if self.dry_run:
            return len(person_ids)

        is_valid = result.status in ('VALID', 'RISKY')
        is_message_ready = result.status == 'VALID'  # Only VALID emails are message-ready (not RISKY)

        # Retry with reconnection on failure
        for attempt in range(3):
            try:
                cur = self.conn.cursor()
                cur.execute("""
                    UPDATE people.people_master
                    SET email_verified = %s,
                        email_verified_at = %s,
                        email_verification_source = 'MillionVerifier',
                        outreach_ready = %s,
                        outreach_ready_at = CASE WHEN %s THEN %s ELSE NULL END,
                        updated_at = NOW()
                    WHERE unique_id = ANY(%s)
                """, (
                    is_valid,
                    result.verified_at,
                    is_message_ready,
                    is_message_ready,
                    result.verified_at,
                    person_ids
                ))
                self.conn.commit()
                return cur.rowcount
            except Exception as e:
                if attempt < 2:
                    self.reconnect()
                else:
                    raise e

        return 0

    async def run(self, limit: int = None, export: bool = False):
        """Main verification pipeline"""

        print("=" * 70)
        print("SLOT EMAIL VERIFICATION PIPELINE (DEDUPLICATED)")
        print("=" * 70)
        print(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE'}")
        print(f"Time: {datetime.now().isoformat()}")
        print()

        # Check API key
        if not self.api_key:
            print("ERROR: MILLIONVERIFIER_API_KEY not found")
            return

        print(f"API Key: {self.api_key[:8]}...{self.api_key[-4:]}")

        # Connect to database
        print("\nConnecting to database...")
        self.connect()
        print("Connected!")

        # Get slot emails
        print("\nFetching filled slot emails...")
        emails = self.get_slot_emails()

        self.stats.unique_emails = len(emails)

        # Split into already verified vs needs verification
        to_verify = {k: v for k, v in emails.items() if not v['already_verified']}
        already_done = {k: v for k, v in emails.items() if v['already_verified']}

        self.stats.already_verified = len(already_done)
        self.stats.to_verify = len(to_verify)

        print(f"\nEmail Summary:")
        print(f"  Total unique emails: {self.stats.unique_emails:,}")
        print(f"  Already verified:    {self.stats.already_verified:,}")
        print(f"  Need verification:   {self.stats.to_verify:,}")

        if limit:
            to_verify = dict(list(to_verify.items())[:limit])
            print(f"  Limited to:          {len(to_verify):,}")

        # Cost estimate
        cost = len(to_verify) * 0.001
        print(f"\nEstimated cost: ${cost:,.2f} ({len(to_verify):,} credits)")

        if self.dry_run:
            print("\n[DRY RUN] Would verify these emails:")
            for i, (email, data) in enumerate(list(to_verify.items())[:20]):
                slots = ', '.join(data['slot_types'])
                people_count = len(data['person_ids'])
                print(f"  {email[:40]:40} | {slots:15} | {people_count} people")
            if len(to_verify) > 20:
                print(f"  ... and {len(to_verify) - 20:,} more")
            return

        if not to_verify:
            print("\nNo emails need verification!")
            return

        # Verify emails
        print("\n" + "-" * 70)
        print("VERIFYING EMAILS")
        print("-" * 70)

        results_for_export = []

        for i, (email_key, data) in enumerate(to_verify.items(), 1):
            email = data['email']
            person_ids = data['person_ids']
            slot_types = data['slot_types']

            print(f"\n[{i:,}/{len(to_verify):,}] {email}")
            print(f"    Slots: {', '.join(slot_types)} | People: {len(person_ids)}")
            sys.stdout.flush()

            # Call API with retry
            print(f"    Verifying...", end=" ")
            sys.stdout.flush()

            result = None
            for attempt in range(3):
                try:
                    result = await self.verify_single_email(email)
                    break
                except Exception as e:
                    if attempt < 2:
                        print(f"[retry {attempt+1}]", end=" ")
                        await asyncio.sleep(1)
                    else:
                        print(f"[FAILED: {e}]")

            if not result:
                print("[API ERROR]")
                self.stats.api_errors += 1
                continue

            self.stats.credits_used += 1

            # Track result
            if result.status == 'VALID':
                print(f"[VALID] {result.result} -> MESSAGE READY")
                self.stats.verified_valid += 1
                self.stats.message_ready += len(person_ids)  # All people with this email are message-ready
            elif result.status == 'RISKY':
                print(f"[RISKY] {result.result} - {result.subresult}")
                self.stats.verified_risky += 1
            else:
                print(f"[INVALID] {result.result} - {result.subresult}")
                self.stats.verified_invalid += 1
                # Track slots that need more work - with full company details
                for outreach_id, domain, slot_type in data['slot_details']:
                    self.stats.invalid_slots.append(InvalidSlotRecord(
                        outreach_id=outreach_id,
                        domain=domain,
                        slot_type=slot_type,
                        email=email,
                        result=result.result,
                        subresult=result.subresult,
                    ))

            # Update database
            print(f"    Updating {len(person_ids)} people...", end=" ")
            updated = self.update_people_records(email, result, person_ids)
            print(f"[{updated} updated]")
            self.stats.people_updated += updated

            # Store for export
            results_for_export.append({
                'email': email,
                'result': result.result,
                'status': result.status,
                'subresult': result.subresult,
                'quality': result.quality,
                'slot_types': ','.join(slot_types),
                'people_count': len(person_ids),
                'verified_at': result.verified_at.isoformat(),
            })

            # Cache result
            self.verified_cache[email_key] = result

            # Rate limit (be nice to API)
            await asyncio.sleep(0.05)

            # Keep DB connection alive every 100 emails
            if i % 100 == 0:
                self.ping_db()
                # Flush stdout for background processes
                sys.stdout.flush()

        # Export if requested
        if export:
            os.makedirs('exports', exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            # Export all verification results
            if results_for_export:
                export_path = f"exports/email_verification_{timestamp}.csv"
                with open(export_path, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=results_for_export[0].keys())
                    writer.writeheader()
                    writer.writerows(results_for_export)
                print(f"\nExported all results to: {export_path}")

            # Export invalid slots that need new contacts
            if self.stats.invalid_slots:
                invalid_path = f"exports/slots_needing_contacts_{timestamp}.csv"
                with open(invalid_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['outreach_id', 'domain', 'slot_type', 'invalid_email', 'result', 'subresult'])
                    for slot in self.stats.invalid_slots:
                        writer.writerow([
                            slot.outreach_id,
                            slot.domain,
                            slot.slot_type,
                            slot.email,
                            slot.result,
                            slot.subresult,
                        ])
                print(f"Exported slots needing contacts to: {invalid_path}")

        # Summary
        print("\n" + "=" * 70)
        print("VERIFICATION COMPLETE")
        print("=" * 70)
        print(f"\nResults:")
        print(f"  Emails verified:    {self.stats.credits_used:,}")
        print(f"  Credits used:       {self.stats.credits_used:,} (1 per unique email)")
        print(f"  Actual cost:        ${self.stats.credits_used * 0.001:,.2f}")
        print()
        print(f"  VALID:              {self.stats.verified_valid:,}")
        print(f"  RISKY:              {self.stats.verified_risky:,}")
        print(f"  INVALID:            {self.stats.verified_invalid:,}")
        print(f"  API Errors:         {self.stats.api_errors:,}")
        print()
        print(f"  People updated:     {self.stats.people_updated:,}")
        print(f"  MESSAGE READY:      {self.stats.message_ready:,} (outreach_ready = TRUE)")

        if self.stats.verified_valid + self.stats.verified_risky > 0:
            total = self.stats.verified_valid + self.stats.verified_risky + self.stats.verified_invalid
            valid_rate = (self.stats.verified_valid + self.stats.verified_risky) / total * 100
            print(f"\n  Deliverable rate:   {valid_rate:.1f}%")

        # Show slots needing more work
        if self.stats.invalid_slots:
            print("\n" + "-" * 70)
            print("SLOTS NEEDING NEW CONTACTS (Invalid emails)")
            print("-" * 70)

            # Group by slot type
            by_slot = defaultdict(list)
            for slot in self.stats.invalid_slots:
                by_slot[slot.slot_type].append(slot)

            for slot_type in sorted(by_slot.keys()):
                slots = by_slot[slot_type]
                unique_companies = len(set(s.outreach_id for s in slots))
                print(f"\n  {slot_type}: {unique_companies:,} companies need new contacts")

                # Show first 5 examples
                seen = set()
                for slot in slots[:10]:
                    if slot.outreach_id not in seen:
                        seen.add(slot.outreach_id)
                        print(f"    - {slot.domain:40} | {slot.email[:30]:30} | {slot.result}")
                        if len(seen) >= 5:
                            break

                if unique_companies > 5:
                    print(f"    ... and {unique_companies - 5} more")

            print(f"\n  Total slots needing new contacts: {len(self.stats.invalid_slots):,}")

        self.conn.close()


def main():
    parser = argparse.ArgumentParser(
        description='Verify slot emails via Million Verifier (deduplicated)'
    )
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be done without API calls')
    parser.add_argument('--limit', type=int,
                        help='Only verify N emails (for testing)')
    parser.add_argument('--export', action='store_true',
                        help='Export results to CSV')

    args = parser.parse_args()

    verifier = SlotEmailVerifier(dry_run=args.dry_run)
    asyncio.run(verifier.run(limit=args.limit, export=args.export))


if __name__ == "__main__":
    main()
