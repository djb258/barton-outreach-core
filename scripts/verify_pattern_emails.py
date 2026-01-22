#!/usr/bin/env python3
"""
Verify Pattern-Generated Emails
================================
Verifies emails in people.people_master that were generated from company patterns
using the MillionVerifier API.

Features:
- Credit throttling to prevent budget overrun
- Configurable daily/session limits
- Tracks verification progress
- Can be safely stopped and resumed

Usage:
    doppler run -- python scripts/verify_pattern_emails.py --limit 1000
    doppler run -- python scripts/verify_pattern_emails.py --dry-run
    doppler run -- python scripts/verify_pattern_emails.py --budget 50.00

Cost:
    ~$0.0037/email (MillionVerifier single API)
    ~$37/10,000 emails

Requires:
    MILLIONVERIFIER_API_KEY in Doppler secrets
"""

import os
import sys
import argparse
import asyncio
import aiohttp
import psycopg2
from datetime import datetime, timezone, date
from typing import Optional, Dict, List, Any

# MillionVerifier API
MV_API_URL = "https://api.millionverifier.com/api/v3/"
COST_PER_EMAIL = 0.0037  # Approximate cost per verification

# Default throttle settings
DEFAULT_MAX_CREDITS = 1000  # Max emails per run
DEFAULT_DAILY_LIMIT = 5000  # Max emails per day
DEFAULT_BATCH_SIZE = 100    # Emails per batch
BATCH_DELAY = 0.5           # Seconds between batches

# Result codes
VALID_RESULTS = {'ok', 'catch_all', 'role', 'risky'}
INVALID_RESULTS = {'invalid', 'disposable', 'unknown'}


class CreditTracker:
    """Tracks API credit usage with throttling."""

    def __init__(self, conn, max_per_run: int = DEFAULT_MAX_CREDITS,
                 daily_limit: int = DEFAULT_DAILY_LIMIT):
        self.conn = conn
        self.max_per_run = max_per_run
        self.daily_limit = daily_limit
        self.used_this_run = 0
        self._ensure_tracking_table()

    def _ensure_tracking_table(self):
        """Create credit tracking table if it doesn't exist."""
        cur = self.conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS outreach.mv_credit_usage (
                id SERIAL PRIMARY KEY,
                usage_date DATE NOT NULL,
                credits_used INTEGER NOT NULL DEFAULT 0,
                cost_estimate NUMERIC(10,4) DEFAULT 0,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE(usage_date)
            )
        """)
        self.conn.commit()

    def get_daily_usage(self) -> int:
        """Get credits used today."""
        cur = self.conn.cursor()
        cur.execute("""
            SELECT COALESCE(credits_used, 0)
            FROM outreach.mv_credit_usage
            WHERE usage_date = CURRENT_DATE
        """)
        result = cur.fetchone()
        return result[0] if result else 0

    def get_remaining_daily(self) -> int:
        """Get remaining credits for today."""
        used = self.get_daily_usage()
        return max(0, self.daily_limit - used)

    def get_remaining_run(self) -> int:
        """Get remaining credits for this run."""
        return max(0, self.max_per_run - self.used_this_run)

    def can_use(self, count: int = 1) -> bool:
        """Check if we can use more credits."""
        if self.used_this_run + count > self.max_per_run:
            return False
        if self.get_daily_usage() + count > self.daily_limit:
            return False
        return True

    def use(self, count: int = 1):
        """Record credit usage."""
        self.used_this_run += count

        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO outreach.mv_credit_usage (usage_date, credits_used, cost_estimate)
            VALUES (CURRENT_DATE, %s, %s)
            ON CONFLICT (usage_date)
            DO UPDATE SET
                credits_used = outreach.mv_credit_usage.credits_used + EXCLUDED.credits_used,
                cost_estimate = outreach.mv_credit_usage.cost_estimate + EXCLUDED.cost_estimate,
                updated_at = NOW()
        """, (count, count * COST_PER_EMAIL))
        self.conn.commit()

    def get_stats(self) -> Dict:
        """Get current usage stats."""
        return {
            'used_this_run': self.used_this_run,
            'max_per_run': self.max_per_run,
            'daily_used': self.get_daily_usage(),
            'daily_limit': self.daily_limit,
            'remaining_run': self.get_remaining_run(),
            'remaining_daily': self.get_remaining_daily(),
            'cost_this_run': self.used_this_run * COST_PER_EMAIL,
        }


