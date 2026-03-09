"""
URL Seeder — Seeds blog URLs from vendor.blog into field_monitor
=================================================================
WP: wp-20260306-signal-sweep-blog-monitor
Kill switch: KILL_BLOG_URL_SEED
Sample gate: LIMIT 100

Reads vendor.blog and inserts URLs into field_monitor.url_registry
with corresponding field_state rows for content_hash monitoring.

This module WRITES to field_monitor tables (seed operation only).
Runtime bridge reads are in change_bridge.py.
"""

import os
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class SeedResult:
    """Result of a blog URL seed operation."""
    urls_seeded: int
    fields_seeded: int
    killed: bool
    kill_switch: Optional[str]
    errors: List[str]
    dry_run: bool


def check_kill_switch(switch_name: str) -> bool:
    """Check if a kill switch is active via environment variable."""
    return os.environ.get(switch_name, "").upper() in ("1", "TRUE", "YES")


async def seed_blog_urls(sql, *, dry_run: bool = True, limit: int = 100) -> SeedResult:
    """
    Seed blog URLs from vendor.blog into field_monitor tables.

    Args:
        sql: Neon SQL tagged template function
        dry_run: If True, query but do not insert
        limit: Sample gate — max URLs to seed

    Returns:
        SeedResult with counts and status
    """
    errors: List[str] = []

    # Kill switch enforcement
    if check_kill_switch("KILL_SIGNAL_SWEEP"):
        return SeedResult(
            urls_seeded=0, fields_seeded=0,
            killed=True, kill_switch="KILL_SIGNAL_SWEEP",
            errors=[], dry_run=dry_run,
        )

    if check_kill_switch("KILL_BLOG_URL_SEED"):
        return SeedResult(
            urls_seeded=0, fields_seeded=0,
            killed=True, kill_switch="KILL_BLOG_URL_SEED",
            errors=[], dry_run=dry_run,
        )

    # Query vendor.blog for active blogs not yet in url_registry
    try:
        candidates = await sql("""
            SELECT vb.domain, vb.path
            FROM vendor.blog vb
            WHERE vb.is_active = true
              AND NOT EXISTS (
                SELECT 1 FROM field_monitor.url_registry ur
                WHERE ur.domain = vb.domain AND ur.path = vb.path
              )
            ORDER BY vb.created_at DESC NULLS LAST
            LIMIT $1
        """, [limit])
    except Exception as e:
        errors.append(f"Query vendor.blog failed: {e}")
        return SeedResult(
            urls_seeded=0, fields_seeded=0,
            killed=False, kill_switch=None,
            errors=errors, dry_run=dry_run,
        )

    if dry_run:
        return SeedResult(
            urls_seeded=len(candidates),
            fields_seeded=len(candidates),
            killed=False, kill_switch=None,
            errors=[], dry_run=True,
        )

    # Seed url_registry + field_state
    urls_seeded = 0
    fields_seeded = 0

    for row in candidates:
        try:
            await sql("""
                INSERT INTO field_monitor.url_registry
                    (url_id, domain, path, check_interval_minutes, is_active)
                VALUES (gen_random_uuid(), $1, $2, 60, true)
                ON CONFLICT DO NOTHING
            """, [row["domain"], row["path"]])
            urls_seeded += 1

            await sql("""
                INSERT INTO field_monitor.field_state
                    (field_id, url_id, field_name, current_value, status, promotion_status)
                SELECT gen_random_uuid(), ur.url_id, 'content_hash', NULL, 'ACTIVE', 'DRAFT'
                FROM field_monitor.url_registry ur
                WHERE ur.domain = $1 AND ur.path = $2
                  AND NOT EXISTS (
                    SELECT 1 FROM field_monitor.field_state fs
                    WHERE fs.url_id = ur.url_id AND fs.field_name = 'content_hash'
                  )
            """, [row["domain"], row["path"]])
            fields_seeded += 1
        except Exception as e:
            errors.append(f"Seed failed for {row['domain']}{row['path']}: {e}")

    return SeedResult(
        urls_seeded=urls_seeded,
        fields_seeded=fields_seeded,
        killed=False, kill_switch=None,
        errors=errors, dry_run=False,
    )
