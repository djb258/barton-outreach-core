#!/usr/bin/env python3
"""
People Slot Pipeline
====================
Integrated pipeline for:
1. Filling slots from available people data
2. Generating emails using company patterns
3. Verifying emails through MillionVerifier

All with credit throttling to control costs.

Usage:
    doppler run -- python scripts/people_slot_pipeline.py --step fill
    doppler run -- python scripts/people_slot_pipeline.py --step generate
    doppler run -- python scripts/people_slot_pipeline.py --step verify --limit 1000
    doppler run -- python scripts/people_slot_pipeline.py --all --verify-limit 500

Options:
    --step fill|generate|verify   Run single step
    --all                         Run entire pipeline
    --dry-run                     Preview without changes
    --verify-limit N              Max emails to verify (default: 1000)
    --daily-limit N               Max verifications per day (default: 5000)
    --budget N.NN                 Max spend in dollars
"""

import os
import sys
import argparse
import asyncio
import aiohttp
import psycopg2
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import re

# ============================================================================
# CONFIGURATION
# ============================================================================

COST_PER_VERIFICATION = 0.0037
DEFAULT_VERIFY_LIMIT = 1000
DEFAULT_DAILY_LIMIT = 5000

SLOT_PATTERNS = {
    'CEO': ['%ceo%', '%chief executive%', '%president%', '%owner%', '%founder%'],
    'CFO': ['%cfo%', '%chief financial%', '%finance director%', '%controller%'],
    'HR': ['%hr %', '%human resource%', '%people %', '%talent%', '%chro%']
}

VALID_RESULTS = {'ok', 'catch_all', 'role', 'risky'}


# ============================================================================
# DATABASE
# ============================================================================

def connect_db():
    return psycopg2.connect(
        host=os.environ['NEON_HOST'],
        database=os.environ['NEON_DATABASE'],
        user=os.environ['NEON_USER'],
        password=os.environ['NEON_PASSWORD'],
        sslmode='require'
    )


# ============================================================================
# STEP 1: FILL SLOTS
# ============================================================================

def fill_slots(conn, dry_run: bool = False) -> Dict[str, int]:
    """Fill unfilled slots from people_master using title matching."""
    cur = conn.cursor()
    results = {'CEO': 0, 'CFO': 0, 'HR': 0}

    print("\n[STEP 1] FILL SLOTS FROM PEOPLE_MASTER")
    print("-" * 50)

    for slot_type, patterns in SLOT_PATTERNS.items():
        pattern_sql = ' OR '.join([f"LOWER(pm.title) LIKE '{p}'" for p in patterns])

        # Find matches
        cur.execute(f"""
            SELECT cs.slot_id, pm.unique_id, pm.full_name, pm.title
            FROM people.company_slot cs
            JOIN outreach.outreach o ON o.outreach_id = cs.outreach_id
            JOIN cl.company_identity_bridge b ON b.company_sov_id = o.sovereign_id
            JOIN people.people_master pm ON pm.company_unique_id = b.source_company_id
            WHERE cs.slot_type = '{slot_type}'
            AND (cs.is_filled = false OR cs.is_filled IS NULL)
            AND pm.title IS NOT NULL
            AND ({pattern_sql})
            LIMIT 1000
        """)
        matches = cur.fetchall()

        if not matches:
            print(f"  {slot_type}: No matches found")
            continue

        print(f"  {slot_type}: Found {len(matches)} matches")

        if dry_run:
            continue

        # Fill slots
        filled = 0
        for slot_id, person_id, name, title in matches:
            cur.execute("""
                UPDATE people.company_slot
                SET person_unique_id = %s,
                    is_filled = true,
                    filled_at = NOW(),
                    source_system = 'pipeline_auto',
                    updated_at = NOW()
                WHERE slot_id = %s
                AND (is_filled = false OR is_filled IS NULL)
            """, (person_id, slot_id))
            filled += cur.rowcount

        conn.commit()
        results[slot_type] = filled
        print(f"  {slot_type}: Filled {filled} slots")

    return results


# ============================================================================
# STEP 2: GENERATE EMAILS
# ============================================================================

def clean_name(name: str) -> str:
    """Clean name for email generation."""
    if not name:
        return ""
    cleaned = name.lower()
    cleaned = re.sub(r'\s+(jr\.?|sr\.?|iii?|iv|phd|md|cpa|esq)\.?$', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'[^a-z]', '', cleaned)
    return cleaned