def connect_db():
    """Connect to Neon PostgreSQL."""
    return psycopg2.connect(
        host=os.environ['NEON_HOST'],
        database=os.environ['NEON_DATABASE'],
        user=os.environ['NEON_USER'],
        password=os.environ['NEON_PASSWORD'],
        sslmode='require'
    )


def get_unverified_pattern_emails(conn, limit: int) -> List[Dict]:
    """Get pattern-generated emails that need verification."""
    cur = conn.cursor()
    cur.execute("""
        SELECT unique_id, email, first_name, last_name
        FROM people.people_master
        WHERE email_verification_source = 'pattern_generated'
        AND (email_verified = false OR email_verified IS NULL)
        AND email IS NOT NULL
        ORDER BY updated_at ASC
        LIMIT %s
    """, (limit,))

    return [
        {'unique_id': row[0], 'email': row[1], 'first_name': row[2], 'last_name': row[3]}
        for row in cur.fetchall()
    ]


async def verify_email(session: aiohttp.ClientSession, email: str, api_key: str) -> Dict[str, Any]:
    """Verify a single email using MillionVerifier API."""
    url = f"{MV_API_URL}?api={api_key}&email={email}"

    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
            if response.status == 200:
                data = await response.json()
                result_code = data.get('result', 'unknown').lower()

                return {
                    'success': True,
                    'email': email,
                    'result': result_code,
                    'is_valid': result_code in VALID_RESULTS,
                    'is_catch_all': result_code == 'catch_all',
                    'quality': data.get('quality', 0),
                    'credits': data.get('credits', 1),
                }
            else:
                return {'success': False, 'email': email, 'error': f'HTTP {response.status}'}
    except asyncio.TimeoutError:
        return {'success': False, 'email': email, 'error': 'timeout'}
    except Exception as e:
        return {'success': False, 'email': email, 'error': str(e)}


def update_verification_result(conn, unique_id: str, result: Dict):
    """Update people_master with verification result."""
    cur = conn.cursor()

    is_valid = result.get('is_valid', False)
    result_code = result.get('result', 'error')

    # Determine verification source based on result
    if is_valid:
        source = 'mv_verified'
    elif result_code == 'catch_all':
        source = 'mv_catch_all'
    elif result_code in INVALID_RESULTS:
        source = 'mv_invalid'
    else:
        source = 'mv_unknown'

    cur.execute("""
        UPDATE people.people_master
        SET email_verified = %s,
            email_verified_at = %s,
            email_verification_source = %s,
            updated_at = NOW()
        WHERE unique_id = %s
    """, (is_valid, datetime.now(timezone.utc), source, unique_id))

    conn.commit()


