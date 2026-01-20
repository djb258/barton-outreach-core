#!/usr/bin/env python3
"""
Tier Snapshot Job
=================

Captures daily snapshots of tier distribution and hub metrics.

Usage:
    python ops/metrics/tier_snapshot.py [--dry-run]

Schedule:
    Recommended: Run daily at 00:00 UTC via cron or scheduler.

DOCTRINE:
    - READ-ONLY: Does not modify tier computation logic
    - Does not touch kill switches or hub status logic
    - Only captures metrics for observability
"""

import argparse
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional

import psycopg2
from psycopg2.extras import RealDictCursor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('tier_snapshot')


def get_db_connection():
    """Get database connection."""
    return psycopg2.connect(
        host=os.getenv('NEON_HOST', 'ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech'),
        port=5432,
        database=os.getenv('NEON_DATABASE', 'Marketing DB'),
        user=os.getenv('NEON_USER', 'Marketing DB_owner'),
        password=os.getenv('NEON_PASSWORD', 'npg_OsE4Z2oPCpiT'),
        sslmode='require'
    )


def capture_tier_snapshot(dry_run: bool = False) -> Dict[str, Any]:
    """
    Capture a daily snapshot of tier distribution.

    Calls the database function fn_capture_tier_snapshot() which:
    1. Reads from vw_tier_telemetry_summary
    2. Aggregates hub pass/block rates
    3. Upserts to tier_snapshot_history

    Args:
        dry_run: If True, only read data without writing snapshot

    Returns:
        Snapshot data dict
    """
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    stats = {
        'snapshot_date': datetime.now().date().isoformat(),
        'snapshot_id': None,
        'tier_distribution': {},
        'hub_pass_rates': {},
        'hub_block_rates': {},
        'success': False,
        'error': None,
    }

    try:
        logger.info("Fetching current tier telemetry...")

        # Get current telemetry
        cur.execute("SELECT * FROM outreach.vw_tier_telemetry_summary")
        telemetry = cur.fetchone()

        if not telemetry:
            raise ValueError("No telemetry data returned from vw_tier_telemetry_summary")

        stats['tier_distribution'] = {
            'total': telemetry['total_companies'],
            'ineligible': telemetry['ineligible_count'],
            'tier_0': telemetry['tier_0_count'],
            'tier_1': telemetry['tier_1_count'],
            'tier_2': telemetry['tier_2_count'],
            'tier_3': telemetry['tier_3_count'],
            'blocked': telemetry['blocked_total'],
            'complete': telemetry['complete_total'],
            'in_progress': telemetry['in_progress_total'],
        }

        stats['hub_pass_rates'] = telemetry.get('hub_pass_rates') or {}

        # Get hub block analysis
        cur.execute("""
            SELECT hub_id, blocked_percentage
            FROM outreach.vw_hub_block_analysis
            WHERE blocked_percentage IS NOT NULL
        """)
        for row in cur.fetchall():
            stats['hub_block_rates'][row['hub_id']] = float(row['blocked_percentage'])

        # Get freshness analysis
        cur.execute("""
            SELECT hub_id, stale_percentage
            FROM outreach.vw_freshness_analysis
            WHERE stale_percentage IS NOT NULL
        """)
        stats['freshness_stats'] = {}
        for row in cur.fetchall():
            stats['freshness_stats'][row['hub_id']] = float(row['stale_percentage'])

        # Capture snapshot (unless dry run)
        if not dry_run:
            logger.info("Capturing snapshot to tier_snapshot_history...")
            cur.execute("SELECT outreach.fn_capture_tier_snapshot() as snapshot_id")
            result = cur.fetchone()
            stats['snapshot_id'] = str(result['snapshot_id'])
            conn.commit()
            logger.info(f"Snapshot captured: {stats['snapshot_id']}")
        else:
            logger.info("DRY RUN - Snapshot not written")

        stats['success'] = True

    except Exception as e:
        logger.error(f"Error capturing snapshot: {e}")
        stats['error'] = str(e)
        conn.rollback()

    finally:
        cur.close()
        conn.close()

    return stats


