#!/usr/bin/env python3
"""
Email Generation & Verification Pipeline
=========================================
Generates emails for people slots using company patterns,
then verifies them with Million Verifier API.

Usage:
    doppler run -- python hubs/people-intelligence/scripts/generate_and_verify_emails.py

    Options:
        --dry-run       Show what would happen without making changes
        --limit N       Only process N records (for testing)
        --generate-only Only generate emails, skip verification
        --verify-only   Only verify existing emails, skip generation

Requires:
    MILLIONVERIFIER_API_KEY in Doppler secrets

Cost:
    ~$0.0037/email (99,903 credits = ~27K verifications)
"""

import os
import sys
import asyncio
import argparse
import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

import psycopg2
import aiohttp


# MillionVerifier result codes
MV_RESULT_CODES = {
    'ok': {'valid': True, 'description': 'Valid email'},
    'catch_all': {'valid': True, 'description': 'Catch-all domain'},
    'unknown': {'valid': False, 'description': 'Unable to verify'},
    'invalid': {'valid': False, 'description': 'Invalid email'},
    'disposable': {'valid': False, 'description': 'Disposable email'},
    'role': {'valid': True, 'description': 'Role-based email'},
    'risky': {'valid': True, 'description': 'Risky but deliverable'},
}

# Rate limiting
BATCH_SIZE = 50
BATCH_DELAY = 0.5  # seconds between batches