async def run_verification(
    api_key: str,
    max_credits: int = DEFAULT_MAX_CREDITS,
    daily_limit: int = DEFAULT_DAILY_LIMIT,
    dry_run: bool = False
):
    """Main verification runner with throttling."""

    print("=" * 80)
    print("PATTERN EMAIL VERIFICATION (MillionVerifier)")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print("=" * 80)

    # Connect to database
    conn = connect_db()

    # Initialize credit tracker
    tracker = CreditTracker(conn, max_per_run=max_credits, daily_limit=daily_limit)

    # Show credit status
    print("\n[1] CREDIT STATUS")
    print("-" * 50)
    stats = tracker.get_stats()
    print(f"  Daily limit: {stats['daily_limit']:,}")
    print(f"  Daily used: {stats['daily_used']:,}")
    print(f"  Daily remaining: {stats['remaining_daily']:,}")
    print(f"  Run limit: {stats['max_per_run']:,}")

    if stats['remaining_daily'] == 0:
        print("\n  [THROTTLED] Daily limit reached. Try again tomorrow.")
        conn.close()
        return

    # Get emails to verify (limited by available credits)
    available = min(stats['remaining_daily'], stats['max_per_run'])
    print(f"\n[2] FETCHING EMAILS (max {available:,})")
    print("-" * 50)

    emails = get_unverified_pattern_emails(conn, available)
    print(f"  Emails to verify: {len(emails):,}")

    if not emails:
        print("  No unverified pattern-generated emails found.")
        conn.close()
        return

    # Cost estimate
    estimated_cost = len(emails) * COST_PER_EMAIL
    print(f"  Estimated cost: ${estimated_cost:.2f}")

    if dry_run:
        print("\n  [DRY RUN] Sample emails:")
        for e in emails[:10]:
            print(f"    {e['email']}")
        if len(emails) > 10:
            print(f"    ... and {len(emails) - 10} more")
        conn.close()
        return

    # Verify emails
    print(f"\n[3] VERIFYING EMAILS")
    print("-" * 50)

    verified = 0
    valid = 0
    invalid = 0
    catch_all = 0
    errors = 0

    async with aiohttp.ClientSession() as session:
        for i in range(0, len(emails), DEFAULT_BATCH_SIZE):
            # Check if we can continue
            if not tracker.can_use(1):
                print(f"\n  [THROTTLED] Credit limit reached. Stopping.")
                break

            batch = emails[i:i + DEFAULT_BATCH_SIZE]
            batch_verified = 0

            for email_data in batch:
                if not tracker.can_use(1):
                    break

                result = await verify_email(session, email_data['email'], api_key)

                if result['success']:
                    tracker.use(1)
                    update_verification_result(conn, email_data['unique_id'], result)
                    verified += 1
                    batch_verified += 1

                    if result['is_valid']:
                        valid += 1
                    elif result.get('result') == 'catch_all':
                        catch_all += 1
                    else:
                        invalid += 1
                else:
                    errors += 1

                # Small delay between requests
                await asyncio.sleep(0.1)

            # Progress update
            progress = min(i + DEFAULT_BATCH_SIZE, len(emails))
            print(f"  Progress: {progress:,} / {len(emails):,} ({batch_verified} verified this batch)")

            # Batch delay
            if i + DEFAULT_BATCH_SIZE < len(emails):
                await asyncio.sleep(BATCH_DELAY)

    # Final stats
    print(f"\n[4] VERIFICATION COMPLETE")
    print("-" * 50)
    print(f"  Verified: {verified:,}")
    print(f"  Valid: {valid:,}")
    print(f"  Catch-all: {catch_all:,}")
    print(f"  Invalid: {invalid:,}")
    print(f"  Errors: {errors:,}")

    if verified > 0:
        valid_rate = valid / verified * 100
        print(f"  Valid rate: {valid_rate:.1f}%")

    # Credit summary
    print(f"\n[5] CREDIT USAGE")
    print("-" * 50)
    final_stats = tracker.get_stats()
    print(f"  Credits used this run: {final_stats['used_this_run']:,}")
    print(f"  Cost this run: ${final_stats['cost_this_run']:.2f}")
    print(f"  Daily total: {final_stats['daily_used']:,}")
    print(f"  Daily remaining: {final_stats['remaining_daily']:,}")

    # Check remaining unverified
    remaining = get_unverified_pattern_emails(conn, 1)
    if remaining:
        cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*) FROM people.people_master
            WHERE email_verification_source = 'pattern_generated'
            AND (email_verified = false OR email_verified IS NULL)
        """)
        remaining_count = cur.fetchone()[0]
        print(f"\n  Remaining unverified: {remaining_count:,}")
        print(f"  Run again to continue verification.")
    else:
        print(f"\n  All pattern-generated emails verified!")

    conn.close()


def main():
    parser = argparse.ArgumentParser(description='Verify pattern-generated emails with throttling')
    parser.add_argument('--dry-run', action='store_true', help='Preview without API calls')
    parser.add_argument('--limit', type=int, default=DEFAULT_MAX_CREDITS,
                        help=f'Max emails this run (default: {DEFAULT_MAX_CREDITS})')
    parser.add_argument('--daily-limit', type=int, default=DEFAULT_DAILY_LIMIT,
                        help=f'Max emails per day (default: {DEFAULT_DAILY_LIMIT})')
    parser.add_argument('--budget', type=float, help='Max spend in dollars (overrides --limit)')

    args = parser.parse_args()

    # Get API key
    api_key = os.environ.get('MILLIONVERIFIER_API_KEY')
    if not api_key:
        print("[ERROR] MILLIONVERIFIER_API_KEY not found in environment")
        print("  Add it to Doppler: doppler secrets set MILLIONVERIFIER_API_KEY=<key>")
        sys.exit(1)

    # Calculate limit from budget if provided
    max_credits = args.limit
    if args.budget:
        max_credits = int(args.budget / COST_PER_EMAIL)
        print(f"[INFO] Budget ${args.budget:.2f} = ~{max_credits:,} emails")

    # Run verification
    asyncio.run(run_verification(
        api_key=api_key,
        max_credits=max_credits,
        daily_limit=args.daily_limit,
        dry_run=args.dry_run
    ))


if __name__ == "__main__":
    main()
