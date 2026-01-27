#!/usr/bin/env python3
"""
People Email Verification Runner
================================
Verifies emails in outreach.people table using MillionVerifier API.

Usage:
    doppler run -- python hubs/people-intelligence/scripts/verify_people_emails.py

    Options:
        --dry-run       Show what would be verified without API calls
        --limit N       Only verify N emails (for testing)
        --re-verify     Re-verify all emails, even if already marked verified

Requires:
    MILLIONVERIFIER_API_KEY in Doppler secrets

Cost:
    ~$37/10,000 verifications (batch rate)
    ~$0.001/email (real-time)
"""

import os
import sys
import asyncio
import argparse
from datetime import datetime
from typing import List, Dict, Any, Optional

import psycopg2
import aiohttp


# MillionVerifier result codes
MV_RESULT_CODES = {
    'ok': {'valid': True, 'deliverable': True, 'description': 'Valid email'},
    'catch_all': {'valid': True, 'deliverable': True, 'description': 'Catch-all domain (risky)'},
    'unknown': {'valid': False, 'deliverable': False, 'description': 'Unable to verify'},
    'invalid': {'valid': False, 'deliverable': False, 'description': 'Invalid email'},
    'disposable': {'valid': False, 'deliverable': False, 'description': 'Disposable email'},
    'role': {'valid': True, 'deliverable': True, 'description': 'Role-based email (info@, support@)'},
    'risky': {'valid': True, 'deliverable': True, 'description': 'Risky but deliverable'},
}