def generate_emails(conn, dry_run: bool = False) -> int:
    """Generate emails for people without them using company patterns."""
    cur = conn.cursor()

    print("\n[STEP 2] GENERATE EMAILS FROM PATTERNS")
    print("-" * 50)

    # Find candidates
    cur.execute("""
        SELECT pm.unique_id, pm.first_name, pm.last_name, o.domain, ct.method_type
        FROM people.people_master pm
        JOIN people.company_slot cs ON cs.person_unique_id = pm.unique_id
        JOIN outreach.company_target ct ON ct.outreach_id = cs.outreach_id
        JOIN outreach.outreach o ON o.outreach_id = cs.outreach_id
        WHERE pm.email IS NULL
        AND ct.method_type IS NOT NULL
        AND o.domain IS NOT NULL
        AND pm.first_name IS NOT NULL
        AND pm.last_name IS NOT NULL
    """)
    candidates = cur.fetchall()

    print(f"  Candidates: {len(candidates)}")

    if not candidates:
        print("  No candidates for email generation")
        return 0

    if dry_run:
        print(f"  [DRY RUN] Would generate {len(candidates)} emails")
        return len(candidates)

    # Generate emails
    generated = 0
    for unique_id, first_name, last_name, domain, method_type in candidates:
        first = clean_name(first_name)
        last = clean_name(last_name)

        if not first or not last:
            continue

        if method_type == 'first.last':
            email = f"{first}.{last}@{domain}"
        else:
            email = f"{first}.{last}@{domain}"

        cur.execute("""
            UPDATE people.people_master
            SET email = %s,
                email_verification_source = 'pattern_generated',
                updated_at = NOW()
            WHERE unique_id = %s
            AND email IS NULL
        """, (email, unique_id))

        if cur.rowcount > 0:
            generated += 1

        if generated % 500 == 0:
            conn.commit()

    conn.commit()
    print(f"  Generated: {generated} emails")
    return generated


# ============================================================================
# STEP 3: VERIFY EMAILS
# ============================================================================

class CreditTracker:
    """Tracks API credit usage with throttling."""

    def __init__(self, conn, max_per_run: int, daily_limit: int):
        self.conn = conn
        self.max_per_run = max_per_run
        self.daily_limit = daily_limit
        self.used_this_run = 0
        self._ensure_table()

    def _ensure_table(self):
        cur = self.conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS outreach.mv_credit_usage (
                id SERIAL PRIMARY KEY,
                usage_date DATE NOT NULL,
                credits_used INTEGER DEFAULT 0,
                cost_estimate NUMERIC(10,4) DEFAULT 0,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE(usage_date)
            )
        """)
        self.conn.commit()

    def get_daily_usage(self) -> int:
        cur = self.conn.cursor()
        cur.execute("""
            SELECT COALESCE(credits_used, 0)
            FROM outreach.mv_credit_usage WHERE usage_date = CURRENT_DATE
        """)
        result = cur.fetchone()
        return result[0] if result else 0

    def can_use(self, count: int = 1) -> bool:
        if self.used_this_run + count > self.max_per_run:
            return False
        if self.get_daily_usage() + count > self.daily_limit:
            return False
        return True

    def use(self, count: int = 1):
        self.used_this_run += count
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO outreach.mv_credit_usage (usage_date, credits_used, cost_estimate)
            VALUES (CURRENT_DATE, %s, %s)
            ON CONFLICT (usage_date) DO UPDATE SET
                credits_used = outreach.mv_credit_usage.credits_used + EXCLUDED.credits_used,
                cost_estimate = outreach.mv_credit_usage.cost_estimate + EXCLUDED.cost_estimate,
                updated_at = NOW()
        """, (count, count * COST_PER_VERIFICATION))
        self.conn.commit()


