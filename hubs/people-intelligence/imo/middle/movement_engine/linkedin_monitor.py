"""
LinkedIn Monitor — Field Monitor Bridge (Read-Only)
====================================================
Reads field_monitor.field_state changes for LinkedIn profile URLs
and bridges detected title changes into the Movement Engine as
EVENT_TALENTFLOW_MOVE events.

Architecture:
    - Reads from field_monitor.url_registry + field_monitor.field_state
    - Joins against people.people_master via linkedin_url
    - Emits DetectedEvent to MovementEngine (no DB writes)
    - Kill switches: KILL_TALENT_FLOW_MONITOR, KILL_LINKEDIN_SEED

Constraints:
    - field_monitor.* bridge reads only; NEVER writes
    - Sample gate: LIMIT 100
    - All logic in hub Middle layer
"""

import os
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class LinkedInChange:
    """A detected LinkedIn profile change from field_monitor."""
    person_unique_id: str
    full_name: str
    linkedin_url: str
    old_title: Optional[str]
    new_title: str
    field_id: str
    url_id: str
    changed_at: datetime


@dataclass
class LinkedInMonitorResult:
    """Result of a LinkedIn monitor sweep."""
    changes_detected: int
    events_emitted: int
    killed: bool
    kill_switch: Optional[str]
    errors: List[str]
    changes: List[LinkedInChange]


def check_kill_switch(switch_name: str) -> bool:
    """Check if a kill switch is active via environment variable."""
    return os.environ.get(switch_name, "").upper() in ("1", "TRUE", "YES")


async def scan_linkedin_changes(sql) -> LinkedInMonitorResult:
    """
    Scan field_monitor for LinkedIn title changes and return detected changes.

    This function is READ-ONLY against field_monitor tables.
    It does NOT write to any table.

    Args:
        sql: Neon SQL tagged template function

    Returns:
        LinkedInMonitorResult with detected changes
    """
    errors: List[str] = []

    # Kill switch enforcement
    if check_kill_switch("KILL_TALENT_FLOW_MONITOR"):
        return LinkedInMonitorResult(
            changes_detected=0,
            events_emitted=0,
            killed=True,
            kill_switch="KILL_TALENT_FLOW_MONITOR",
            errors=[],
            changes=[],
        )

    if check_kill_switch("KILL_LINKEDIN_SEED"):
        return LinkedInMonitorResult(
            changes_detected=0,
            events_emitted=0,
            killed=True,
            kill_switch="KILL_LINKEDIN_SEED",
            errors=[],
            changes=[],
        )

    # Read-only query: join field_monitor state with people_master
    # to find title changes on LinkedIn profiles
    try:
        rows = await sql("""
            SELECT
                pm.unique_id AS person_unique_id,
                pm.full_name,
                pm.linkedin_url,
                fs.previous_value AS old_title,
                fs.current_value AS new_title,
                fs.field_id,
                fs.url_id,
                fs.last_changed_at
            FROM field_monitor.field_state fs
            JOIN field_monitor.url_registry ur ON ur.url_id = fs.url_id
            JOIN people.people_master pm
                ON pm.linkedin_url LIKE '%' || ur.domain || ur.path || '%'
            WHERE ur.domain = 'linkedin.com'
              AND fs.field_name = 'title'
              AND fs.previous_value IS NOT NULL
              AND fs.current_value IS NOT NULL
              AND fs.previous_value <> fs.current_value
              AND fs.last_changed_at > now() - interval '7 days'
            ORDER BY fs.last_changed_at DESC
            LIMIT 100
        """)
    except Exception as e:
        errors.append(f"Query failed: {e}")
        return LinkedInMonitorResult(
            changes_detected=0,
            events_emitted=0,
            killed=False,
            kill_switch=None,
            errors=errors,
            changes=[],
        )

    changes: List[LinkedInChange] = []
    for row in rows:
        changes.append(LinkedInChange(
            person_unique_id=row["person_unique_id"],
            full_name=row["full_name"],
            linkedin_url=row["linkedin_url"],
            old_title=row["old_title"],
            new_title=row["new_title"],
            field_id=row["field_id"],
            url_id=row["url_id"],
            changed_at=row["last_changed_at"],
        ))

    return LinkedInMonitorResult(
        changes_detected=len(changes),
        events_emitted=0,  # Caller bridges into MovementEngine
        killed=False,
        kill_switch=None,
        errors=errors,
        changes=changes,
    )


def bridge_to_movement_event(change: LinkedInChange) -> Dict[str, Any]:
    """
    Convert a LinkedInChange into MovementEngine event metadata.

    The caller should pass this to MovementEngine.detect_event() with:
        event_type="talentflow_move"
        source_system="field_monitor"

    Args:
        change: Detected LinkedIn title change

    Returns:
        Dict suitable for MovementEngine.detect_event(metadata=...)
    """
    return {
        "signal_type": "job_change",
        "signal_date": change.changed_at,
        "old_title": change.old_title,
        "new_title": change.new_title,
        "linkedin_url": change.linkedin_url,
        "source": "field_monitor",
        "field_id": change.field_id,
        "url_id": change.url_id,
    }
