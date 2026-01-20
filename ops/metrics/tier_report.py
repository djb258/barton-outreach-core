#!/usr/bin/env python3
"""
Tier Telemetry Report Generator
================================

Generates lightweight markdown reports from tier telemetry data.

Usage:
    python ops/metrics/tier_report.py [--output FILE] [--days N]

Output:
    Markdown report to stdout or file.

DOCTRINE:
    - READ-ONLY: Does not modify any data
    - Does not touch tier computation logic
    - Does not touch kill switches or hub status logic
"""

import argparse
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional, List

import psycopg2
from psycopg2.extras import RealDictCursor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('tier_report')


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


def fetch_tier_distribution() -> Dict[str, Any]:
    """Fetch current tier distribution from view."""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cur.execute("SELECT * FROM outreach.vw_tier_distribution ORDER BY marketing_tier")
        rows = cur.fetchall()
        return {
            'tiers': [dict(row) for row in rows],
            'fetched_at': datetime.utcnow().isoformat()
        }
    finally:
        cur.close()
        conn.close()


def fetch_hub_block_analysis() -> List[Dict[str, Any]]:
    """Fetch hub block analysis from view."""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cur.execute("SELECT * FROM outreach.vw_hub_block_analysis ORDER BY waterfall_order")
        return [dict(row) for row in cur.fetchall()]
    finally:
        cur.close()
        conn.close()


def fetch_freshness_analysis() -> List[Dict[str, Any]]:
    """Fetch freshness analysis from view."""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cur.execute("SELECT * FROM outreach.vw_freshness_analysis ORDER BY hub_id")
        return [dict(row) for row in cur.fetchall()]
    finally:
        cur.close()
        conn.close()


def fetch_signal_gap_analysis() -> List[Dict[str, Any]]:
    """Fetch signal gap analysis from view."""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cur.execute("SELECT * FROM outreach.vw_signal_gap_analysis ORDER BY hub_id")
        return [dict(row) for row in cur.fetchall()]
    finally:
        cur.close()
        conn.close()


def fetch_drift_analysis(days: int = 7) -> List[Dict[str, Any]]:
    """Fetch tier drift analysis from view."""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cur.execute("""
            SELECT * FROM outreach.vw_tier_drift_analysis
            LIMIT %s
        """, (days,))
        return [dict(row) for row in cur.fetchall()]
    finally:
        cur.close()
        conn.close()