class EmailPipeline:
    """Generates and verifies emails for people slots."""

    def __init__(self, api_key: Optional[str] = None, dry_run: bool = False):
        self.api_key = api_key or os.getenv('MILLIONVERIFIER_API_KEY')
        self.dry_run = dry_run
        self.conn = None
        self.stats = {
            'slots_processed': 0,
            'emails_generated': 0,
            'emails_verified': 0,
            'valid': 0,
            'invalid': 0,
            'catch_all': 0,
            'errors': 0,
        }

    def connect_db(self):
        """Connect to Neon PostgreSQL."""
        self.conn = psycopg2.connect(
            host=os.environ['NEON_HOST'],
            database=os.environ['NEON_DATABASE'],
            user=os.environ['NEON_USER'],
            password=os.environ['NEON_PASSWORD'],
            sslmode='require'
        )
        self.conn.autocommit = True
        return self.conn

    def generate_email(self, pattern: str, first_name: str, last_name: str) -> Optional[str]:
        """Generate email from pattern and name."""
        if not pattern or not first_name or not last_name:
            return None

        # Clean names
        first = first_name.lower().strip()
        last = last_name.lower().strip()

        # Remove special characters
        first = re.sub(r'[^a-z]', '', first)
        last = re.sub(r'[^a-z]', '', last)

        if not first or not last:
            return None

        # Apply pattern
        email = pattern.lower()
        email = email.replace('{first}', first)
        email = email.replace('{last}', last)
        email = email.replace('{f}', first[0] if first else '')
        email = email.replace('{l}', last[0] if last else '')

        return email

    def get_slots_for_generation(self, limit: Optional[int] = None) -> List[Dict]:
        """Get slots that need email generation."""
        cur = self.conn.cursor()

        query = '''
            SELECT
                cs.slot_id,
                cs.person_unique_id,
                pm.full_name,
                pm.first_name,
                pm.last_name,
                ct.email_method,
                cs.company_unique_id
            FROM people.company_slot cs
            JOIN people.people_master pm ON cs.person_unique_id = pm.unique_id
            JOIN outreach.company_target ct ON cs.company_unique_id = ct.company_unique_id
            WHERE cs.is_filled = true
            AND ct.email_method IS NOT NULL
            AND (pm.email IS NULL OR pm.email = '')
            AND pm.full_name IS NOT NULL AND pm.full_name <> ''
        '''

        if limit:
            query += f' LIMIT {limit}'

        cur.execute(query)
        rows = cur.fetchall()

        return [
            {
                'slot_id': row[0],
                'person_unique_id': row[1],
                'full_name': row[2],
                'first_name': row[3],
                'last_name': row[4],
                'email_pattern': row[5],
                'company_unique_id': row[6]
            }
            for row in rows
        ]

    def get_emails_for_verification(self, limit: Optional[int] = None) -> List[Dict]:
        """Get existing emails that need verification."""
        cur = self.conn.cursor()

        query = '''
            SELECT unique_id, email, email_verified_at
            FROM people.people_master
            WHERE email IS NOT NULL AND email <> ''
            AND email_verified_at IS NULL
        '''

        if limit:
            query += f' LIMIT {limit}'

        cur.execute(query)
        rows = cur.fetchall()

        return [
            {
                'person_unique_id': row[0],
                'email': row[1],
                'email_verified_at': row[2]
            }
            for row in rows
        ]

    async def verify_email(self, email: str) -> Dict[str, Any]:
        """Verify email with Million Verifier API."""
        if not self.api_key:
            return {'valid': None, 'result_code': 'no_api_key', 'error': 'No API key'}

        url = f"https://api.millionverifier.com/api/v3/?api={self.api_key}&email={email}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        data = await response.json()
                        result_code = data.get('result', 'unknown')

                        # Check for errors
                        if data.get('error'):
                            return {
                                'valid': None,
                                'result_code': 'api_error',
                                'error': data.get('error'),
                                'credits': data.get('credits', 0)
                            }

                        result_info = MV_RESULT_CODES.get(result_code, {'valid': False})

                        return {
                            'valid': result_info['valid'],
                            'result_code': result_code,
                            'quality': data.get('quality', 0),
                            'free': data.get('free', False),
                            'credits': data.get('credits', 0)
                        }
                    else:
                        return {'valid': None, 'result_code': 'http_error', 'error': f"HTTP {response.status}"}
        except asyncio.TimeoutError:
            return {'valid': None, 'result_code': 'timeout', 'error': 'Request timeout'}
        except Exception as e:
            return {'valid': None, 'result_code': 'error', 'error': str(e)}

    def update_people_master_email(self, person_unique_id: str, email: str, verified: bool, result_code: str):
        """Update people_master with generated/verified email."""
        cur = self.conn.cursor()

        cur.execute('''
            UPDATE people.people_master
            SET email = %s,
                email_verified = %s,
                email_verified_at = %s,
                email_verification_source = %s,
                updated_at = NOW()
            WHERE unique_id = %s
        ''', (email, verified, datetime.now(), f'millionverifier:{result_code}', person_unique_id))

    def update_email_verification(self, person_unique_id: str, verified: bool, result_code: str):
        """Update verification status for existing email."""
        cur = self.conn.cursor()

        cur.execute('''
            UPDATE people.people_master
            SET email_verified = %s,
                email_verified_at = %s,
                email_verification_source = %s,
                updated_at = NOW()
            WHERE unique_id = %s
        ''', (verified, datetime.now(), f'millionverifier:{result_code}', person_unique_id))

    async def run_pipeline(self, limit: Optional[int] = None,
                          generate_only: bool = False,
                          verify_only: bool = False):
        """Run the full email generation and verification pipeline."""
        print("=" * 70)
        print("Email Generation & Verification Pipeline")
        print("=" * 70)

        # Check API key
        if not self.api_key:
            print("\n[ERROR] MILLIONVERIFIER_API_KEY not found!")
            print("   Add it to Doppler: doppler secrets set MILLIONVERIFIER_API_KEY=<key>")
            return

        print(f"\n[OK] API Key: {self.api_key[:8]}...")
        if self.dry_run:
            print("[DRY RUN] No changes will be made")

        # Connect
        print("\n[DB] Connecting to Neon PostgreSQL...")
        self.connect_db()
        print("[DB] Connected!")

        # Phase 1: Generate emails for slots
        if not verify_only:
            print("\n" + "=" * 70)
            print("PHASE 1: Email Generation")
            print("=" * 70)

            slots = self.get_slots_for_generation(limit=limit)
            print(f"[INFO] Found {len(slots):,} slots needing email generation")

            if slots:
                generated_emails = []

                for slot in slots:
                    email = self.generate_email(
                        slot['email_pattern'],
                        slot['first_name'],
                        slot['last_name']
                    )

                    if email:
                        generated_emails.append({
                            'person_unique_id': slot['person_unique_id'],
                            'email': email,
                            'full_name': slot['full_name']
                        })
                        self.stats['emails_generated'] += 1

                print(f"[INFO] Generated {len(generated_emails):,} emails")

                if self.dry_run:
                    print("\n[DRY RUN] Sample generated emails:")
                    for item in generated_emails[:10]:
                        print(f"   {item['full_name']}: {item['email']}")
                else:
                    # Verify generated emails
                    print("\n[VERIFY] Verifying generated emails...")
                    await self._verify_batch(generated_emails, update_with_email=True)

        # Phase 2: Verify existing emails
        if not generate_only:
            print("\n" + "=" * 70)
            print("PHASE 2: Verify Existing Emails")
            print("=" * 70)

            existing = self.get_emails_for_verification(limit=limit)
            print(f"[INFO] Found {len(existing):,} existing emails to verify")

            if existing and not self.dry_run:
                await self._verify_batch(existing, update_with_email=False)
            elif self.dry_run and existing:
                print("\n[DRY RUN] Sample existing emails to verify:")
                for item in existing[:10]:
                    print(f"   {item['email']}")

        # Summary
        print("\n" + "=" * 70)
        print("Pipeline Complete!")
        print("=" * 70)
        print(f"  Emails generated:    {self.stats['emails_generated']:,}")
        print(f"  Emails verified:     {self.stats['emails_verified']:,}")
        print(f"  Valid:               {self.stats['valid']:,}")
        print(f"  Invalid:             {self.stats['invalid']:,}")
        print(f"  Catch-all:           {self.stats['catch_all']:,}")
        print(f"  Errors:              {self.stats['errors']:,}")

        if self.stats['emails_verified'] > 0:
            valid_rate = self.stats['valid'] / self.stats['emails_verified'] * 100
            print(f"  Valid rate:          {valid_rate:.1f}%")

        if self.conn:
            self.conn.close()

    async def _verify_batch(self, items: List[Dict], update_with_email: bool = False):
        """Verify a batch of emails."""
        total = len(items)

        for i, item in enumerate(items, 1):
            email = item['email']
            person_id = str(item['person_unique_id'])

            print(f"  [{i}/{total}] {email}...", end=" ", flush=True)

            result = await self.verify_email(email)

            if result.get('valid') is None:
                error = result.get('error', 'Unknown error')
                if 'Insufficient credits' in str(error):
                    print(f"[OUT OF CREDITS] Stopping...")
                    self.stats['errors'] += 1
                    return
                print(f"[ERROR] {error}")
                self.stats['errors'] += 1
                continue

            is_valid = result['valid']
            result_code = result['result_code']
            self.stats['emails_verified'] += 1

            if is_valid:
                self.stats['valid'] += 1
                if result_code == 'catch_all':
                    self.stats['catch_all'] += 1
                    print(f"[CATCH-ALL] {result_code}")
                else:
                    print(f"[VALID] {result_code}")
            else:
                self.stats['invalid'] += 1
                print(f"[INVALID] {result_code}")

            # Update database
            if update_with_email:
                self.update_people_master_email(person_id, email, is_valid, result_code)
            else:
                self.update_email_verification(person_id, is_valid, result_code)

            # Rate limit
            if i % BATCH_SIZE == 0:
                await asyncio.sleep(BATCH_DELAY)
            else:
                await asyncio.sleep(0.05)  # Small delay between requests


def main():
    parser = argparse.ArgumentParser(description='Generate and verify emails for people slots')
    parser.add_argument('--dry-run', action='store_true', help='Show what would happen')
    parser.add_argument('--limit', type=int, help='Only process N records')
    parser.add_argument('--generate-only', action='store_true', help='Only generate, skip verification')
    parser.add_argument('--verify-only', action='store_true', help='Only verify existing emails')

    args = parser.parse_args()

    pipeline = EmailPipeline(dry_run=args.dry_run)
    asyncio.run(pipeline.run_pipeline(
        limit=args.limit,
        generate_only=args.generate_only,
        verify_only=args.verify_only
    ))


if __name__ == "__main__":
    main()
