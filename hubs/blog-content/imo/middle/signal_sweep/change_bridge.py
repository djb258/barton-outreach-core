"""
Change Bridge — Reads field_monitor changes and bridges to blog pipeline
=========================================================================
WP: wp-20260306-signal-sweep-blog-monitor
Kill switch: KILL_SIGNAL_SWEEP, KILL_FUNDING_DETECTION (reused)

Reads field_monitor.field_state for content_hash changes on blog URLs
and returns structured change records for the blog pipeline to
re-process affected articles.

This module is READ-ONLY against field_monitor tables.
It does NOT call ingest_article() directly — the caller bridges.
"""

import os
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class BlogChange:
    """A detected blog content change from field_monitor."""
    domain: str
    path: str
    url: str
    old_hash: Optional[str]
    new_hash: str
    url_id: str
    field_id: str
    changed_at: datetime


@dataclass
class BlogSweepResult:
    """Result of a blog change sweep."""
    changes_detected: int
    killed: bool
    kill_switch: Optional[str]
    errors: List[str]
    changes: List[BlogChange]


def check_kill_switch(switch_name: str) -> bool:
    """Check if a kill switch is active via environment variable."""
    return os.environ.get(switch_name, "").upper() in ("1", "TRUE", "YES")


async def scan_blog_changes(sql, *, lookback_days: int = 7, limit: int = 100) -> BlogSweepResult:
    """
    Scan field_monitor for blog content changes.

    READ-ONLY against field_monitor tables. Returns changes
    for the caller to bridge into the blog pipeline.

    Args:
        sql: Neon SQL tagged template function
        lookback_days: How far back to look for changes
        limit: Max changes to return

    Returns:
        BlogSweepResult with detected changes
    """
    errors: List[str] = []

    # Kill switch enforcement
    if check_kill_switch("KILL_SIGNAL_SWEEP"):
        return BlogSweepResult(
            changes_detected=0,
            killed=True,
            kill_switch="KILL_SIGNAL_SWEEP",
            errors=[],
            changes=[],
        )

    if check_kill_switch("KILL_FUNDING_DETECTION"):
        return BlogSweepResult(
            changes_detected=0,
            killed=True,
            kill_switch="KILL_FUNDING_DETECTION",
            errors=[],
            changes=[],
        )

    # Read-only query: find content_hash changes on blog URLs
    try:
        rows = await sql("""
            SELECT
                ur.domain,
                ur.path,
                fs.previous_value AS old_hash,
                fs.current_value AS new_hash,
                fs.url_id,
                fs.field_id,
                fs.last_changed_at
            FROM field_monitor.field_state fs
            JOIN field_monitor.url_registry ur ON ur.url_id = fs.url_id
            WHERE fs.field_name = 'content_hash'
              AND fs.previous_value IS NOT NULL
              AND fs.current_value IS NOT NULL
              AND fs.previous_value <> fs.current_value
              AND fs.last_changed_at > now() - ($1 || ' days')::interval
              AND ur.domain <> 'linkedin.com'
            ORDER BY fs.last_changed_at DESC
            LIMIT $2
        """, [str(lookback_days), limit])
    except Exception as e:
        errors.append(f"Query failed: {e}")
        return BlogSweepResult(
            changes_detected=0,
            killed=False,
            kill_switch=None,
            errors=errors,
            changes=[],
        )

    changes: List[BlogChange] = []
    for row in rows:
        changes.append(BlogChange(
            domain=row["domain"],
            path=row["path"],
            url=f"https://{row['domain']}{row['path']}",
            old_hash=row["old_hash"],
            new_hash=row["new_hash"],
            url_id=row["url_id"],
            field_id=row["field_id"],
            changed_at=row["last_changed_at"],
        ))

    return BlogSweepResult(
        changes_detected=len(changes),
        killed=False,
        kill_switch=None,
        errors=errors,
        changes=changes,
    )


def bridge_to_article_input(change: BlogChange) -> Dict[str, Any]:
    """
    Convert a BlogChange into input suitable for ingest_article().

    The caller should pass this to the blog pipeline's ingest_article()
    for re-processing the changed content.

    Args:
        change: Detected blog content change

    Returns:
        Dict suitable for ingest_article() input
    """
    old_hash_short = change.old_hash[:8] if change.old_hash else "none"
    new_hash_short = change.new_hash[:8] if change.new_hash else "none"

    return {
        "source_url": change.url,
        "source": "company_blog",
        "title": f"[Signal Sweep] {change.domain}{change.path}",
        "content": f"[Pending fetch — content_hash changed from {old_hash_short} to {new_hash_short}]",
        "published_at": change.changed_at.isoformat() if change.changed_at else None,
        "metadata": {
            "trigger": "signal_sweep",
            "old_hash": change.old_hash,
            "new_hash": change.new_hash,
            "field_id": change.field_id,
            "url_id": change.url_id,
        },
    }
