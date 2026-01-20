"""
Blog Content Hub — Status Computation
======================================

Doctrine: CL Parent-Child v1.1
Hub ID: blog-content
Waterfall Order: 5 (optional hub, does not gate completion)

SIGNAL-ONLY MODE:
    This hub ONLY produces signals. It NEVER writes identity.
    All signals must reference a valid company_unique_id.

PASS CRITERIA (deterministic):
    1. company_unique_id exists in outreach.blog
    2. At least ONE valid blog signal in last FRESHNESS_DAYS
    3. Signal has valid deduplication hash (no duplicates)

FRESHNESS RULE:
    Blog signals decay over time.
    PASS status requires at least one signal within FRESHNESS_DAYS.

STATUS TRANSITIONS:
    IN_PROGRESS → PASS: When valid signal exists within freshness window
    PASS → IN_PROGRESS: When all signals expire (freshness decay)
    * → FAIL: Reserved for explicit failures (not used - signals are dropped, not failed)
"""

import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Configuration (Locked)
FRESHNESS_DAYS = 30  # Blog signals expire after 30 days
MIN_SIGNALS = 1  # Minimum signals to PASS


@dataclass
class BlogHubStatusResult:
    """Result of hub status computation"""
    company_unique_id: str
    status: str  # PASS, IN_PROGRESS, FAIL, BLOCKED
    status_reason: str
    metric_value: Optional[float] = None  # Signal count
    last_processed_at: Optional[datetime] = None
    details: Optional[Dict[str, Any]] = None


def generate_blog_signal_hash(
    company_unique_id: str,
    article_url: str,
    event_type: str
) -> str:
    """
    Generate deduplication hash for blog signal.

    Hash key: (company_unique_id, article_url, event_type)
    """
    unique_string = f"{company_unique_id}|{article_url}|{event_type}"
    return hashlib.sha256(unique_string.encode()).hexdigest()


def compute_blog_hub_status(
    company_unique_id: str,
    blog_signals: List[Dict[str, Any]],
    freshness_cutoff: Optional[datetime] = None
) -> BlogHubStatusResult:
    """
    Compute hub status for Blog Content.

    PASS criteria (ALL must be true):
        1. At least MIN_SIGNALS valid signals
        2. At least one signal within freshness window
        3. company_unique_id is valid

    Args:
        company_unique_id: The company to compute status for
        blog_signals: List of blog signals for this company
        freshness_cutoff: Cutoff datetime for freshness (default: now - FRESHNESS_DAYS)

    Returns:
        BlogHubStatusResult with status and reason
    """
    if not company_unique_id:
        return BlogHubStatusResult(
            company_unique_id=company_unique_id or 'UNKNOWN',
            status='FAIL',
            status_reason='company_unique_id is NULL',
            metric_value=0
        )

    if freshness_cutoff is None:
        freshness_cutoff = datetime.utcnow() - timedelta(days=FRESHNESS_DAYS)

    if not blog_signals:
        return BlogHubStatusResult(
            company_unique_id=company_unique_id,
            status='IN_PROGRESS',
            status_reason='No blog signals found',
            metric_value=0,
            details={'fresh_signals': 0, 'total_signals': 0}
        )

    # Count fresh signals (within freshness window)
    fresh_signals = 0
    seen_hashes = set()

    for signal in blog_signals:
        signal_time = signal.get('created_at') or signal.get('detected_at')
        article_url = signal.get('source_url') or signal.get('article_url', '')
        event_type = signal.get('event_type', 'unknown')

        # Skip duplicates (based on hash)
        signal_hash = generate_blog_signal_hash(company_unique_id, article_url, event_type)
        if signal_hash in seen_hashes:
            continue
        seen_hashes.add(signal_hash)

        # Check freshness
        if signal_time:
            if isinstance(signal_time, str):
                try:
                    signal_time = datetime.fromisoformat(signal_time.replace('Z', '+00:00'))
                except ValueError:
                    continue

            if signal_time >= freshness_cutoff:
                fresh_signals += 1

    total_signals = len(seen_hashes)
    latest_signal = max(
        (s.get('created_at') or s.get('detected_at') for s in blog_signals if s.get('created_at') or s.get('detected_at')),
        default=None
    )

    # Determine status
    if fresh_signals >= MIN_SIGNALS:
        return BlogHubStatusResult(
            company_unique_id=company_unique_id,
            status='PASS',
            status_reason=f'{fresh_signals} fresh signal(s) within {FRESHNESS_DAYS} days',
            metric_value=float(fresh_signals),
            last_processed_at=latest_signal,
            details={
                'fresh_signals': fresh_signals,
                'total_signals': total_signals,
                'freshness_days': FRESHNESS_DAYS
            }
        )
    else:
        if total_signals > 0:
            reason = f'No fresh signals: {total_signals} total signal(s) but none within {FRESHNESS_DAYS} days'
        else:
            reason = 'No valid signals (all duplicates filtered)'

        return BlogHubStatusResult(
            company_unique_id=company_unique_id,
            status='IN_PROGRESS',
            status_reason=reason,
            metric_value=float(fresh_signals),
            last_processed_at=latest_signal,
            details={
                'fresh_signals': fresh_signals,
                'total_signals': total_signals,
                'freshness_days': FRESHNESS_DAYS,
                'freshness_expired': total_signals > 0
            }
        )