class PeopleEmailVerifier:
    """Verifies emails in outreach.people using MillionVerifier API."""

    def __init__(self, api_key: Optional[str] = None, dry_run: bool = False):
        self.api_key = api_key or os.getenv('MILLIONVERIFIER_API_KEY')
        self.dry_run = dry_run
        self.conn = None
        self.stats = {
            'total': 0,
            'verified': 0,
            'valid': 0,
            'invalid': 0,
            'errors': 0,
            'skipped': 0,
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
        return self.conn

    def get_emails_to_verify(self, limit: Optional[int] = None, re_verify: bool = False) -> List[Dict]:
        """Get emails from people table that need verification."""
        cur = self.conn.cursor()

        if re_verify:
            # Re-verify all emails (useful for API verification of imported emails)
            query = """
                SELECT person_id, email, email_verified, email_verified_at
                FROM outreach.people
                WHERE email IS NOT NULL AND email != ''
                ORDER BY created_at DESC
            """
        else:
            # Only verify emails not yet verified or without timestamp
            query = """
                SELECT person_id, email, email_verified, email_verified_at
                FROM outreach.people
                WHERE email IS NOT NULL AND email != ''
                AND (email_verified = false OR email_verified_at IS NULL)
                ORDER BY created_at DESC
            """

        if limit:
            query += f" LIMIT {limit}"

        cur.execute(query)
        rows = cur.fetchall()

        return [
            {
                'person_id': row[0],
                'email': row[1],
                'email_verified': row[2],
                'email_verified_at': row[3]
            }
            for row in rows
        ]

    async def verify_email(self, email: str) -> Dict[str, Any]:
        """Verify a single email using MillionVerifier API."""
        if not self.api_key:
            return {
                'valid': None,
                'result_code': 'no_api_key',
                'error': 'MILLIONVERIFIER_API_KEY not configured'
            }

        url = f"https://api.millionverifier.com/api/v3/?api={self.api_key}&email={email}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        data = await response.json()
                        result_code = data.get('result', 'unknown')
                        result_info = MV_RESULT_CODES.get(result_code, {'valid': False, 'deliverable': False})

                        return {
                            'valid': result_info['valid'],
                            'deliverable': result_info['deliverable'],
                            'result_code': result_code,
                            'subresult': data.get('subresult'),
                            'quality': data.get('quality', 0),
                            'free': data.get('free', False),
                            'role': data.get('role', False),
                            'credits': data.get('credits', 1)
                        }
                    else:
                        return {
                            'valid': None,
                            'result_code': 'api_error',
                            'error': f"HTTP {response.status}"
                        }
        except asyncio.TimeoutError:
            return {'valid': None, 'result_code': 'timeout', 'error': 'Request timeout'}
        except Exception as e:
            return {'valid': None, 'result_code': 'error', 'error': str(e)}

    def update_verification_status(self, person_id: str, is_valid: bool, result: Dict):
        """Update people table with verification result."""
        cur = self.conn.cursor()

        cur.execute("""
            UPDATE outreach.people
            SET email_verified = %s,
                email_verified_at = %s,
                updated_at = NOW()
            WHERE person_id = %s
        """, (is_valid, datetime.now(), person_id))

        self.conn.commit()

    async def run_verification(self, limit: Optional[int] = None, re_verify: bool = False):
        """Run email verification pipeline."""
        print("=" * 60)
        print("People Email Verification Runner")
        print("=" * 60)

        # Check API key
        if not self.api_key:
            print("\n[ERROR] MILLIONVERIFIER_API_KEY not found!")
            print("   Add it to Doppler:")
            print("   doppler secrets set MILLIONVERIFIER_API_KEY=<your-api-key>")
            print("\n   Get your API key at: https://www.millionverifier.com/")
            return

        print(f"\n[OK] API Key configured: {self.api_key[:8]}...")

        if self.dry_run:
            print("[DRY RUN] No API calls will be made")

        # Connect to database
        print("\n[DB] Connecting to Neon PostgreSQL...")
        self.connect_db()
        print("[DB] Connected!")

        # Get emails to verify
        print("\n[FETCH] Getting emails to verify...")
        emails = self.get_emails_to_verify(limit=limit, re_verify=re_verify)
        self.stats['total'] = len(emails)

        if not emails:
            print("[INFO] No emails to verify!")
            if not re_verify:
                print("   Use --re-verify to re-verify all emails")
            return

        print(f"[INFO] Found {len(emails)} emails to verify")

        if self.dry_run:
            print("\n[DRY RUN] Would verify these emails:")
            for email_data in emails[:10]:
                print(f"   {email_data['email']}")
            if len(emails) > 10:
                print(f"   ... and {len(emails) - 10} more")
            return

        # Verify emails
        print("\n[VERIFY] Starting verification...")
        for i, email_data in enumerate(emails, 1):
            email = email_data['email']
            person_id = str(email_data['person_id'])

            print(f"  [{i}/{len(emails)}] {email}...", end=" ", flush=True)

            result = await self.verify_email(email)

            if result.get('valid') is None:
                print(f"[ERROR] {result.get('error', 'Unknown error')}")
                self.stats['errors'] += 1
                continue

            is_valid = result['valid']
            result_code = result['result_code']

            # Update database
            self.update_verification_status(person_id, is_valid, result)
            self.stats['verified'] += 1

            if is_valid:
                self.stats['valid'] += 1
                print(f"[VALID] {result_code}")
            else:
                self.stats['invalid'] += 1
                print(f"[INVALID] {result_code}")

            # Small delay to respect rate limits
            await asyncio.sleep(0.1)

        # Print summary
        print("\n" + "=" * 60)
        print("Verification Complete!")
        print("=" * 60)
        print(f"  Total emails:     {self.stats['total']}")
        print(f"  Verified:         {self.stats['verified']}")
        print(f"  Valid:            {self.stats['valid']}")
        print(f"  Invalid:          {self.stats['invalid']}")
        print(f"  Errors:           {self.stats['errors']}")
        if self.stats['verified'] > 0:
            valid_rate = self.stats['valid'] / self.stats['verified'] * 100
            print(f"  Valid rate:       {valid_rate:.1f}%")

        # Close connection
        self.conn.close()


def main():
    parser = argparse.ArgumentParser(description='Verify emails in outreach.people table')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be verified')
    parser.add_argument('--limit', type=int, help='Only verify N emails')
    parser.add_argument('--re-verify', action='store_true', help='Re-verify all emails')

    args = parser.parse_args()

    verifier = PeopleEmailVerifier(dry_run=args.dry_run)
    asyncio.run(verifier.run_verification(limit=args.limit, re_verify=args.re_verify))


if __name__ == "__main__":
    main()
