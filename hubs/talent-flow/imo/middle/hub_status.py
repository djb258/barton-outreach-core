"""
Talent Flow Hub — Status Computation
=====================================

Doctrine: CL Parent-Child v1.1
Hub ID: talent-flow
Waterfall Order: 4

PASS CRITERIA (deterministic, no fuzzy logic):
    1. company_unique_id exists in movement signals
    2. At least ONE valid movement signal:
       - event_type IN (joined, left, title_change)
       - confidence >= CONFIDENCE_THRESHOLD
    3. At least one signal within FRESHNESS_DAYS

FRESHNESS RULE:
    Movement signals decay over time.
    PASS status expires after N days without new movements.
    After expiration, status reverts to IN_PROGRESS.

STATUS TRANSITIONS:
    IN_PROGRESS → PASS: When valid movement detected within freshness window
    PASS → IN_PROGRESS: When all signals expire (freshness decay)
    * → FAIL: Reserved for explicit failures (not used - signals are sensor-only)
    * → BLOCKED: Reserved for upstream blocks (People Intelligence must PASS)

SENSOR-ONLY MODE:
    This hub ONLY detects movements. It NEVER triggers enrichment.
    All signals must reference a valid company_unique_id from upstream.
"""

import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

# Configuration (Locked)
FRESHNESS_DAYS = 60  # Movement signals expire after 60 days
MIN_MOVEMENTS = 1  # Minimum movements to PASS
CONFIDENCE_THRESHOLD = 0.70  # Minimum confidence for valid movement


class MovementType(Enum):
    """Types of movements that contribute to PASS status."""
    JOINED = "joined"
    LEFT = "left"
    TITLE_CHANGE = "title_change"


# Valid movement types for PASS criteria
VALID_MOVEMENT_TYPES = {
    MovementType.JOINED.value,
    MovementType.LEFT.value,
    MovementType.TITLE_CHANGE.value,
}


@dataclass
class TalentFlowHubStatusResult:
    """Result of hub status computation"""
    company_unique_id: str
    status: str  # PASS, IN_PROGRESS, FAIL, BLOCKED
    status_reason: str
    metric_value: Optional[float] = None  # Movement detection rate
    last_processed_at: Optional[datetime] = None
    details: Optional[Dict[str, Any]] = None


def generate_movement_signal_hash(
    company_unique_id: str,
    person_id: str,
    event_type: str,
    detected_at: str
) -> str:
    """
    Generate deduplication hash for movement signal.

    Hash key: (company_unique_id, person_id, event_type, detected_at_date)

    Note: We include date (not full timestamp) to allow re-detection
    if the same movement is seen again on a different day.
    """
    # Normalize date to just YYYY-MM-DD for deduplication
    if detected_at:
        try:
            dt = datetime.fromisoformat(detected_at.replace('Z', '+00:00'))
            date_str = dt.strftime('%Y-%m-%d')
        except (ValueError, AttributeError):
            date_str = str(detected_at)[:10]
    else:
        date_str = 'unknown'

    unique_string = f"{company_unique_id}|{person_id}|{event_type}|{date_str}"
    return hashlib.sha256(unique_string.encode()).hexdigest()