def generate_markdown_report(days: int = 7) -> str:
    """
    Generate a complete markdown report.

    Args:
        days: Number of days for drift analysis

    Returns:
        Markdown string
    """
    report = []
    now = datetime.utcnow()

    # Header
    report.append("# Tier Telemetry Report")
    report.append("")
    report.append(f"**Generated:** {now.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    report.append("")
    report.append("---")
    report.append("")

    # Tier Distribution
    report.append("## Tier Distribution")
    report.append("")

    try:
        tier_data = fetch_tier_distribution()
        total = sum(t['company_count'] for t in tier_data['tiers'])

        report.append("| Tier | Name | Count | Percentage |")
        report.append("|------|------|-------|------------|")

        for tier in tier_data['tiers']:
            report.append(
                f"| {tier['marketing_tier']} | {tier['tier_name']} | "
                f"{tier['company_count']:,} | {tier['percentage']}% |"
            )

        report.append("")
        report.append(f"**Total Companies:** {total:,}")
        report.append("")

    except Exception as e:
        report.append(f"*Error fetching tier distribution: {e}*")
        report.append("")

    # Hub Block Analysis
    report.append("## Hub Block Analysis")
    report.append("")
    report.append("Shows which hubs are causing the most blocks.")
    report.append("")

    try:
        hub_data = fetch_hub_block_analysis()

        report.append("| Hub | PASS | IN_PROGRESS | FAIL | BLOCKED | Block % |")
        report.append("|-----|------|-------------|------|---------|---------|")

        for hub in hub_data:
            block_pct = hub.get('blocked_percentage') or 0
            status_icon = "🟢" if block_pct < 5 else ("🟡" if block_pct < 20 else "🔴")
            report.append(
                f"| {hub['hub_name']} | {hub.get('pass_count', 0):,} | "
                f"{hub.get('in_progress_count', 0):,} | {hub.get('fail_count', 0):,} | "
                f"{hub.get('blocked_by_upstream_count', 0):,} | {status_icon} {block_pct}% |"
            )

        report.append("")

    except Exception as e:
        report.append(f"*Error fetching hub block analysis: {e}*")
        report.append("")

    # Freshness Analysis
    report.append("## Freshness Analysis")
    report.append("")
    report.append("Shows % of companies with stale data per hub.")
    report.append("")

    try:
        freshness_data = fetch_freshness_analysis()

        report.append("| Hub | Freshness Window | Fresh | Stale | Stale % |")
        report.append("|-----|------------------|-------|-------|---------|")

        for hub in freshness_data:
            stale_pct = hub.get('stale_percentage') or 0
            status_icon = "🟢" if stale_pct < 10 else ("🟡" if stale_pct < 30 else "🔴")
            freshness_days = hub.get('freshness_days') or 'N/A'
            report.append(
                f"| {hub['hub_name']} | {freshness_days} days | "
                f"{hub.get('fresh_count', 0):,} | {hub.get('stale_count', 0):,} | "
                f"{status_icon} {stale_pct}% |"
            )

        report.append("")

    except Exception as e:
        report.append(f"*Error fetching freshness analysis: {e}*")
        report.append("")

    # Signal Gap Analysis
    report.append("## Signal Gap Analysis")
    report.append("")
    report.append("Shows % of companies lacking signals per hub.")
    report.append("")

    try:
        signal_data = fetch_signal_gap_analysis()

        report.append("| Hub | With Signals | Lacking Signals | Gap % |")
        report.append("|-----|--------------|-----------------|-------|")

        for hub in signal_data:
            gap_pct = hub.get('lacking_signals_percentage') or 0
            status_icon = "🟢" if gap_pct < 20 else ("🟡" if gap_pct < 50 else "🔴")
            report.append(
                f"| {hub['hub_name']} | {hub.get('companies_with_signals', 0):,} | "
                f"{hub.get('companies_lacking_signals', 0):,} | {status_icon} {gap_pct}% |"
            )

        report.append("")

    except Exception as e:
        report.append(f"*Error fetching signal gap analysis: {e}*")
        report.append("")

    # Drift Analysis
    report.append(f"## Tier Drift (Last {days} Days)")
    report.append("")

    try:
        drift_data = fetch_drift_analysis(days)

        if drift_data:
            report.append("| Date | Ineligible | Tier 0 | Tier 1 | Tier 2 | Tier 3 |")
            report.append("|------|------------|--------|--------|--------|--------|")

            for snapshot in drift_data:
                date_str = snapshot['snapshot_date'].strftime('%Y-%m-%d')
                inelig_delta = snapshot.get('ineligible_delta') or 0
                t0_delta = snapshot.get('tier_0_delta') or 0
                t1_delta = snapshot.get('tier_1_delta') or 0
                t2_delta = snapshot.get('tier_2_delta') or 0
                t3_delta = snapshot.get('tier_3_delta') or 0

                def fmt_delta(count, delta):
                    if delta > 0:
                        return f"{count:,} (+{delta})"
                    elif delta < 0:
                        return f"{count:,} ({delta})"
                    return f"{count:,}"

                report.append(
                    f"| {date_str} | "
                    f"{fmt_delta(snapshot['ineligible_count'], inelig_delta)} | "
                    f"{fmt_delta(snapshot['tier_0_count'], t0_delta)} | "
                    f"{fmt_delta(snapshot['tier_1_count'], t1_delta)} | "
                    f"{fmt_delta(snapshot['tier_2_count'], t2_delta)} | "
                    f"{fmt_delta(snapshot['tier_3_count'], t3_delta)} |"
                )

            report.append("")

            # Check for significant drift
            has_significant_drift = any(
                any(abs(s.get(f'{t}_delta') or 0) > (s['total_companies'] * 0.05)
                    for t in ['ineligible', 'tier_0', 'tier_1', 'tier_2', 'tier_3'])
                for s in drift_data
            )

            if has_significant_drift:
                report.append("> ⚠️ **Warning:** Significant tier drift detected (>5% change)")
                report.append("")
        else:
            report.append("*No historical snapshots available. Run tier_snapshot.py to capture data.*")
            report.append("")

    except Exception as e:
        report.append(f"*Error fetching drift analysis: {e}*")
        report.append("")

    # Footer
    report.append("---")
    report.append("")
    report.append("*Report generated by `ops/metrics/tier_report.py`*")
    report.append("")

    return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(description='Tier Telemetry Report Generator')
    parser.add_argument('--output', '-o', type=str, default=None,
                        help='Output file path (default: stdout)')
    parser.add_argument('--days', type=int, default=7,
                        help='Days for drift analysis (default: 7)')
    args = parser.parse_args()

    try:
        report = generate_markdown_report(days=args.days)

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"Report written to {args.output}")
        else:
            print(report)

        return 0

    except Exception as e:
        logger.error(f"Error generating report: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