async def verify_single_email(session: aiohttp.ClientSession, email: str, api_key: str) -> Dict:
    url = f"https://api.millionverifier.com/api/v3/?api={api_key}&email={email}"
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
            if response.status == 200:
                data = await response.json()
                result_code = data.get('result', 'unknown').lower()
                return {
                    'success': True,
                    'result': result_code,
                    'is_valid': result_code in VALID_RESULTS,
                }
            return {'success': False, 'error': f'HTTP {response.status}'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


async def verify_emails(
    conn,
    api_key: str,
    max_verify: int,
    daily_limit: int,
    dry_run: bool = False
) -> Dict[str, int]:
    """Verify pattern-generated emails through MillionVerifier."""
    cur = conn.cursor()

    print("\n[STEP 3] VERIFY EMAILS (MillionVerifier)")
    print("-" * 50)

    tracker = CreditTracker(conn, max_per_run=max_verify, daily_limit=daily_limit)

    daily_used = tracker.get_daily_usage()
    remaining = min(max_verify, daily_limit - daily_used)

    print(f"  Daily limit: {daily_limit}, Used today: {daily_used}")
    print(f"  Run limit: {max_verify}, Available: {remaining}")

    if remaining <= 0:
        print("  [THROTTLED] Daily limit reached")
        return {'verified': 0, 'valid': 0, 'invalid': 0}

    # Get unverified emails
    cur.execute("""
        SELECT unique_id, email
        FROM people.people_master
        WHERE email_verification_source = 'pattern_generated'
        AND (email_verified = false OR email_verified IS NULL)
        AND email IS NOT NULL
        LIMIT %s
    """, (remaining,))
    emails = cur.fetchall()

    print(f"  Emails to verify: {len(emails)}")
    print(f"  Estimated cost: ${len(emails) * COST_PER_VERIFICATION:.2f}")

    if not emails:
        print("  No unverified emails found")
        return {'verified': 0, 'valid': 0, 'invalid': 0}

    if dry_run:
        print(f"  [DRY RUN] Would verify {len(emails)} emails")
        return {'verified': len(emails), 'valid': 0, 'invalid': 0}

    # Verify
    results = {'verified': 0, 'valid': 0, 'invalid': 0}

    async with aiohttp.ClientSession() as session:
        for unique_id, email in emails:
            if not tracker.can_use(1):
                print("  [THROTTLED] Credit limit reached")
                break

            result = await verify_single_email(session, email, api_key)

            if result['success']:
                tracker.use(1)
                is_valid = result['is_valid']
                source = 'mv_verified' if is_valid else 'mv_invalid'

                cur.execute("""
                    UPDATE people.people_master
                    SET email_verified = %s,
                        email_verified_at = %s,
                        email_verification_source = %s,
                        updated_at = NOW()
                    WHERE unique_id = %s
                """, (is_valid, datetime.now(timezone.utc), source, unique_id))
                conn.commit()

                results['verified'] += 1
                if is_valid:
                    results['valid'] += 1
                else:
                    results['invalid'] += 1

            await asyncio.sleep(0.1)

            if results['verified'] % 100 == 0:
                print(f"    Progress: {results['verified']} verified...")

    print(f"  Verified: {results['verified']}")
    print(f"  Valid: {results['valid']} ({results['valid']/results['verified']*100:.1f}%)" if results['verified'] > 0 else "")
    print(f"  Invalid: {results['invalid']}")
    print(f"  Cost: ${results['verified'] * COST_PER_VERIFICATION:.2f}")

    return results


# ============================================================================
# MAIN PIPELINE
# ============================================================================

async def run_pipeline(
    step: Optional[str] = None,
    run_all: bool = False,
    verify_limit: int = DEFAULT_VERIFY_LIMIT,
    daily_limit: int = DEFAULT_DAILY_LIMIT,
    dry_run: bool = False
):
    """Run the people slot pipeline."""

    print("=" * 70)
    print("PEOPLE SLOT PIPELINE")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print("=" * 70)

    conn = connect_db()
    api_key = os.environ.get('MILLIONVERIFIER_API_KEY')

    # Run steps
    if step == 'fill' or run_all:
        fill_slots(conn, dry_run)

    if step == 'generate' or run_all:
        generate_emails(conn, dry_run)

    if step == 'verify' or run_all:
        if not api_key:
            print("\n[ERROR] MILLIONVERIFIER_API_KEY not found")
            print("  Skipping verification step")
        else:
            await verify_emails(conn, api_key, verify_limit, daily_limit, dry_run)

    # Final status
    print("\n" + "=" * 70)
    print("PIPELINE STATUS")
    print("=" * 70)

    cur = conn.cursor()

    # Slot status
    cur.execute("""
        SELECT slot_type, COUNT(*) FILTER (WHERE is_filled), COUNT(*)
        FROM people.company_slot GROUP BY slot_type ORDER BY slot_type
    """)
    print("\nSlot Fill:")
    for row in cur.fetchall():
        pct = row[1] / row[2] * 100 if row[2] > 0 else 0
        print(f"  {row[0]}: {row[1]:,} / {row[2]:,} ({pct:.1f}%)")

    # Email status
    cur.execute("SELECT COUNT(*) FROM people.people_master WHERE email IS NOT NULL")
    with_email = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM people.people_master WHERE email_verified = true")
    verified = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM people.people_master")
    total = cur.fetchone()[0]

    print(f"\nPeople Email Status:")
    print(f"  With email: {with_email:,} / {total:,}")
    print(f"  Verified: {verified:,}")

    conn.close()


def main():
    parser = argparse.ArgumentParser(description='People Slot Pipeline')
    parser.add_argument('--step', choices=['fill', 'generate', 'verify'],
                        help='Run single step')
    parser.add_argument('--all', action='store_true', help='Run entire pipeline')
    parser.add_argument('--dry-run', action='store_true', help='Preview without changes')
    parser.add_argument('--verify-limit', type=int, default=DEFAULT_VERIFY_LIMIT,
                        help=f'Max emails to verify (default: {DEFAULT_VERIFY_LIMIT})')
    parser.add_argument('--daily-limit', type=int, default=DEFAULT_DAILY_LIMIT,
                        help=f'Max daily verifications (default: {DEFAULT_DAILY_LIMIT})')
    parser.add_argument('--budget', type=float, help='Max spend in dollars')

    args = parser.parse_args()

    if not args.step and not args.all:
        parser.print_help()
        print("\n[ERROR] Must specify --step or --all")
        sys.exit(1)

    verify_limit = args.verify_limit
    if args.budget:
        verify_limit = int(args.budget / COST_PER_VERIFICATION)
        print(f"[INFO] Budget ${args.budget:.2f} = ~{verify_limit:,} verifications")

    asyncio.run(run_pipeline(
        step=args.step,
        run_all=args.all,
        verify_limit=verify_limit,
        daily_limit=args.daily_limit,
        dry_run=args.dry_run
    ))


if __name__ == "__main__":
    main()