def compute_talent_flow_hub_status(
    company_unique_id: str,
    movement_signals: List[Dict[str, Any]],
    freshness_cutoff: Optional[datetime] = None,
    people_hub_status: Optional[str] = None
) -> TalentFlowHubStatusResult:
    """
    Compute hub status for Talent Flow.

    PASS criteria (ALL must be true):
        1. Upstream People Intelligence hub is PASS (not BLOCKED)
        2. At least MIN_MOVEMENTS valid movement signals
        3. At least one signal within freshness window
        4. company_unique_id is valid

    Args:
        company_unique_id: The company to compute status for
        movement_signals: List of movement signals for this company
        freshness_cutoff: Cutoff datetime for freshness (default: now - FRESHNESS_DAYS)
        people_hub_status: Status of upstream People Intelligence hub

    Returns:
        TalentFlowHubStatusResult with status and reason
    """
    if not company_unique_id:
        return TalentFlowHubStatusResult(
            company_unique_id=company_unique_id or 'UNKNOWN',
            status='FAIL',
            status_reason='company_unique_id is NULL',
            metric_value=0
        )

    # Check upstream dependency (People Intelligence must not be BLOCKED)
    if people_hub_status == 'BLOCKED':
        return TalentFlowHubStatusResult(
            company_unique_id=company_unique_id,
            status='BLOCKED',
            status_reason='Upstream People Intelligence hub is BLOCKED',
            metric_value=0,
            details={'blocked_by': 'people-intelligence'}
        )

    if freshness_cutoff is None:
        freshness_cutoff = datetime.utcnow() - timedelta(days=FRESHNESS_DAYS)

    if not movement_signals:
        return TalentFlowHubStatusResult(
            company_unique_id=company_unique_id,
            status='IN_PROGRESS',
            status_reason='No movement signals detected',
            metric_value=0,
            details={'fresh_movements': 0, 'total_movements': 0}
        )

    # Count valid fresh movements (within freshness window)
    fresh_movements = 0
    seen_hashes = set()
    valid_movements = 0
    movement_breakdown = {
        'joined': 0,
        'left': 0,
        'title_change': 0,
    }

    for signal in movement_signals:
        event_type = signal.get('event_type', '')
        confidence = signal.get('confidence', 0)
        person_id = signal.get('person_id', '')
        detected_at = signal.get('detected_at') or signal.get('created_at')

        # Skip invalid movement types
        if event_type not in VALID_MOVEMENT_TYPES:
            continue

        # Skip low confidence movements
        if confidence < CONFIDENCE_THRESHOLD:
            continue

        # Skip duplicates (based on hash)
        signal_hash = generate_movement_signal_hash(
            company_unique_id,
            str(person_id),
            event_type,
            str(detected_at) if detected_at else ''
        )
        if signal_hash in seen_hashes:
            continue
        seen_hashes.add(signal_hash)

        valid_movements += 1
        movement_breakdown[event_type] = movement_breakdown.get(event_type, 0) + 1

        # Check freshness
        if detected_at:
            if isinstance(detected_at, str):
                try:
                    detected_at = datetime.fromisoformat(detected_at.replace('Z', '+00:00'))
                except ValueError:
                    continue

            if detected_at >= freshness_cutoff:
                fresh_movements += 1

    total_movements = len(seen_hashes)
    latest_signal = max(
        (s.get('detected_at') or s.get('created_at') for s in movement_signals
         if s.get('detected_at') or s.get('created_at')),
        default=None
    )

    # Compute detection rate (valid / total input)
    detection_rate = (valid_movements / len(movement_signals) * 100) if movement_signals else 0

    # Determine status
    if fresh_movements >= MIN_MOVEMENTS:
        return TalentFlowHubStatusResult(
            company_unique_id=company_unique_id,
            status='PASS',
            status_reason=f'{fresh_movements} fresh movement(s) within {FRESHNESS_DAYS} days',
            metric_value=detection_rate,
            last_processed_at=latest_signal,
            details={
                'fresh_movements': fresh_movements,
                'total_movements': total_movements,
                'freshness_days': FRESHNESS_DAYS,
                'movement_breakdown': movement_breakdown,
                'confidence_threshold': CONFIDENCE_THRESHOLD
            }
        )
    else:
        if total_movements > 0:
            reason = f'No fresh movements: {total_movements} total but none within {FRESHNESS_DAYS} days'
        else:
            reason = 'No valid movements (filtered by confidence or duplicates)'

        return TalentFlowHubStatusResult(
            company_unique_id=company_unique_id,
            status='IN_PROGRESS',
            status_reason=reason,
            metric_value=detection_rate,
            last_processed_at=latest_signal,
            details={
                'fresh_movements': fresh_movements,
                'total_movements': total_movements,
                'freshness_days': FRESHNESS_DAYS,
                'movement_breakdown': movement_breakdown,
                'freshness_expired': total_movements > 0 and fresh_movements == 0
            }
        )