def get_tier_drift(days: int = 7) -> Dict[str, Any]:
    """
    Get tier drift analysis for the last N days.

    Args:
        days: Number of days to analyze

    Returns:
        Drift analysis dict
    """
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cur.execute("""
            SELECT *
            FROM outreach.vw_tier_drift_analysis
            LIMIT %s
        """, (days,))

        rows = cur.fetchall()

        drift_data = {
            'period_days': days,
            'snapshots': [],
            'has_drift': False,
        }

        for row in rows:
            snapshot = {
                'date': row['snapshot_date'].isoformat(),
                'total': row['total_companies'],
                'tiers': {
                    'ineligible': row['ineligible_count'],
                    'tier_0': row['tier_0_count'],
                    'tier_1': row['tier_1_count'],
                    'tier_2': row['tier_2_count'],
                    'tier_3': row['tier_3_count'],
                },
                'deltas': {
                    'ineligible': row['ineligible_delta'],
                    'tier_0': row['tier_0_delta'],
                    'tier_1': row['tier_1_delta'],
                    'tier_2': row['tier_2_delta'],
                    'tier_3': row['tier_3_delta'],
                },
            }
            drift_data['snapshots'].append(snapshot)

            # Check for significant drift (>5% change)
            if any(abs(d or 0) > (row['total_companies'] * 0.05) for d in snapshot['deltas'].values()):
                drift_data['has_drift'] = True

        return drift_data

    finally:
        cur.close()
        conn.close()


def print_snapshot_summary(stats: Dict[str, Any]) -> None:
    """Print a formatted snapshot summary."""
    print()
    print("=" * 60)
    print("TIER SNAPSHOT SUMMARY")
    print("=" * 60)
    print(f"Date: {stats['snapshot_date']}")
    print(f"Snapshot ID: {stats.get('snapshot_id', 'N/A')}")
    print()

    if not stats['success']:
        print(f"ERROR: {stats.get('error', 'Unknown error')}")
        return

    td = stats['tier_distribution']
    print("TIER DISTRIBUTION:")
    print(f"  Total Companies: {td['total']}")
    print()
    print(f"  INELIGIBLE (Tier -1): {td['ineligible']:,} ({td['ineligible']/td['total']*100:.1f}%)")
    print(f"  Tier 0 (Cold):        {td['tier_0']:,} ({td['tier_0']/td['total']*100:.1f}%)")
    print(f"  Tier 1 (Persona):     {td['tier_1']:,} ({td['tier_1']/td['total']*100:.1f}%)")
    print(f"  Tier 2 (Trigger):     {td['tier_2']:,} ({td['tier_2']/td['total']*100:.1f}%)")
    print(f"  Tier 3 (Aggressive):  {td['tier_3']:,} ({td['tier_3']/td['total']*100:.1f}%)")
    print()

    print("STATUS DISTRIBUTION:")
    print(f"  BLOCKED:     {td['blocked']:,}")
    print(f"  COMPLETE:    {td['complete']:,}")
    print(f"  IN_PROGRESS: {td['in_progress']:,}")
    print()

    if stats.get('hub_pass_rates'):
        print("HUB PASS RATES:")
        for hub_id, rate in sorted(stats['hub_pass_rates'].items()):
            print(f"  {hub_id}: {rate}%")
        print()

    if stats.get('hub_block_rates'):
        print("HUB BLOCK RATES:")
        for hub_id, rate in sorted(stats['hub_block_rates'].items()):
            print(f"  {hub_id}: {rate}%")
        print()

    if stats.get('freshness_stats'):
        print("FRESHNESS (% STALE):")
        for hub_id, rate in sorted(stats['freshness_stats'].items()):
            print(f"  {hub_id}: {rate}%")
        print()

    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description='Tier Snapshot Job')
    parser.add_argument('--dry-run', action='store_true',
                        help='Read data without writing snapshot')
    parser.add_argument('--drift', action='store_true',
                        help='Show drift analysis')
    parser.add_argument('--days', type=int, default=7,
                        help='Days for drift analysis (default: 7)')
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("TIER SNAPSHOT JOB")
    logger.info("=" * 60)

    if args.dry_run:
        logger.info("*** DRY RUN MODE ***")

    try:
        # Capture snapshot
        stats = capture_tier_snapshot(dry_run=args.dry_run)
        print_snapshot_summary(stats)

        # Show drift if requested
        if args.drift:
            print()
            print("TIER DRIFT ANALYSIS (Last {} days)".format(args.days))
            print("-" * 40)
            drift = get_tier_drift(days=args.days)

            if drift['has_drift']:
                print("WARNING: Significant drift detected!")

            for snapshot in drift['snapshots']:
                deltas = snapshot['deltas']
                delta_str = ", ".join(
                    f"{k}: {'+' if v and v > 0 else ''}{v or 0}"
                    for k, v in deltas.items()
                    if v
                )
                print(f"  {snapshot['date']}: {delta_str or 'No change'}")

        if not stats['success']:
            return 1

        return 0

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