async def backfill_blog_hub_status(conn) -> Dict[str, int]:
    """
    Backfill hub status for all companies in outreach.blog.

    Args:
        conn: Database connection (asyncpg or psycopg2)

    Returns:
        Dict with counts: {'total': N, 'pass': N, 'in_progress': N}
    """
    logger.info("Starting Blog Content hub status backfill")

    counts = {'total': 0, 'pass': 0, 'in_progress': 0, 'fail': 0, 'blocked': 0}

    # Query all companies with blog signals
    # Group by company_unique_id and count fresh signals
    query = """
        WITH company_signals AS (
            SELECT
                company_unique_id,
                COUNT(*) as total_signals,
                COUNT(*) FILTER (
                    WHERE created_at >= NOW() - INTERVAL '%s days'
                ) as fresh_signals,
                MAX(created_at) as last_signal
            FROM outreach.blog
            WHERE company_unique_id IS NOT NULL
            GROUP BY company_unique_id
        )
        SELECT
            company_unique_id,
            total_signals,
            fresh_signals,
            last_signal,
            CASE
                WHEN fresh_signals >= %s THEN 'PASS'
                ELSE 'IN_PROGRESS'
            END as computed_status
        FROM company_signals
    """

    try:
        # Check if using asyncpg or psycopg2
        if hasattr(conn, 'fetch'):
            # asyncpg - use $1, $2 syntax
            query_asyncpg = query.replace('%s', '$1', 1).replace('%s', '$2', 1)
            rows = await conn.fetch(query_asyncpg, FRESHNESS_DAYS, MIN_SIGNALS)
        else:
            # psycopg2
            cursor = conn.cursor()
            cursor.execute(query, (FRESHNESS_DAYS, MIN_SIGNALS))
            rows = cursor.fetchall()

        for row in rows:
            if hasattr(row, 'get'):
                # asyncpg Record
                company_id = row['company_unique_id']
                status = row['computed_status']
                fresh = row['fresh_signals']
                total = row['total_signals']
            else:
                # psycopg2 tuple
                company_id, total, fresh, last_signal, status = row

            # Upsert to company_hub_status
            upsert_query = """
                INSERT INTO outreach.company_hub_status
                    (company_unique_id, hub_id, status, metric_value, status_reason, last_processed_at)
                VALUES (%s, 'blog-content', %s::outreach.hub_status_enum, %s, %s, NOW())
                ON CONFLICT (company_unique_id, hub_id)
                DO UPDATE SET
                    status = EXCLUDED.status,
                    metric_value = EXCLUDED.metric_value,
                    status_reason = EXCLUDED.status_reason,
                    last_processed_at = EXCLUDED.last_processed_at
            """

            reason = f'{fresh} fresh signal(s), {total} total signals'

            if hasattr(conn, 'execute'):
                # asyncpg
                upsert_asyncpg = upsert_query.replace('%s', '$1', 1).replace('%s', '$2', 1).replace('%s', '$3', 1).replace('%s', '$4', 1)
                await conn.execute(upsert_asyncpg, company_id, status, float(fresh), reason)
            else:
                cursor.execute(upsert_query, (company_id, status, float(fresh), reason))

            counts['total'] += 1
            counts[status.lower()] += 1

        if not hasattr(conn, 'execute'):
            conn.commit()

        logger.info(f"Blog Content backfill complete: {counts}")
        return counts

    except Exception as e:
        logger.error(f"Blog Content backfill failed: {e}")
        raise
