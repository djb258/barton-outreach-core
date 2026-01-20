"""
People Intelligence Hub — Status Computation
==============================================

Doctrine: CL Parent-Child v1.1
Hub ID: people-intelligence
Waterfall Order: 3

PASS CRITERIA (deterministic, no fuzzy logic):
    1. company_unique_id exists in outreach.people
    2. At least ONE slot holder with verified contact anchor:
       - full_name IS NOT NULL
       - title IS NOT NULL
       - linkedin_url IS NOT NULL (minimal People Slot Contract)
    3. Freshness: Last update within FRESHNESS_DAYS

FRESHNESS RULE:
    PASS status expires after N days without updates.
    After expiration, status reverts to IN_PROGRESS until re-verified.

STATUS TRANSITIONS:
    IN_PROGRESS → PASS: When criteria met
    PASS → IN_PROGRESS: When freshness expires
    * → FAIL: Reserved for explicit failures (not used here)
    * → BLOCKED: Reserved for upstream blocks (not used here)
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Configuration (Locked)
FRESHNESS_DAYS = 90  # PASS expires after 90 days without update
MIN_VERIFIED_SLOTS = 1  # Minimum slots with contact anchor to PASS


@dataclass
class PeopleHubStatusResult:
    """Result of hub status computation"""
    company_unique_id: str
    status: str  # PASS, IN_PROGRESS, FAIL, BLOCKED
    status_reason: str
    metric_value: Optional[float] = None  # Slot fill rate (0-100)
    last_processed_at: Optional[datetime] = None
    details: Optional[Dict[str, Any]] = None


def compute_people_hub_status(
    company_unique_id: str,
    people_records: List[Dict[str, Any]],
    last_update: Optional[datetime] = None
) -> PeopleHubStatusResult:
    """
    Compute hub status for People Intelligence.

    PASS criteria (ALL must be true):
        1. At least MIN_VERIFIED_SLOTS records with contact anchor
        2. Contact anchor = full_name + title + linkedin_url all NOT NULL
        3. Freshness check passes

    Args:
        company_unique_id: The company to compute status for
        people_records: List of people records for this company
        last_update: Timestamp of last update (for freshness check)

    Returns:
        PeopleHubStatusResult with status and reason
    """
    if not company_unique_id:
        return PeopleHubStatusResult(
            company_unique_id=company_unique_id or 'UNKNOWN',
            status='FAIL',
            status_reason='company_unique_id is NULL',
            metric_value=0
        )

    if not people_records:
        return PeopleHubStatusResult(
            company_unique_id=company_unique_id,
            status='IN_PROGRESS',
            status_reason='No people records found',
            metric_value=0,
            details={'verified_slots': 0, 'total_records': 0}
        )

    # Count records with verified contact anchor
    # Contact anchor = full_name + title + linkedin_url (minimal People Slot Contract)
    verified_count = 0
    for record in people_records:
        full_name = record.get('full_name')
        title = record.get('title')
        linkedin_url = record.get('linkedin_url')

        if full_name and title and linkedin_url:
            verified_count += 1

    total_records = len(people_records)
    fill_rate = (verified_count / total_records * 100) if total_records > 0 else 0

    # Check freshness
    if last_update:
        freshness_cutoff = datetime.utcnow() - timedelta(days=FRESHNESS_DAYS)
        is_fresh = last_update >= freshness_cutoff
    else:
        # No update timestamp, assume not fresh
        is_fresh = False

    # Determine status
    if verified_count >= MIN_VERIFIED_SLOTS:
        if is_fresh:
            return PeopleHubStatusResult(
                company_unique_id=company_unique_id,
                status='PASS',
                status_reason=f'{verified_count} verified slot(s) with contact anchor',
                metric_value=fill_rate,
                last_processed_at=last_update,
                details={
                    'verified_slots': verified_count,
                    'total_records': total_records,
                    'fill_rate': fill_rate,
                    'is_fresh': True
                }
            )
        else:
            # Freshness expired - revert to IN_PROGRESS
            return PeopleHubStatusResult(
                company_unique_id=company_unique_id,
                status='IN_PROGRESS',
                status_reason=f'Freshness expired: {verified_count} verified slot(s) but last update > {FRESHNESS_DAYS} days ago',
                metric_value=fill_rate,
                last_processed_at=last_update,
                details={
                    'verified_slots': verified_count,
                    'total_records': total_records,
                    'fill_rate': fill_rate,
                    'is_fresh': False,
                    'freshness_expired': True
                }
            )
    else:
        return PeopleHubStatusResult(
            company_unique_id=company_unique_id,
            status='IN_PROGRESS',
            status_reason=f'Insufficient verified slots: {verified_count} < {MIN_VERIFIED_SLOTS} required',
            metric_value=fill_rate,
            last_processed_at=last_update,
            details={
                'verified_slots': verified_count,
                'total_records': total_records,
                'fill_rate': fill_rate,
                'required_slots': MIN_VERIFIED_SLOTS
            }
        )


async def backfill_people_hub_status(conn) -> Dict[str, int]:
    """
    Backfill hub status for all companies in outreach.people.

    Args:
        conn: Database connection (asyncpg or psycopg2)

    Returns:
        Dict with counts: {'total': N, 'pass': N, 'in_progress': N, 'fail': N}
    """
    logger.info("Starting People Intelligence hub status backfill")

    counts = {'total': 0, 'pass': 0, 'in_progress': 0, 'fail': 0, 'blocked': 0}

    # Query all companies with people records
    # Group by company_unique_id and get aggregated stats
    query = """
        WITH company_people AS (
            SELECT
                company_unique_id,
                COUNT(*) as total_records,
                COUNT(*) FILTER (
                    WHERE full_name IS NOT NULL
                    AND title IS NOT NULL
                    AND linkedin_url IS NOT NULL
                ) as verified_count,
                MAX(updated_at) as last_update
            FROM outreach.people
            WHERE company_unique_id IS NOT NULL
            GROUP BY company_unique_id
        )
        SELECT
            company_unique_id,
            total_records,
            verified_count,
            last_update,
            CASE
                WHEN verified_count >= $1
                    AND last_update >= NOW() - INTERVAL '$2 days'
                THEN 'PASS'
                ELSE 'IN_PROGRESS'
            END as computed_status
        FROM company_people
    """

    try:
        # Check if using asyncpg or psycopg2
        if hasattr(conn, 'fetch'):
            # asyncpg
            rows = await conn.fetch(query, MIN_VERIFIED_SLOTS, FRESHNESS_DAYS)
        else:
            # psycopg2
            cursor = conn.cursor()
            cursor.execute(query, (MIN_VERIFIED_SLOTS, FRESHNESS_DAYS))
            rows = cursor.fetchall()

        for row in rows:
            if hasattr(row, 'get'):
                # asyncpg Record
                company_id = row['company_unique_id']
                status = row['computed_status']
                verified = row['verified_count']
                total = row['total_records']
            else:
                # psycopg2 tuple
                company_id, total, verified, last_update, status = row

            # Upsert to company_hub_status
            upsert_query = """
                INSERT INTO outreach.company_hub_status
                    (company_unique_id, hub_id, status, metric_value, status_reason, last_processed_at)
                VALUES ($1, 'people-intelligence', $2::outreach.hub_status_enum, $3, $4, NOW())
                ON CONFLICT (company_unique_id, hub_id)
                DO UPDATE SET
                    status = EXCLUDED.status,
                    metric_value = EXCLUDED.metric_value,
                    status_reason = EXCLUDED.status_reason,
                    last_processed_at = EXCLUDED.last_processed_at
            """

            fill_rate = (verified / total * 100) if total > 0 else 0
            reason = f'{verified} verified slot(s), {total} total records'

            if hasattr(conn, 'execute'):
                await conn.execute(upsert_query, company_id, status, fill_rate, reason)
            else:
                cursor.execute(upsert_query, (company_id, status, fill_rate, reason))

            counts['total'] += 1
            counts[status.lower()] += 1

        if not hasattr(conn, 'execute'):
            conn.commit()

        logger.info(f"People Intelligence backfill complete: {counts}")
        return counts

    except Exception as e:
        logger.error(f"People Intelligence backfill failed: {e}")
        raise


def compute_status_for_db_row(row: Dict[str, Any]) -> PeopleHubStatusResult:
    """
    Compute status from a database aggregation row.

    Expected row keys:
        - company_unique_id
        - verified_count: int
        - total_records: int
        - last_update: datetime
    """
    company_id = row.get('company_unique_id')
    verified = row.get('verified_count', 0)
    total = row.get('total_records', 0)
    last_update = row.get('last_update')

    # Build mock people_records for the compute function
    # We only need the count, not actual records
    mock_records = []
    for i in range(verified):
        mock_records.append({
            'full_name': 'verified',
            'title': 'verified',
            'linkedin_url': 'verified'
        })
    for i in range(total - verified):
        mock_records.append({
            'full_name': None,
            'title': None,
            'linkedin_url': None
        })

    return compute_people_hub_status(company_id, mock_records, last_update)