async def backfill_talent_flow_hub_status(conn) -> Dict[str, int]:
    """
    Backfill hub status for all companies with movement signals.

    This uses the movement_events table (or equivalent) to compute
    status for all companies and upsert to company_hub_status.

    Args:
        conn: Database connection (asyncpg or psycopg2)

    Returns:
        Dict with counts: {'total': N, 'pass': N, 'in_progress': N}
    """
    logger.info("Starting Talent Flow hub status backfill")

    counts = {'total': 0, 'pass': 0, 'in_progress': 0, 'fail': 0, 'blocked': 0}

    # Query all companies with movement signals
    # Note: Assumes movement_events table exists in outreach schema
    # If using different table name, adjust accordingly
    query = """
        WITH company_movements AS (
            SELECT
                company_unique_id,
                COUNT(*) as total_movements,
                COUNT(*) FILTER (
                    WHERE detected_at >= NOW() - INTERVAL '%s days'
                    AND confidence >= %s
                    AND event_type IN ('joined', 'left', 'title_change')
                ) as fresh_movements,
                MAX(detected_at) as last_movement
            FROM outreach.movement_events
            WHERE company_unique_id IS NOT NULL
            GROUP BY company_unique_id
        ),
        people_status AS (
            SELECT company_unique_id, status
            FROM outreach.company_hub_status
            WHERE hub_id = 'people-intelligence'
        )
        SELECT
            cm.company_unique_id,
            cm.total_movements,
            cm.fresh_movements,
            cm.last_movement,
            ps.status as people_status,
            CASE
                WHEN ps.status = 'BLOCKED' THEN 'BLOCKED'
                WHEN cm.fresh_movements >= %s THEN 'PASS'
                ELSE 'IN_PROGRESS'
            END as computed_status
        FROM company_movements cm
        LEFT JOIN people_status ps ON cm.company_unique_id = ps.company_unique_id
    """

    try:
        # Check if using asyncpg or psycopg2
        if hasattr(conn, 'fetch'):
            # asyncpg - use $1, $2, $3 syntax
            query_asyncpg = query.replace('%s', '$1', 1).replace('%s', '$2', 1).replace('%s', '$3', 1)
            rows = await conn.fetch(query_asyncpg, FRESHNESS_DAYS, CONFIDENCE_THRESHOLD, MIN_MOVEMENTS)
        else:
            # psycopg2
            cursor = conn.cursor()
            cursor.execute(query, (FRESHNESS_DAYS, CONFIDENCE_THRESHOLD, MIN_MOVEMENTS))
            rows = cursor.fetchall()

        for row in rows:
            if hasattr(row, 'get'):
                # asyncpg Record
                company_id = row['company_unique_id']
                status = row['computed_status']
                fresh = row['fresh_movements']
                total = row['total_movements']
            else:
                # psycopg2 tuple
                company_id, total, fresh, last_movement, people_status, status = row

            # Upsert to company_hub_status
            upsert_query = """
                INSERT INTO outreach.company_hub_status
                    (company_unique_id, hub_id, status, metric_value, status_reason, last_processed_at)
                VALUES (%s, 'talent-flow', %s::outreach.hub_status_enum, %s, %s, NOW())
                ON CONFLICT (company_unique_id, hub_id)
                DO UPDATE SET
                    status = EXCLUDED.status,
                    metric_value = EXCLUDED.metric_value,
                    status_reason = EXCLUDED.status_reason,
                    last_processed_at = EXCLUDED.last_processed_at
            """

            detection_rate = (fresh / total * 100) if total > 0 else 0
            reason = f'{fresh} fresh movement(s), {total} total signals'

            if hasattr(conn, 'execute'):
                # asyncpg
                upsert_asyncpg = upsert_query.replace('%s', '$1', 1).replace('%s', '$2', 1).replace('%s', '$3', 1).replace('%s', '$4', 1)
                await conn.execute(upsert_asyncpg, company_id, status, detection_rate, reason)
            else:
                cursor.execute(upsert_query, (company_id, status, detection_rate, reason))

            counts['total'] += 1
            counts[status.lower()] += 1

        if not hasattr(conn, 'execute'):
            conn.commit()

        logger.info(f"Talent Flow backfill complete: {counts}")
        return counts

    except Exception as e:
        logger.error(f"Talent Flow backfill failed: {e}")
        raise


def compute_status_for_db_row(row: Dict[str, Any]) -> TalentFlowHubStatusResult:
    """
    Compute status from a database aggregation row.

    Expected row keys:
        - company_unique_id
        - fresh_movements: int
        - total_movements: int
        - last_movement: datetime
        - people_status: str (optional)
    """
    company_id = row.get('company_unique_id')
    fresh = row.get('fresh_movements', 0)
    total = row.get('total_movements', 0)
    last_movement = row.get('last_movement')
    people_status = row.get('people_status')

    # Build mock movement_signals for the compute function
    # We only need the count, not actual signals
    mock_signals = []
    for i in range(fresh):
        mock_signals.append({
            'event_type': 'joined',
            'confidence': 0.85,
            'person_id': f'mock_{i}',
            'detected_at': datetime.utcnow()  # Fresh
        })
    for i in range(total - fresh):
        mock_signals.append({
            'event_type': 'joined',
            'confidence': 0.85,
            'person_id': f'mock_old_{i}',
            'detected_at': datetime.utcnow() - timedelta(days=FRESHNESS_DAYS + 1)  # Expired
        })

    return compute_talent_flow_hub_status(
        company_id,
        mock_signals,
        people_hub_status=people_status
    )


__all__ = [
    'TalentFlowHubStatusResult',
    'compute_talent_flow_hub_status',
    'backfill_talent_flow_hub_status',
    'generate_movement_signal_hash',
    'compute_status_for_db_row',
    'FRESHNESS_DAYS',
    'MIN_MOVEMENTS',
    'CONFIDENCE_THRESHOLD',
]
